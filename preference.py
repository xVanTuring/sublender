import bpy

from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, IntVectorProperty
# from .consts import output_size_enum, SUBLENDER_DIR
from . import consts


class SublenderPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    cache_path: StringProperty(
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
    follow_channels: BoolProperty(
        name="Follow Channels Group",
        description="Follow options in channels group to generate texture, it may cause texture not founded",
        default=False
    )
    # display_in_material_tab: BoolProperty(
    #     name="Display in Material Tab",
    #     description="Display in Material Tab",
    #     default=False
    # )
# TODO log

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "cache_path")
        # TODO
        # layout.prop(self, "follow_channels")
        # layout.prop(self, "display_in_material_tab")
        layout.prop(self, "default_output")
        if self.default_output == consts.CUSTOM:
            layout.prop(self, "custom_output")
