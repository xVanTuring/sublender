instance_map = {}
sbsar_dict = {}

graph_clss = {}
"""clss_name->{clss,input...}"""
sub_panel_clss_list = []

material_templates = {}
material_template_enum = []
current_uuid = ""
async_task_map = {}

eval_delegate_map = {}
file_existence_dict = {}
library = {"materials": {}, "version": "0.1.1"}
preview_collections = None
library_category_enum = []
library_material_preset_map = {}
library_category_material_map = {"$OTHER$": [], "$ALL$": []}

graph_enum = []
instance_of_graph = []

applying_preset = False


def clear():
    global current_uuid
    current_uuid = ""
    graph_clss.clear()
    sbsar_dict.clear()
    file_existence_dict.clear()
    graph_enum.clear()
    instance_of_graph.clear()
