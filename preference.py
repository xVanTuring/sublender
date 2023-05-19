import bpy
import platform
import os
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import AddonPreferences, Operator

from . import utils, ui

default_library_path = os.path.expanduser("~/Documents/Sublender")

if platform.system() == "Linux":
    default_sbsrender_path = "/opt/Allegorithmic/Substance_Designer/sbsrender"
elif platform.system() == "Windows":
    default_sbsrender_path = "C:\\Program Files\\Allegorithmic\\Substance Designer\\sbsrender.exe"
else:
    default_sbsrender_path = "/Applications/Substance Designer.app/Contents/MacOS/sbsrender"


def output_size_x_updated(self, _):
    if self.output_size_lock and self.output_size_y != self.output_size_x:
        self.output_size_y = self.output_size_x


thank_list = ["kalish", "miurahr", "martinblech"]


# noinspection PyTypeChecker
class SublenderPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    output_size_x: EnumProperty(name='Width', items=utils.consts.output_size_one_enum, default='8')
    output_size_y: EnumProperty(name='Height', items=utils.consts.output_size_one_enum, default='8')
    output_size_lock: BoolProperty(default=True, update=output_size_x_updated)

    enable_visible_if: BoolProperty(name="Enable Visible If")
    enable_output_params: BoolProperty(name="Enable Output Params")

    engine_enum: EnumProperty(items=[("$default$", "Unspecified", "Unspecified, it will use the default engine."),
                                     ("d3d11pc", "d3d11pc(GPU,windows)",
                                      "d3d11pc: it will use dx11 as render engine, might not be available in linux"),
                                     ("sse2", "sse2(CPU)", "sse2"), ("ogl3", "ogl3(GPU,non-windows)", "ogl3"),
                                     ("d3d10pc", "d3d10pc(GPU,2019)", "similar to d3d11pc, but for substance 2019"),
                                     (utils.consts.CUSTOM, "Custom", "Custom")],
                              default="$default$",
                              name="Substance Render Engine")
    custom_engine: StringProperty(name="Custom Engine", default='')
    sbs_render: StringProperty(name="Sbsrender Path", default=default_sbsrender_path, subtype='FILE_PATH')
    memory_budget: IntProperty(name="Memory Budget (MB)", min=0, default=1000)
    hide_channels: BoolProperty(name="Hide Channels Group", default=False)
    library_preview_engine: EnumProperty(name="Default Library Render Engine",
                                         items=[("eevee", "Eevee", ""), ("cycles", "Cycles", "")],
                                         default="eevee")
    library_path: StringProperty(name="Library Path(restart required)",
                                 default=default_library_path,
                                 subtype='DIR_PATH')

    def draw(self, _):
        layout = self.layout
        if not utils.globalvar.py7zr_state:
            ui.draw_install_deps(layout)
            return
        layout.prop(self, 'sbs_render')
        layout.prop(self, 'library_path')
        row = layout.row()
        row.prop(self, 'output_size_x', text='Default Texture Size')
        row.prop(self, 'output_size_lock', toggle=1, icon_only=True, icon="LINKED")
        if self.output_size_lock:
            row.prop(self, 'output_size_x', text='')
        else:
            row.prop(self, 'output_size_y', text='')
        row = layout.row()
        row.prop(self, 'enable_output_params', toggle=1)
        row.prop(self, 'enable_visible_if', toggle=1, icon="HIDE_OFF")
        row = layout.row()
        row.prop(self, 'memory_budget')
        row.prop(self, 'hide_channels', toggle=1)
        layout.prop(self, 'engine_enum')
        if self.engine_enum == utils.consts.CUSTOM:
            layout.prop(self, 'custom_engine')
        layout.prop(self, 'library_preview_engine')

        layout.separator()
        layout.label(text="Special Thanks to YOU and: ")
        layout.label(text=', '.join(thank_list))


def register():

    bpy.utils.register_class(SublenderPreferences)


def unregister():
    bpy.utils.unregister_class(SublenderPreferences)
