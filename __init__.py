bl_info = {
    "name": "Sublender",
    "author": "xVanTuring(@foxmail.com)",
    "blender": (2, 80, 0),
    "version": (2, 1, 1),
    "location": "View3D > Properties > Sublender",
    "description": "An add-on for sbsar",
    "category": "Material",
}
import logging

import bpy
from bpy.app.handlers import persistent

# Support reloading
if "py7zr" in locals():
    import importlib

    wheels = importlib.reload(wheels)
    wheels.load_wheels()
else:
    from . import wheels

    wheels.load_wheels()

from . import globalvar

logging.basicConfig(level=logging.DEBUG, format="%(name)s %(message)s")
log = logging.getLogger(__name__)

saved = False


@persistent
def on_load_pre(_):
    """Remove all register clss, global var generate previously"""
    from . import globalvar

    if globalvar.current_uuid == "":
        return
    for clss in globalvar.sub_panel_clss_list:
        bpy.utils.unregister_class(clss)
    globalvar.sub_panel_clss_list.clear()
    for class_name in globalvar.graph_clss:
        class_info = globalvar.graph_clss.get(class_name)
        bpy.utils.unregister_class(class_info.clss)
    globalvar.clear()


@persistent
def on_load_post(_):
    from . import operators
    from .props.scene import get_scene_setting
    operators.sublender_update.auto_check()
    if bpy.data.filepath != "" and get_scene_setting().uuid != "":
        bpy.ops.sublender.init_async(pop_import=False)


@persistent
def on_save_pre(_):
    global saved
    if bpy.data.filepath == "":
        saved = False


@persistent
def on_save_post(_):
    from . import utils

    global saved
    if saved:
        return
    saved = True
    utils.refresh_panel(bpy.context)


def register():
    """Late-loads and registers the Blender-dependent submodules."""
    globalvar.version = bl_info["version"]
    log.info("Sublender@register: Starting")
    import sys

    # Support reloading
    if "%s.blender" % __name__ in sys.modules:
        import importlib

        def reload_mod(name):
            modname = "%s.%s" % (__name__, name)
            try:
                old_module = sys.modules[modname]
            except KeyError:
                # Wasn't loaded before -- can happen after an upgrade.
                new_module = importlib.import_module(modname)
            else:
                new_module = importlib.reload(old_module)

            sys.modules[modname] = new_module
            return new_module

        workflow = reload_mod("workflow")
        props = reload_mod("props")
        importer = reload_mod("importer")
        preference = reload_mod("preference")
        async_loop = reload_mod("async_loop")
        render = reload_mod("render")
        operators = reload_mod("operators")
        ui = reload_mod("ui")
    else:
        from . import (
            workflow,
            props,
            importer,
            preference,
            async_loop,
            render,
            operators,
            ui,
            wheels,
        )
    workflow.load_material_workflows()
    preference.register()
    render.register()

    async_loop.setup_asyncio_executor()
    async_loop.register()
    importer.register()
    props.register()
    operators.register()
    ui.register()
    render.sublender_library.ensure_library()
    render.sublender_library.load_library()
    bpy.app.handlers.load_pre.append(on_load_pre)
    bpy.app.handlers.save_pre.append(on_save_pre)
    bpy.app.handlers.save_post.append(on_save_post)
    bpy.app.handlers.load_post.append(on_load_post)
    log.info("Sublender@register: Done")


def unregister():
    from . import props, importer, preference, async_loop, render, operators, ui, utils

    ui.unregister()
    preference.unregister()
    async_loop.unregister()
    render.unregister()
    importer.unregister()
    props.unregister()
    operators.unregister()
    utils.unregister()

    for clss in globalvar.sub_panel_clss_list:
        bpy.utils.unregister_class(clss)
    for class_name in globalvar.graph_clss:
        class_info = globalvar.graph_clss.get(class_name)
        bpy.utils.unregister_class(class_info.clss)
    globalvar.clear()

    bpy.app.handlers.load_pre.remove(on_load_pre)
    bpy.app.handlers.save_post.remove(on_save_post)
    bpy.app.handlers.save_pre.remove(on_save_pre)
    bpy.app.handlers.load_post.remove(on_load_post)
