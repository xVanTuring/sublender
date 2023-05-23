from . import library, scene, material


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
