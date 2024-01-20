import asyncio
import typing

from ..parser.sbsarlite import SbsarPackageData
from ..datatypes import GraphClassInfoData

sbsar_dict: typing.Dict[str, SbsarPackageData] = {}

graph_clss: typing.Dict[str, GraphClassInfoData] = {}

sub_panel_clss_list: typing.List = []

material_templates: typing.Dict = {}
material_template_enum: typing.List = []
current_uuid = ""
async_task_map: typing.Dict = {}

eval_delegate_map: typing.Dict = {}
file_existence_dict: typing.Dict = {}
library: typing.Dict = {"materials": {}, "version": "0.1.1"}
preview_collections = None
library_category_enum: typing.List = []
library_material_preset_map: typing.Dict = {}

MaterialTuple = typing.Tuple[str, str, str, typing.Any, int]
library_category_material_map: typing.Dict[str, typing.List[MaterialTuple]] = {
    "$OTHER$": [],
    "$ALL$": [],
}

graph_enum: typing.List = []
instance_of_graph: list[tuple[str, str, str, str, int] | tuple[str, str, str]] = []

applying_preset = False

display_restart = False

task_id = 0
queue: asyncio.Queue = asyncio.Queue()
consumer_started = False

version = (0, 0, 0)


def clear():
    global current_uuid
    current_uuid = ""
    graph_clss.clear()
    sbsar_dict.clear()
    file_existence_dict.clear()
    graph_enum.clear()
    instance_of_graph.clear()
