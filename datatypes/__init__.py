import typing
from dataclasses import dataclass

from ..parser import GroupInfoData
from ..parser.sbsarlite import SbsarGraphInputData, SbsarGraphData


@dataclass
class GraphClassGroupInfoData:
    tree: typing.List[GroupInfoData]
    map: typing.Dict[str, GroupInfoData]


@dataclass
class OutputInfoData:
    name: str
    usages: typing.List[str]
    label: str
    uid: str


@dataclass
class GraphClassOutputInfoData:
    list: list[OutputInfoData]
    dict: typing.Dict[str, OutputInfoData]
    usage: typing.Dict[str, typing.List[str]]


@dataclass
class GraphClassInfoData:
    clss: typing.Type
    input: typing.List[SbsarGraphInputData]
    prop_input_map: typing.Dict[str, SbsarGraphInputData]
    sbs_graph: SbsarGraphData
    group_info: GraphClassGroupInfoData
    output_info: GraphClassOutputInfoData
