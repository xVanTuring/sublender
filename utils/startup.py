import uuid

import bpy

from .. import props, globalvar, sbsar_import
from ..props.scene import get_scene_setting


async def init_sublender_async(self, context):
    sublender_settings = get_scene_setting(context)
    await sbsar_import.load_sbsars_async(self.report)
    props.scene.init_graph_items()
    props.scene.init_instance_of_graph(sublender_settings)
    bpy.app.handlers.undo_post.append(on_blender_undo)
    bpy.app.handlers.redo_post.append(on_blender_undo)
    if sublender_settings.uuid == "":
        sublender_settings.uuid = str(uuid.uuid4())
    globalvar.current_uuid = sublender_settings.uuid
    refresh_panel(context)


def refresh_panel(context):
    if context.area is not None:
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
                break
    else:
        print("Context.Area is None, Forcing updating all VIEW_3D-UI")
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    for region in area.regions:
                        if region.type == "UI":
                            region.tag_redraw()
                            break
                    break


def sublender_inited(context):
    sublender_settings = get_scene_setting(context)
    return (
            globalvar.current_uuid != ""
            and globalvar.current_uuid == sublender_settings.uuid
    )


def on_blender_undo(_):
    sublender_settings = props.get_scene_setting()
    if sublender_settings.live_update and sublender_settings.catch_undo:
        print("sublender_settings.catch_undo is On,re-render texture now")
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name="")


def unregister():
    if on_blender_undo in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.remove(on_blender_undo)
        bpy.app.handlers.redo_post.remove(on_blender_undo)
