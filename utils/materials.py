import bpy

from .startup import sublender_inited
from .. import props, globalvar, formatting
from ..props.scene import get_scene_setting


def find_active_material(context):
    if not sublender_inited(context):
        return None
    scene_sb_settings = get_scene_setting(context)
    if scene_sb_settings.follow_selection:
        if (
                context.view_layer.objects.active is None
                or len(bpy.context.view_layer.objects.active.material_slots) == 0
        ):
            return None
        active_material_enum = props.scene.instance_list_of_object
        if len(active_material_enum) == 0:
            return None
        mat_name = get_scene_setting(context).object_active_instance
        return bpy.data.materials.get(mat_name, None)
    if len(globalvar.instance_of_graph) > 0:
        target_mat = bpy.data.materials.get(scene_sb_settings.active_instance)
        return target_mat
    return None


def reset_material(material):
    clss_name = formatting.gen_clss_name(material.sublender.graph_url)
    graph_setting = getattr(material, clss_name)
    clss_info = globalvar.graph_clss.get(clss_name)
    for p_input in clss_info.input:
        if p_input.identifier != "$outputsize" and p_input.identifier != "$randomseed":
            graph_setting.property_unset(p_input.prop)
