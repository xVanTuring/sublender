import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)

from . import globalvar


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
    material_template: EnumProperty(
        name="Material Template", items=globalvar.material_template_enum)
    uuid: StringProperty(name="UUID of this material", default="")
    package_missing: BoolProperty()
    package_loaded: BoolProperty(default=False)
    library_uid: StringProperty(default="")


# endregion

class ImportingGraphItem(bpy.types.PropertyGroup):
    graph_url: StringProperty(name="Graph Url")
    enable: BoolProperty(name="Import", default=True)
    material_template: EnumProperty(
        items=globalvar.material_template_enum,
        name='Template'
    )
    material_name: StringProperty(
        name='Material Name')
    use_fake_user: BoolProperty(
        name="Fake User",
        default=True
    )
    assign_to_selection: BoolProperty(
        name='Append to selected mesh',
        default=False
    )
    library_uid: StringProperty(default="")


# region SublenderSetting
def get_graph_list(_, __):
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
    # return globalvar.graph_enum


def active_graph_updated(self, context):
    m_instance_list = get_instance_list(self, context)
    context.scene.sublender_settings.active_instance = m_instance_list[0][0]
    # get_instance_list(self, context)


def get_instance_list(_, context):
    return globalvar.instance_map.get(context.scene.sublender_settings.active_graph,
                                      [("$DUMMY$", "No Instance", "Dummy")])

    # mats = bpy.data.materials.items()
    # globalvar.instance_of_graph.clear()
    # i = 0
    # for mat_name, mat in mats:
    #     m_sublender: Sublender_Material_MT_Setting = mat.sublender
    #     if (m_sublender is not None) and (m_sublender.graph_url == self.active_graph) and (
    #             m_sublender.package_path is not ""):
    #         globalvar.instance_of_graph.append((
    #             mat_name, mat_name, mat_name, mat.preview.icon_id, i))
    #         i += 1
    # return globalvar.instance_of_graph


instance_list_of_object = []


def get_instance_list_of_object(_, context):
    instance_list_of_object.clear()
    if context.view_layer.objects.active is None or len(
            context.view_layer.objects.active.material_slots) == 0:
        return instance_list_of_object

    for i, mat_slot in enumerate(context.view_layer.objects.active.material_slots):
        mat = mat_slot.material
        if mat is None:
            continue
        mat_setting: Sublender_Material_MT_Setting = mat.sublender
        if mat_setting.package_path != '' and mat_setting.graph_url != '':
            mat_name = mat.name
            instance_list_of_object.append((mat_name, mat_name, mat_name, mat.preview.icon_id, i))
    return instance_list_of_object


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(items=get_graph_list,
                               name="Graph",
                               # get=get_idx(get_graph_list, "active_graph"),
                               # set=set_idx("active_graph"),
                               update=active_graph_updated)
    active_instance: EnumProperty(items=get_instance_list, name="Instance")
    # get = get_idx(globalvar.instance_of_graph, "active_instance"),
    # set = set_idx("active_instance")
    object_active_instance: EnumProperty(
        items=get_instance_list_of_object,
        name="Object Active Instance",
        get=get_idx(instance_list_of_object, "object_active_instance"),
        set=set_idx("object_active_instance")
    )
    catch_undo: BoolProperty(name="Catch Undo",
                             default=False,
                             description="Tender texture after undo/redo")
    uuid: StringProperty(name="UUID of this blender file", default="")
    live_update: BoolProperty(name="Live Update", description="Live Update")
    follow_selection: BoolProperty(name="Follow Selection", default=False)
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)


# endregion

# region SublenderLibrary
def get_library_material_list(self, _):
    if self.mode == "CATEGORIES":
        return globalvar.library_category_material_map[self.categories]
    else:
        return globalvar.library_category_material_map["$ALL$"]


def get_material_preset(self, _):
    return globalvar.library_material_preset_map.get(self.active_material, [])


def get_category_list(_, __):
    return globalvar.library_category_enum


def category_selected(self, context):
    material_list = get_library_material_list(self, context)
    if len(material_list) > 0:
        self.active_material = material_list[0][0]


def search_materials(_, __):
    pass
    # self.info_type = material_library.rpr_material_library.search_materials(search_string)


class SublenderLibrary(bpy.types.PropertyGroup):
    active_material: EnumProperty(items=get_library_material_list)
    material_preset: EnumProperty(items=get_material_preset,
                                  get=get_idx(get_material_preset, "material_preset"),
                                  set=set_idx("material_preset")
                                  )
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)
    categories: EnumProperty(items=get_category_list, update=category_selected)
    mode: EnumProperty(
        name="Library browsing mode",
        items=(
            ('CATEGORIES', "Categories", "Browse materials by category"),
            ('SEARCH', "Search", "Search for materials by name"),
        ),
        default='CATEGORIES',
    )
    search: StringProperty(
        name="Search",
        set=search_materials,
    )


# endregion

def register():
    bpy.utils.register_class(ImportingGraphItem)
    bpy.utils.register_class(Sublender_Material_MT_Setting)
    bpy.utils.register_class(SublenderSetting)
    bpy.utils.register_class(SublenderLibrary)
    bpy.types.Scene.sublender_settings = bpy.props.PointerProperty(
        type=SublenderSetting, name="Sublender")
    bpy.types.Material.sublender = bpy.props.PointerProperty(
        type=Sublender_Material_MT_Setting)
    bpy.types.Scene.sublender_library = bpy.props.PointerProperty(
        type=SublenderLibrary, name="Sublender Library")


def unregister():
    bpy.utils.unregister_class(Sublender_Material_MT_Setting)
    bpy.utils.unregister_class(SublenderSetting)
    bpy.utils.unregister_class(ImportingGraphItem)
    bpy.utils.unregister_class(SublenderLibrary)
