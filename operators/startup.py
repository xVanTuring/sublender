import bpy
from bpy.props import BoolProperty

from .. import utils, async_loop


class SublenderOTInitAsync(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.init_async"
    bl_label = "Init & Import"
    bl_description = "Init Sublender"
    task_id = "Sublender_Init_Async"
    pop_import: BoolProperty(default=False, name="Pop Import")

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        await utils.init_sublender_async(self, context)
        if self.pop_import:
            bpy.ops.sublender.select_sbsar("INVOKE_DEFAULT")


def register():
    bpy.utils.register_class(SublenderOTInitAsync)


def unregister():
    bpy.utils.unregister_class(SublenderOTInitAsync)
