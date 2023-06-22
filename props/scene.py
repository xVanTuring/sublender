import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)

from .. import utils
from .utils import get_idx, set_idx


def get_graph_list(_, __):
    init_graph_items()
    return utils.globalvar.graph_enum


def init_graph_items():
    utils.globalvar.graph_enum.clear()
    package_url_set = set()
    i = 0
    for material in bpy.data.materials:
        m_sublender = material.sublender
        if (m_sublender is not None) and (m_sublender.graph_url != "") and (m_sublender.package_path != ""):
            if m_sublender.graph_url not in package_url_set:
                package_url_set.add(m_sublender.graph_url)
                utils.globalvar.graph_enum.append(
                    (m_sublender.graph_url, m_sublender.graph_url, m_sublender.graph_url))
                i += 1


def active_graph_updated(self, context):
    # manually update
    init_instance_of_graph(self)


def init_instance_of_graph(self):
    utils.globalvar.instance_of_graph.clear()
    if len(utils.globalvar.graph_enum) == 0:
        return
    i = 0
    active_graph = self.active_graph
    for material in bpy.data.materials:
        m_sublender = material.sublender
        if m_sublender is not None and m_sublender.graph_url == active_graph:
            mat_name = material.name
            utils.globalvar.instance_of_graph.append((mat_name, mat_name, mat_name, material.preview.icon_id, i))
            i += 1


def get_instance_of_graph(self, context):
    init_instance_of_graph(self)
    return utils.globalvar.instance_of_graph


instance_list_of_object = []


# OPTI: get called multiple times
def get_instance_list_of_object(_, context):
    build_instance_list_of_object(context)
    return instance_list_of_object


def build_instance_list_of_object(context):
    instance_list_of_object.clear()
    if context.view_layer.objects.active is None or len(context.view_layer.objects.active.material_slots) == 0:
        return instance_list_of_object

    for i, mat_slot in enumerate(context.view_layer.objects.active.material_slots):
        mat = mat_slot.material
        if mat is None:
            continue
        mat_setting = mat.sublender
        if mat_setting.package_path != '' and mat_setting.graph_url != '':
            mat_name = mat.name
            instance_list_of_object.append((mat_name, mat_name, mat_name, mat.preview.icon_id, i))


class ImportingGraphItem(bpy.types.PropertyGroup):
    graph_url: StringProperty(name="Graph Url")
    material_name: StringProperty(name='Material Name')
    enable: BoolProperty(name="Import", default=True)
    preset_name: StringProperty(default="")
    library_uid: StringProperty(default="")
    material_template: EnumProperty(items=utils.globalvar.material_template_enum, name='Template')
    use_fake_user: BoolProperty(name="Fake User", default=True)
    assign_to_selection: BoolProperty(name='Append to selected mesh', default=False)
    package_path: StringProperty(name="Package Path", subtype="FILE_PATH")


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(items=get_graph_list,
                               name="Graph",
                               get=get_idx(utils.globalvar.graph_enum, "active_graph"),
                               set=set_idx("active_graph"),
                               update=active_graph_updated)
    active_instance: EnumProperty(items=get_instance_of_graph,
                                  name="Instance",
                                  get=get_idx(utils.globalvar.instance_of_graph, "active_instance"),
                                  set=set_idx("active_instance"))
    object_active_instance: EnumProperty(items=get_instance_list_of_object,
                                         name="Object Active Instance",
                                         get=get_idx(instance_list_of_object, "object_active_instance"),
                                         set=set_idx("object_active_instance"))
    catch_undo: BoolProperty(name="Catch Undo", default=False, description="Render texture after undo/redo")
    uuid: StringProperty(name="UUID of this blender file", default="")
    live_update: BoolProperty(name="Live Update", description="Live Update")
    follow_selection: BoolProperty(name="Follow Selection", default=False)
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)


cls_list = [ImportingGraphItem, SublenderSetting]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sublender_settings = bpy.props.PointerProperty(type=SublenderSetting, name="Sublender")


def unregister():
    del bpy.types.Scene.sublender_settings
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
