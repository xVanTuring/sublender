import bpy
from bpy.app.handlers import persistent

bl_info = {
    "name": "Sublender",
    "author": "xVanTuring(@outlook.com)",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "View3D > Properties > Sublender",
    "description": "An add-on for sbsar",
    "category": "Material"
}


@persistent
def on_load_pre(dummy):
    from . import (globalvar)
    for clss in globalvar.sub_panel_clss_list:
        bpy.utils.unregister_class(clss)
    globalvar.sub_panel_clss_list.clear()
    for class_name in globalvar.graph_clss:
        class_info = globalvar.graph_clss.get(class_name)
        bpy.utils.unregister_class(class_info['clss'])
    globalvar.current_uuid = ""
    globalvar.graph_clss.clear()
    globalvar.sbsar_dict.clear()
    globalvar.aContext = None
    globalvar.instance_map.clear()


def register():
    import sys

    # Support reloading
    if '%s.blender' % __name__ in sys.modules:
        import importlib

        def reload_mod(name):
            modname = '%s.%s' % (__name__, name)
            try:
                old_module = sys.modules[modname]
            except KeyError:
                # Wasn't loaded before -- can happen after an upgrade.
                new_module = importlib.import_module(modname)
            else:
                new_module = importlib.reload(old_module)

            sys.modules[modname] = new_module
            return new_module

        template = reload_mod('template')
        settings = reload_mod('settings')
        importer = reload_mod('importer')
        preference = reload_mod('preference')
        async_loop = reload_mod('async_loop')
        texture_render = reload_mod('texture_render')
        sb_operators = reload_mod('sb_operators')
        ui = reload_mod('ui')
    else:
        from . import (template, utils, settings,
                       importer, preference, async_loop, texture_render,
                       sb_operators, ui)

    template.load_material_templates()
    preference.register()
    texture_render.register()
    async_loop.register()
    importer.register()
    settings.register()
    sb_operators.register()
    ui.register()
    bpy.app.handlers.load_pre.append(on_load_pre)


def unregister():
    from . import (settings,
                   importer, preference, async_loop, texture_render,
                   sb_operators, ui, globalvar)
    ui.unregister()
    preference.unregister()
    async_loop.unregister()
    texture_render.unregister()
    importer.unregister()
    settings.unregister()
    sb_operators.unregister()

    for clss in globalvar.sub_panel_clss_list:
        bpy.utils.unregister_class(clss)
    for class_name in globalvar.graph_clss:
        class_info = globalvar.graph_clss.get(class_name)
        bpy.utils.unregister_class(class_info['clss'])
    globalvar.current_uuid = ""
    globalvar.graph_clss.clear()
    globalvar.sbsar_dict.clear()
    globalvar.aContext = None
    globalvar.instance_map.clear()

    bpy.app.handlers.load_pre.remove(on_load_pre)
