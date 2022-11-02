import asyncio
import typing

instance_map = {
}

sbsar_dict = {}

graph_clss = {}
"""clss_name->{clss,input...}"""
sub_panel_clss_list = []

material_templates = {}
material_template_enum = []
current_uuid = ""

async_task: typing.Optional[asyncio.Future] = None

eval_delegate_map = {}
load_status = -1
file_existence_dict = {}


def clear():
    global current_uuid
    # global aContext
    current_uuid = ""
    graph_clss.clear()
    sbsar_dict.clear()
    # aContext = None
    instance_map.clear()
    file_existence_dict.clear()
