import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty

from .. import utils
from .utils import get_idx, set_idx


def get_library_material_list(self, _):
    return utils.globalvar.library_category_material_map.get(self.categories, [])


def get_material_preset(self, _):
    return utils.globalvar.library_material_preset_map.get(self.active_material, [])


def get_category_list(_, __):
    return utils.globalvar.library_category_enum


def category_selected(self, context):
    material_list = utils.globalvar.library_category_material_map.get(
        self.categories, []
    )
    if len(material_list) > 0:
        self.active_material = material_list[0][0]


build_in_material_type = [
    ("Ceramic", "Ceramic", "Ceramic"),
    ("Concrete-Asphalt", "Concrete-Asphalt", "Concrete-Asphalt"),
    ("Fabric", "Fabric", "Fabric"),
    ("Ground", "Ground", "Ground"),
    ("Leather", "Leather", "Leather"),
    ("Marble-Granite", "Marble-Granite", "Marble-Granite"),
    ("Metal", "Metal", "Metal"),
    ("Organic", "Organic", "Organic"),
    ("Paint", "Paint", "Paint"),
    ("Paper", "Paper", "Paper"),
    ("Plaster", "Plaster", "Plaster"),
    ("Plastic-Rubber", "Plastic-Rubber", "Plastic-Rubber"),
    ("Stone", "Stone", "Stone"),
    ("Terracotta", "Terracotta", "Terracotta"),
    ("Translucent", "Translucent", "Translucent"),
    ("Wood", "Wood", "Wood"),
    ("$CUSTOM$", "Custom", "Custom"),
]


class ImportingPreset(bpy.types.PropertyGroup):
    name: StringProperty(default="")
    enable: BoolProperty(default=True)


class ImportingGraphItemLibrary(bpy.types.PropertyGroup):
    graph_url: StringProperty(name="Graph Url")
    category: EnumProperty(items=build_in_material_type, default="$CUSTOM$")
    category_str: StringProperty(default="")
    package_path: StringProperty(name="Package Path", subtype="FILE_PATH")
    importing_presets: bpy.props.CollectionProperty(type=ImportingPreset)
    enable: BoolProperty(name="Import", default=True)


class SublenderLibrary(bpy.types.PropertyGroup):
    active_material: EnumProperty(items=get_library_material_list)
    material_preset: EnumProperty(
        items=get_material_preset,
        get=get_idx(get_material_preset, "material_preset"),
        set=set_idx("material_preset"),
    )
    importing_graphs: bpy.props.CollectionProperty(type=ImportingGraphItemLibrary)
    categories: EnumProperty(items=get_category_list, update=category_selected)


cls_list = [ImportingPreset, ImportingGraphItemLibrary, SublenderLibrary]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sublender_library = bpy.props.PointerProperty(
        type=SublenderLibrary, name="Sublender Library"
    )


def unregister():
    del bpy.types.Scene.sublender_library
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
