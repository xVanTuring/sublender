import bpy

from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, IntVectorProperty
# from .consts import output_size_enum, SUBLENDER_DIR
from . import consts


class SublenderPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    cachePath: StringProperty(
        name="Cache Path",
        subtype='FILE_PATH',
        default=consts.SUBLENDER_DIR,
        description="Path to store texture cache"
    )
    default_output: EnumProperty(
        name="Default Output Size",
        default="512",
        items=consts.output_size_enum,
        description="Default Output Size to be set when creating graph"
    )
    custom_output: IntVectorProperty(
        name="Custom Output Size(the nth power of 2)",
        description="Default Output Size to be set when creating graph,the nth power of 2",
        default=[4, 4],
        min=0,
        max=13,
        size=2
    )
    # prefer_workflow:

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "cachePath")
        layout.prop(self, "default_output")
        if self.default_output == consts.CUSTOM:
            layout.prop(self, "custom_output")
