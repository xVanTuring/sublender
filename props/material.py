import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from .. import utils


def package_path_updated(self, _):
    if self.package_missing:
        bpy.ops.sublender.load_missing_sbsar(sbsar_path=self.package_path)


class SublenderMaterialSetting(bpy.types.PropertyGroup):
    package_path: StringProperty(name="Package Path", subtype="FILE_PATH", update=package_path_updated)
    graph_url: StringProperty(name="Graph URL")
    show_setting: BoolProperty(name="Show Params", default=True)
    material_template: EnumProperty(name="Material Template", items=utils.globalvar.material_template_enum)
    uuid: StringProperty(name="UUID of this material", default="")
    package_missing: BoolProperty()
    package_loaded: BoolProperty(default=False)
    library_uid: StringProperty(default="")


cls_list = [SublenderMaterialSetting]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)
    bpy.types.Material.sublender = bpy.props.PointerProperty(type=SublenderMaterialSetting)


def unregister():
    del bpy.types.Material.sublender
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
