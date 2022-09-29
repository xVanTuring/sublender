import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import AddonPreferences

from . import consts


def output_size_x_updated(self, context):
    if self.output_size_lock and self.output_size_y != self.output_size_x:
        self.output_size_y = self.output_size_x


thank_list = ["kalish"]


# noinspection PyTypeChecker
class SublenderPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    compatible_mode: BoolProperty(
        name="Compatible Undo Mode",
        description="Enable Compatible Undo Mode for blender 2.82a, with this option on, "
                    "sublender will increase the texture suffix to prevent blender"
                    " from crash when undo in Material Mode.",
        default=True
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

    enable_visible_if: BoolProperty(
        name="Enable Visible If"
    )

    engine_enum: EnumProperty(
        items=[
            ("$default$", "Unspecified", "Unspecified, it will use the default engine."),
            ("d3d11pc", "d3d11pc(gpu,windows)",
             "d3d11pc: it will use dx11 as render engine, might not be available in linux"),
            ("sse2", "sse2(cpu)", "sse2"),
            ("ogl3", "ogl3(gpu,non-windows)", "ogl3"),
            ("d3d10pc", "d3d10pc(gpu,2019)",
             "similar to d3d11pc, but for substance 2019"),
            (consts.CUSTOM, "Custom", "Custom")],
        default="$default$",
        name="Substance Render Engine"
    )
    custom_engine: StringProperty(name="Custom Engine", default='')
    sat_path: StringProperty(name="SAT Installation Path", default='', subtype='DIR_PATH')

    # ("channels", "Follow Channels group",
    #  "Follow channels group info in graph parameters"),

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'sat_path')
        row = layout.row()
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
        row = layout.row()
        row.prop(self, 'compatible_mode',
                 toggle=1, icon="GHOST_ENABLED")
        row.prop(self, 'enable_visible_if',
                 toggle=1, icon="HIDE_OFF")
        # layout.prop(self, 'update_when_sizing', toggle=1, icon='FILE_REFRESH')
        layout.prop(self, 'engine_enum')
        if self.engine_enum == consts.CUSTOM:
            layout.prop(self, 'custom_engine')

        layout.label(text="Special Thanks to YOU and: ")
        layout.label(text=' '.join(thank_list))


def register():
    bpy.utils.register_class(SublenderPreferences)


def unregister():
    bpy.utils.unregister_class(SublenderPreferences)
