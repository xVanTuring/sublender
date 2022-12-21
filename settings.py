import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)

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


def package_path_updated(self, context):
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


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(
        items=graph_list, name="Graph", update=active_graph_updated)
    active_instance: EnumProperty(
        items=instance_list, name="Instance")
    catch_undo: BoolProperty(name="Catch Undo",
                             default=False,
                             description="Tender texture after undo/redo")
    uuid: StringProperty(name="UUID of this blender file", default="")
    live_update: BoolProperty(
        name="Live Update", description="Live Update")
    follow_selection: BoolProperty(name="Follow Selection", default=False)
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)


def get_materials(self, context):
    if self.mode == "CATEGORIES":
        if self.categories == "$ALL$":
            return globalvar.library_preview_enum
        else:
            return globalvar.library_category_material_map[self.categories]
    else:
        return globalvar.library_preview_enum


def get_categories(self, context):
    return globalvar.library_category_enum


def category_selected(self, context):
    current_materials = get_materials(self, context)
    if len(current_materials) > 0:
        self.library_preview = current_materials[0][0]


def search_materials(self, search_string):
    pass
    # self.info_type = material_library.rpr_material_library.search_materials(search_string)


class SublenderLibrary(bpy.types.PropertyGroup):
    library_preview: EnumProperty(items=get_materials)
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItem)
    categories: EnumProperty(items=get_categories, update=category_selected)
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
