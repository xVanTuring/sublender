if "bpy" in locals():
    from importlib import reload
    template = reload(template)
    utils = reload(utils)
    settings = reload(settings)
    parser = reload(parser)
    consts = reload(consts)
    globalvar = reload(globalvar)
    importer = reload(importer)
    preference = reload(preference)
    async_loop = reload(async_loop)
    texture_render = reload(texture_render)
    sb_operators = reload(sb_operators)
    ui = reload(ui)
else:
    from sublender import (template, utils, settings, parser, consts,
                           globalvar, importer, preference, async_loop, texture_render,
                           sb_operators, ui)
import bpy

bl_info = {
    "name": "Sublender",
    "author": "xVanTuring(@outlook.com)",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (0, 0, 1),
    "location": "View3D > Properties > Sublender",
    "description": "A addon for sbsar",
    "category": "Material"
}


def register():
    template.load_material_templates()

    preference.register()
    texture_render.register()
    async_loop.register()
    importer.register()
    settings.register()
    sb_operators.register()
    ui.register()



def unregister():
    preference.unregister()
    async_loop.unregister()
    texture_render.unregister()
    importer.unregister()
    settings.unregister()
    sb_operators.unregister()
    ui.unregister()
    for clss_name in globalvar.graph_clss:
        clss_info = globalvar.graph_clss.get(clss_name)
        bpy.utils.unregister_class(clss_info['clss'])
