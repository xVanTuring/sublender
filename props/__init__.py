from . import library, scene, material
from .material import get_material_sublender
from .scene import get_scene_setting, ImportingGraphItem


def new_graph_item(graph_url: str, category: str, package_path: str):
    return {
        "graph_url": graph_url,
        "category": category,
        "package_path": package_path,
        "presets": [],
    }


mod_list = [library, scene, material]


def register():
    for mod in mod_list:
        mod.register()


def unregister():
    for mod in mod_list:
        mod.unregister()
