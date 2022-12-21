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
async_task_map = {}

eval_delegate_map = {}
load_status = -1
file_existence_dict = {}
library = {
    "materials": [],
    "version": "0.1.1"
}
preview_collections = None

library_preview_enum = []


def clear():
    global current_uuid
    current_uuid = ""
    graph_clss.clear()
    sbsar_dict.clear()
    instance_map.clear()
    file_existence_dict.clear()
