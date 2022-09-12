import bpy

from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, IntVectorProperty
# from .consts import output_size_enum, SUBLENDER_DIR
from . import consts


def output_size_x_updated(self, context):
    if self.output_size_lock and self.output_size_y != self.output_size_x:
        self.output_size_y = self.output_size_x


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
    output_size_x: EnumProperty(
        name='Width',
        items=consts.output_size_one_enum,
        default='8'
    )
    output_size_y: EnumProperty(
        name='Height',
        items=consts.output_size_one_enum,
        default='8'
    )
    output_size_lock: BoolProperty(
        default=True,
        update=output_size_x_updated
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
        row = self.layout.row()
        row.prop(self,
                 'output_size_x', text='Default Texture Size')
        row.prop(self, 'output_size_lock',
                 toggle=1, icon_only=True, icon="LINKED",)
        if self.output_size_lock:
            row.prop(self,
                     'output_size_x', text='')
        else:
            row.prop(self,
                     'output_size_y', text='')
