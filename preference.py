import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import AddonPreferences

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
    default_render_policy: EnumProperty(
        name="Default Render Policy",
        items=[
            ("all", "Render all texture", "Render all texture"),
            ("workflow", "Follow active workflow", "Follow active workflow"),
            ("channels", "Follow channels group info in graph parameters",
             "Follow channels group info in graph parameters"),
        ]
    )

    # TODO log

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "cache_path")
        # TODO
        # layout.prop(self, "follow_channels")
        layout.prop(self, "default_render_policy")
        row = self.layout.row()
        row.prop(self,
                 'output_size_x', text='Default Texture Size')
        row.prop(self, 'output_size_lock',
                 toggle=1, icon_only=True, icon="LINKED", )
        if self.output_size_lock:
            row.prop(self,
                     'output_size_x', text='')
        else:
            row.prop(self,
                     'output_size_y', text='')


def register():
    bpy.utils.register_class(SublenderPreferences)


def unregister():
    bpy.utils.unregister_class(SublenderPreferences)
