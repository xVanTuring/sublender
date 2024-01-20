import typing

import bpy

from .startup import sublender_inited
from .. import props
from ..props.scene import get_scene_setting


def find_active_graph(context) -> typing.Tuple[typing.Any | None, str | None]:
    if not sublender_inited(context):
        return None, None
    scene_sb_settings = get_scene_setting(context)
    if scene_sb_settings.follow_selection:
        if (
                context.view_layer.objects.active is None
                or len(bpy.context.view_layer.objects.active.material_slots) == 0
        ):
            return None, None
        if get_scene_setting(context).object_active_instance == "":
            props.scene.build_instance_list_of_object(context)
        active_material_enum = props.scene.instance_list_of_object
        if len(active_material_enum) == 0:
            return None, None
        mat_name = get_scene_setting(context).object_active_instance
        active_mat = bpy.data.materials.get(mat_name, None)
        return active_mat, active_mat.sublender.graph_url

    mats = bpy.data.materials
    target_mat = mats.get(scene_sb_settings.active_instance)
    if target_mat is not None:
        return target_mat, target_mat.sublender.graph_url
    return None, None
