import bpy
from bpy.props import BoolProperty
from .. import utils, async_loop
from . import workflow, material, output, sublender_update


class SublenderOTInitAsync(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.init_async"
    bl_label = "Init & Import"
    bl_description = "Init Sublender"
    task_id = "Sublender_Init_Async"
    pop_import: BoolProperty(default=False, name="Pop Import")

    @classmethod
    def poll(cls, context):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        await utils.init_sublender_async(self, context)
        if self.pop_import:
            bpy.ops.sublender.select_sbsar('INVOKE_DEFAULT')


def ShowMessageBox(message="", title="Message Box", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


cls_list = [SublenderOTInitAsync]
mod_list = [workflow, material, output, sublender_update]


def register():
    for mod in mod_list:
        mod.register()
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
    for mod in mod_list:
        mod.unregister()