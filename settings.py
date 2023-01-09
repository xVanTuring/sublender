import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)

from . import globalvar, consts


# region get/set idx
def get_idx(enum_items, name: str):
    def get_x(self):
        if callable(enum_items):
            len_of_x = len(enum_items(self, bpy.context))
        else:
            len_of_x = len(enum_items)
        if name in self:
            if len_of_x <= self[name]:
                if len_of_x > 0:
                    return 0
                return -1
            return self[name]
        elif len_of_x > 0:
            return 0
        return -1

    return get_x


def set_idx(name):
    def setter(self, value):
        self[name] = value

    return setter


# endregion


# region Sublender_Material_MT_Setting
def package_path_updated(self, _):
    if self.package_missing:
        bpy.ops.sublender.load_sbsar(sbsar_path=self.package_path)


class Sublender_Material_MT_Setting(bpy.types.PropertyGroup):
    package_path: StringProperty(name="Package Path", subtype="FILE_PATH", update=package_path_updated)
    graph_url: StringProperty(name="Graph URL")
    show_setting: BoolProperty(name="Show Params", default=True)
    material_template: EnumProperty(name="Material Template", items=globalvar.material_template_enum)
    uuid: StringProperty(name="UUID of this material", default="")
    package_missing: BoolProperty()
    package_loaded: BoolProperty(default=False)
    library_uid: StringProperty(default="")


# endregion


class ImportingPreset(bpy.types.PropertyGroup):
    name: StringProperty(default="")
    enable: BoolProperty(default=True)


class ImportingGraphItem(bpy.types.PropertyGroup):
    graph_url: StringProperty(name="Graph Url")
    enable: BoolProperty(name="Import", default=True)
    material_template: EnumProperty(items=globalvar.material_template_enum, name='Template')
    material_name: StringProperty(name='Material Name')
    use_fake_user: BoolProperty(name="Fake User", default=True)
    assign_to_selection: BoolProperty(name='Append to selected mesh', default=False)
    library_uid: StringProperty(default="")
    preset_name: StringProperty(default="")
    importing_presets: bpy.props.CollectionProperty(type=ImportingPreset)
    category: EnumProperty(items=consts.build_in_material_type, default="$CUSTOM$")
    category_str: StringProperty(default="")


# region SublenderSetting


def get_graph_list(_, __):
    init_graph_items()
    return globalvar.graph_enum


def init_graph_items():
    globalvar.graph_enum.clear()
    package_url_set = set()
    i = 0
    for material in bpy.data.materials:
        m_sublender = material.sublender
        if (m_sublender is not None) and (m_sublender.graph_url != "") and (m_sublender.package_path != ""):
            if m_sublender.graph_url not in package_url_set:
                package_url_set.add(m_sublender.graph_url)
                globalvar.graph_enum.append(
                    (m_sublender.graph_url, m_sublender.graph_url, m_sublender.graph_url))
                i += 1


def active_graph_updated(self, context):
    # manually update
    init_instance_of_graph(self)


def init_instance_of_graph(self):
    globalvar.instance_of_graph.clear()
    if len(globalvar.graph_enum) == 0:
        return
    i = 0
    active_graph = self.active_graph
    for material in bpy.data.materials:
        m_sublender = material.sublender
        if m_sublender is not None and m_sublender.graph_url == active_graph:
            mat_name = material.name
            globalvar.instance_of_graph.append((mat_name, mat_name, mat_name, material.preview.icon_id, i))
            i += 1


def get_instance_of_graph(self, context):
    init_instance_of_graph(self)
    return globalvar.instance_of_graph


instance_list_of_object = []


def get_instance_list_of_object(_, context):
    init_instance_list_of_object(context)
    return instance_list_of_object


def init_instance_list_of_object(context):
    instance_list_of_object.clear()
    if context.view_layer.objects.active is None or len(
            context.view_layer.objects.active.material_slots) == 0:
        return instance_list_of_object

    for i, mat_slot in enumerate(context.view_layer.objects.active.material_slots):
        mat = mat_slot.material
        if mat is None:
            continue
        mat_setting = mat.sublender
        if mat_setting.package_path != '' and mat_setting.graph_url != '':
            mat_name = mat.name
            instance_list_of_object.append((mat_name, mat_name, mat_name, mat.preview.icon_id, i))


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(items=get_graph_list,
                               name="Graph",
                               get=get_idx(globalvar.graph_enum, "active_graph"),
                               set=set_idx("active_graph"),
                               update=active_graph_updated)
    active_instance: EnumProperty(items=get_instance_of_graph,
                                  name="Instance",
                                  get=get_idx(globalvar.instance_of_graph, "active_instance"),
                                  set=set_idx("active_instance"))
    # BUG: enum display error
    object_active_instance: EnumProperty(items=get_instance_list_of_object,
                                         name="Object Active Instance",
                                         get=get_idx(instance_list_of_object, "object_active_instance"),
                                         set=set_idx("object_active_instance"))
    catch_undo: BoolProperty(name="Catch Undo", default=False, description="Tender texture after undo/redo")
    uuid: StringProperty(name="UUID of this blender file", default="")
    live_update: BoolProperty(name="Live Update", description="Live Update")
    follow_selection: BoolProperty(name="Follow Selection", default=False)
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)


# endregion


# region SublenderLibrary
def get_library_material_list(self, _):
    return globalvar.library_category_material_map[self.categories]


def get_material_preset(self, _):
    return globalvar.library_material_preset_map.get(self.active_material, [])


def get_category_list(_, __):
    return globalvar.library_category_enum


def category_selected(self, context):
    material_list = get_library_material_list(self, context)
    if len(material_list) > 0:
        self.active_material = material_list[0][0]


class SublenderLibrary(bpy.types.PropertyGroup):
    active_material: EnumProperty(items=get_library_material_list)
    material_preset: EnumProperty(items=get_material_preset,
                                  get=get_idx(get_material_preset, "material_preset"),
                                  set=set_idx("material_preset"))
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)
    categories: EnumProperty(items=get_category_list, update=category_selected)


# endregion


def register():
    bpy.utils.register_class(ImportingPreset)
    bpy.utils.register_class(ImportingGraphItem)
    bpy.utils.register_class(Sublender_Material_MT_Setting)
    bpy.utils.register_class(SublenderSetting)
    bpy.utils.register_class(SublenderLibrary)
    bpy.types.Scene.sublender_settings = bpy.props.PointerProperty(type=SublenderSetting, name="Sublender")
    bpy.types.Material.sublender = bpy.props.PointerProperty(type=Sublender_Material_MT_Setting)
    bpy.types.Scene.sublender_library = bpy.props.PointerProperty(type=SublenderLibrary,
                                                                  name="Sublender Library")


def unregister():
    bpy.utils.unregister_class(Sublender_Material_MT_Setting)
    bpy.utils.unregister_class(SublenderSetting)
    bpy.utils.unregister_class(ImportingGraphItem)
    bpy.utils.unregister_class(ImportingPreset)
    bpy.utils.unregister_class(SublenderLibrary)
