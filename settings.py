from . import globals
from . import utils
import bpy
from bpy.props import (PointerProperty, StringProperty, BoolProperty, CollectionProperty,
                       EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)


class Sublender_Material_MT_Setting(bpy.types.PropertyGroup):
    package_path: StringProperty(name="Package Path")
    graph_url: StringProperty(name="Graph URL")
    show_setting: BoolProperty(name="Show Params")
    material_template: EnumProperty(
        name="Material Template", items=globals.material_template_enum)


def graph_list(self, context):
    mats = bpy.data.materials.items()
    globals.instance_map.clear()
    for mat_name, mat in mats:
        m_sublender: Sublender_Material_MT_Setting = mat.sublender
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            if not(m_sublender.graph_url in globals.instance_map):
                globals.instance_map[m_sublender.graph_url] = []
            globals.instance_map[m_sublender.graph_url].append((
                mat_name, mat_name, mat_name,))
    # [(identifier, name, description, icon, number), ...]
    m_graph_list = list(map(lambda x: (x, x, ""), globals.instance_map.keys()))
    if (len(m_graph_list)) > 0:
        return list(map(lambda x: (x, x, ""), globals.instance_map.keys()))
    else:
        return [("$DUMMY$", "No Graph", "Dummy")]


def active_graph_updated(self, context):
    pass
    # m_instance_list  = instance_list(self,context)
    # context.scene.sublender_settings.active_instance = m_instance_list[0][0]


def instance_list(self, context):
    # [(identifier, name, description, icon, number), ...]
    return globals.instance_map.get(context.scene.sublender_settings.active_graph, [("$DUMMY$", "No Instance", "Dummy")])


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(
        items=graph_list, name="Graph")
    active_instance: EnumProperty(
        items=instance_list, name="Instance")
    uuid: StringProperty(name="UUID of this blender file", default="")
    live_update: BoolProperty(name="Live Update")
    follow_selection: BoolProperty(name="Follow Selection", default=True)
