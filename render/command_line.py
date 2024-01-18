import os
import pathlib
import logging
import typing

from .. import utils, parser, render

log = logging.getLogger(__name__)


def generate_cmd_list(
    preferences,
    target_material_name: str,
    m_sublender,
    input_list: typing.List,
    graph_setting,
):
    param_list = [
        "render",
        "--input",
        m_sublender.package_path,
        "--input-graph",
        m_sublender.graph_url,
    ]
    handle_input_list(graph_setting, input_list, param_list)
    handle_output(param_list, target_material_name)
    handle_render_engine(param_list, preferences)
    handle_memory(preferences.memory_budget, param_list)

    return param_list


def handle_memory(memory_budget: int, param_list: typing.List[str]):
    param_list.append("--memory-budget")
    param_list.append("{0}".format(memory_budget))


def handle_output(param_list: typing.List[str], target_material_name: str):
    param_list.append("--output-path")
    target_dir = render.texture_output_dir(target_material_name)
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    param_list.append(target_dir)
    param_list.append("--output-name")
    param_list.append("{outputNodeName}")


def handle_render_engine(
    param_list: typing.List[str],
    engine_param,
):
    engine_value, custom_value = engine_param.engine_enum, engine_param.custom_engine
    if engine_value != "$default$":
        if engine_value != utils.consts.CUSTOM:
            param_list.append("--engine")
            param_list.append(engine_value)
            log.debug("using render engine  {0}".format(engine_value))
        else:
            if custom_value != "":
                param_list.append("--engine")
                param_list.append(custom_value)
                log.debug("using render engine  {0}".format(custom_value))
    else:
        log.debug("using default render engine")


def handle_input_list(
    graph_setting, input_list: typing.List, param_list: typing.List[str]
):
    for input_info in input_list:
        if input_info["identifier"] == "$outputsize":
            handle_input_output_size(graph_setting, input_info, param_list)
        else:
            handle_input_normal(input_info, graph_setting, param_list)


def handle_input_output_size(graph_setting, input_info, param_list):
    locked = getattr(graph_setting, utils.consts.output_size_lock, True)
    param_list.append("--set-value")
    width = getattr(graph_setting, utils.consts.output_size_x)
    if locked:
        param_list.append("{0}@{1},{1}".format(input_info["identifier"], width))
    else:
        height = getattr(graph_setting, utils.consts.output_size_x)
        param_list.append("{0}@{1},{2}".format(input_info["identifier"], width, height))


def handle_input_normal(input_info, graph_setting, param_list: typing.List[str]):
    value = graph_setting.get(input_info["prop"])
    if value is None:
        return
    if input_info.get("enum_items") is not None:
        value = input_info.get("enum_items")[value][0]
    if input_info["type"] == parser.sbsarlite.SBSARTypeEnum.IMAGE:
        if value == "":
            return
        if not os.path.exists(value):
            log.debug("Image is missing")
        param_list.append("--set-entry")
    else:
        param_list.append("--set-value")
    value = convert_to_command_value(graph_setting, input_info, value)
    param_list.append("{0}@{1}".format(input_info["identifier"], value))


def convert_to_command_value(graph_setting, input_info, value):
    to_list_fn = getattr(value, "to_list", None)
    if to_list_fn is not None:
        if isinstance(value[0], float):
            value = ",".join(map(lambda x: ("%0.3f" % x), to_list_fn()))
        else:
            value = ",".join(map(str, to_list_fn()))
    if isinstance(value, float):
        value = "%.3f" % value
    if input_info.get("widget") == "combobox":
        value = getattr(graph_setting, input_info["prop"]).replace("$NUM:", "")
    return value
