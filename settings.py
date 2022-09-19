import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
import typing
from . import globalvar


def graph_list(self, context):
    mats = bpy.data.materials.items()
    globalvar.instance_map.clear()
    for mat_name, mat in mats:
        m_sublender: Sublender_Material_MT_Setting = mat.sublender
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            if not (m_sublender.graph_url in globalvar.instance_map):
                globalvar.instance_map[m_sublender.graph_url] = []
            globalvar.instance_map[m_sublender.graph_url].append((
                mat_name, mat_name, mat_name, mat.preview.icon_id, len(globalvar.instance_map[m_sublender.graph_url])))

    # [(identifier, name, description, icon, number), ...]
    m_graph_list = list(
        map(lambda x: (x, x, ""), globalvar.instance_map.keys()))
    if (len(m_graph_list)) > 0:
        return list(map(lambda x: (x, x, ""), globalvar.instance_map.keys()))
    else:
        return [("$DUMMY$", "No Graph", "Dummy")]


def active_graph_updated(self, context):
    m_instance_list = instance_list(self, context)
    context.scene.sublender_settings.active_instance = m_instance_list[0][0]


def instance_list(self, context):
    # [(identifier, name, description, icon, number), ...]
    return globalvar.instance_map.get(context.scene.sublender_settings.active_graph,
                                      [("$DUMMY$", "No Instance", "Dummy")])


def active_instance_update(self, context):
    # update active_graph here if not the same
    pass


class Sublender_Material_MT_Setting(bpy.types.PropertyGroup):
    package_path: StringProperty(name="Package Path")
    graph_url: StringProperty(name="Graph URL")
    show_setting: BoolProperty(name="Show Params")
    material_template: EnumProperty(
        name="Material Template", items=globalvar.material_template_enum)
    uuid: StringProperty(name="UUID of this material", default="")
    # noinspection PyTypeChecker
    render_policy: EnumProperty(
        name="Default Render Policy",
        items=[
            ("all", "Render all texture", "Render all texture to disk"),
            ("workflow", "Follow active workflow", "Follow active workflow"),
        ],
        default="all"
    )


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(
        items=graph_list, name="Graph", update=active_graph_updated)
    active_instance: EnumProperty(
        items=instance_list, name="Instance", update=active_instance_update)
    # active_instance_obj: EnumProperty(
    #     items=instance_list_obj, name="Instance")
    uuid: StringProperty(name="UUID of this blender file", default="")
    live_update: BoolProperty(
        name="Live Update", description="Live Update")
    follow_selection: BoolProperty(name="Follow Selection", default=True)


def register():
    bpy.utils.register_class(Sublender_Material_MT_Setting)
    bpy.utils.register_class(SublenderSetting)
    bpy.types.Scene.sublender_settings = bpy.props.PointerProperty(
        type=SublenderSetting, name="Sublender")
    bpy.types.Material.sublender = bpy.props.PointerProperty(
        type=Sublender_Material_MT_Setting)


def unregister():
    bpy.utils.unregister_class(Sublender_Material_MT_Setting)
    bpy.utils.unregister_class(SublenderSetting)
