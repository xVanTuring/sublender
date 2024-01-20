import os
import tempfile
import typing
import xml
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, IntEnum

import py7zr
import xmltodict

from .. import parser


class SBSARTypeEnum(IntEnum):
    FLOAT1 = 0
    FLOAT2 = 1
    FLOAT3 = 2
    FLOAT4 = 3
    INTEGER1 = 4
    IMAGE = 5
    STRING = 6
    FONT = 7
    INTEGER2 = 8
    INTEGER3 = 9
    INTEGER4 = 10


SbsarValueType = float | list[float] | int | list[int] | str | None


class SBSARWidgetEnum(Enum):
    togglebutton = "togglebutton"
    slider = "slider"
    color = "color"
    combobox = "combobox"


@dataclass
class SbsarPresetInputData:
    identifier: str
    type: int | SBSARTypeEnum
    uid: str
    prop: str
    value: str


@dataclass
class SbsarGraphOutputData:
    identifier: str
    uid: str
    label: str
    usages: typing.List[str]


@dataclass
class SbsarGraphInputData:
    uid: str
    identifier: str
    type: int | SBSARTypeEnum
    prop: str
    widget: SBSARWidgetEnum | None = None
    default: SbsarValueType = None
    label: str | None = None
    visibleIf: str | None = None
    group: str | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    clamp: bool | None = None
    combo_items: typing.List[typing.Tuple[str, str, str]] | None = None
    label0: str | None = None
    label1: str | None = None
    alteroutputs: typing.List[str] | None = None


@dataclass
class SbsarGraphPresetData:
    preset_name: str
    inputs: typing.List[SbsarPresetInputData]


@dataclass
class SbsarGraphData:
    pkgUrl: str
    label: str
    inputs: typing.List[SbsarGraphInputData]
    outputs: typing.List[SbsarGraphOutputData]
    category: str
    description: str
    presets: typing.Dict[str, SbsarGraphPresetData]


@dataclass
class SbsarPackageData:
    graphs: typing.List[SbsarGraphData]
    asmuid: str


def parse_sbsar_raw(raw: OrderedDict) -> SbsarPackageData:
    xml_graphs = raw["sbsdescription"]["graphs"]
    parsed_sbsar: SbsarPackageData = SbsarPackageData(graphs=[], asmuid=raw["sbsdescription"]["@asmuid"])
    graph_count = int(xml_graphs["@count"])
    if graph_count > 1:
        graph_list = xml_graphs["graph"]
    else:
        graph_list = [xml_graphs["graph"]]
    for i in range(graph_count):
        if graph_list[i].get("@hideInLibrary") == "on":
            continue
        parsed_sbsar.graphs.append(parse_graph(graph_list[i]))
    return parsed_sbsar


def parse_graph(raw: OrderedDict) -> SbsarGraphData:
    parsed_graph = SbsarGraphData(
        pkgUrl=raw["@pkgurl"],
        label=raw["@label"],
        inputs=[],
        outputs=[],
        category=raw.get("@category", ""),
        description=raw.get("@description", ""),
        presets={},
    )

    if parsed_graph.category is not None:
        parsed_graph.category = parsed_graph.category.split("/")[-1]

    xml_inputs = raw["inputs"]
    input_count = int(xml_inputs["@count"])

    if input_count > 1:
        raw_input_list = xml_inputs["input"]
    else:
        raw_input_list = [xml_inputs["input"]]
    for i in range(input_count):
        parsed_graph.inputs.append(parse_input(raw_input_list[i]))

    xml_outputs = raw["outputs"]
    output_count = int(xml_outputs["@count"])
    if output_count > 1:
        raw_output_list = xml_outputs["output"]
    else:
        raw_output_list = [xml_outputs["output"]]
    for i in range(output_count):
        parsed_graph.outputs.append(parse_output(raw_output_list[i]))
    xml_presets: OrderedDict | None = raw.get("sbspresets", None)
    if xml_presets is not None:
        presets_count = int(xml_presets["@count"])
        if presets_count > 0:
            if presets_count > 1:
                raw_preset_list = xml_presets["sbspreset"]
            else:
                raw_preset_list = [xml_presets["sbspreset"]]
            for i in range(presets_count):
                preset_name, preset = parse_preset(raw_preset_list[i])
                parsed_graph.presets[preset_name] = preset
    return parsed_graph


def parse_preset(raw: OrderedDict) -> typing.Tuple[str, SbsarGraphPresetData]:
    preset = SbsarGraphPresetData(
        preset_name=raw.get("@label", "No Preset Name"),
        inputs=[],
    )
    inputs: typing.Any = raw.get("presetinput")
    if not isinstance(inputs, list):
        inputs = [inputs]
    for p_input in inputs:
        input_info = SbsarPresetInputData(
            identifier=p_input.get("@identifier"),
            type=int(p_input.get("@type")),
            uid=p_input.get("@uid"),
            prop=parser.uid_prop(p_input.get("@uid")),
            value=p_input.get("@value"),
        )
        preset.inputs.append(input_info)
    return raw.get("@label", "No Label"), preset


def parse_output(raw: OrderedDict) -> SbsarGraphOutputData:
    parsed_output = SbsarGraphOutputData(
        identifier=raw["@identifier"],
        uid=raw["@uid"],
        label=raw["outputgui"]["@label"],
        usages=[],
    )
    if raw["outputgui"]["channels"] is not None:
        if isinstance(raw["outputgui"]["channels"]["channel"], list):
            channels = raw["outputgui"]["channels"]["channel"]
        else:
            channels = [raw["outputgui"]["channels"]["channel"]]
        for channel in channels:
            parsed_output.usages.append(channel["@names"])

    return parsed_output


def parse_input(raw: OrderedDict) -> SbsarGraphInputData:
    parsed_input = SbsarGraphInputData(
        uid=raw["@uid"],
        identifier=raw["@identifier"],
        type=int(raw["@type"]),
        prop=parser.uid_prop(raw["@uid"]),
    )
    if parsed_input.identifier == "$randomseed":
        parsed_input.prop = "$randomseed"
    if raw.get("@default") is not None:
        default_value = parse_str_value(raw["@default"], parsed_input.type)
        parsed_input.default = default_value
    else:
        parsed_input.default = None

    if raw.get("inputgui") is not None:
        parse_gui(raw["inputgui"], parsed_input.type, parsed_input)
    else:
        # prevent any error
        parsed_input.widget = None
        parsed_input.label = None
        parsed_input.visibleIf = None
        parsed_input.group = None
        parsed_input.min = None
        parsed_input.max = None
        parsed_input.step = None
        parsed_input.clamp = None
        parsed_input.label0 = None
        parsed_input.label1 = None
        parsed_input.combo_items = None

    if raw.get("@alteroutputs") is not None:
        alteroutputs = raw.get("@alteroutputs").split(",")
        parsed_input.alteroutputs = alteroutputs
    return parsed_input


def parse_gui(raw: OrderedDict, type_num: int, parsed_input: SbsarGraphInputData):
    parsed_input.widget = raw.get("@widget")
    parsed_input.label = raw.get("@label")
    parsed_input.visibleIf = raw.get("@visibleif")
    parsed_input.group = raw.get("@group")

    if parsed_input.widget == SBSARWidgetEnum.slider:
        guislider: typing.Optional[typing.Dict] = raw.get("guislider")
        if guislider is not None:
            if guislider.get("@min"):
                parsed_input.min = parse_str_value(guislider["@min"], type_num)
                if isinstance(parsed_input.min, list):
                    parsed_input.min = parsed_input.min[0]

            if guislider.get("@max"):
                parsed_input.max = parse_str_value(guislider["@max"], type_num)
                if isinstance(parsed_input.max, list):
                    parsed_input.max = parsed_input.max[0]

            if guislider.get("@step"):
                parsed_input.step = parse_str_value(guislider["@step"], type_num)
                if type_num < SBSARTypeEnum.INTEGER1:
                    if parsed_input.step:
                        parsed_input.step = parsed_input.step * 100

            if guislider.get("@clamp") == "on":
                parsed_input.clamp = True
            else:
                parsed_input.clamp = False
            # parsed_input['label0'] = raw.get('guislider').get('@label0')
            # parsed_input['label1'] = raw.get('guislider').get('@label1')
            # parsed_input['label2'] = raw.get('guislider').get('@label2')
            # parsed_input['label3'] = raw.get('guislider').get('@label3')
    elif parsed_input.widget == SBSARWidgetEnum.togglebutton:
        guibutton: typing.Optional[typing.Dict] = raw.get("guibutton")
        if guibutton is not None:
            parsed_input.label0 = guibutton.get("@label0")
            parsed_input.label1 = guibutton.get("@label1")
    elif parsed_input.widget == SBSARWidgetEnum.combobox:
        if raw.get("guicombobox") is not None:
            parsed_input.combo_items = list(
                map(lambda raw_combobox_item: (
                    "$NUM:{0}".format(raw_combobox_item.get("@value")),
                    raw_combobox_item.get("@text"),
                    raw_combobox_item.get("@text"),
                ), raw["guicombobox"].get("guicomboboxitem"))
            )
            if parsed_input.default is not None:
                parsed_input.default = "$NUM:{0}".format(parsed_input.default)


def parse_str_value(raw_str: str, type_num: int) -> SbsarValueType:
    if type_num < 4:
        parsed = [float(value) for value in raw_str.split(",")]
        if len(parsed) == 1:
            return parsed[0]
        return parsed
    elif type_num == 4 or type_num > 7:
        parsed = [int(value) for value in raw_str.split(",")]
        if len(parsed) == 1:
            return parsed[0]
        return parsed

    return raw_str


def parse_doc(file_path: str) -> SbsarPackageData | None:
    archive = py7zr.SevenZipFile(file_path, mode="r")
    allfiles = archive.getnames()
    sbsar_xml_path = None
    unzip_dir = os.path.join(
        tempfile.gettempdir(), "sublender", os.path.basename(file_path)
    )
    for file_name in allfiles:
        if file_name.endswith("xml"):
            sbsar_xml_path = os.path.join(unzip_dir, file_name)
            archive.extract(unzip_dir, targets=[file_name])
    if sbsar_xml_path is not None:
        # https://stackoverflow.com/a/16375153
        with open(sbsar_xml_path, "r") as f:
            raw_xml_str = f.read()
            try:
                raw_sbs_xml = xmltodict.parse(raw_xml_str)
            except xml.parsers.expat.ExpatError as e:
                e.with_traceback(None)
                raise Exception(
                    "Failed to parsed file {} as it's empty".format(sbsar_xml_path)
                )
        return parse_sbsar_raw(raw_sbs_xml)
    return None
