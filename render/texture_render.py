import asyncio
import datetime
import logging

import bpy
from bpy.props import StringProperty, BoolProperty

from .texture_render_base import RenderTextureBase
from .. import utils, async_loop

log = logging.getLogger(__name__)


class SublenderOTRenderTexture(
    async_loop.AsyncModalOperatorMixin, RenderTextureBase, bpy.types.Operator
):
    bl_idname = "sublender.render_texture_async"
    bl_label = "Render Texture"
    bl_description = "Render Texture"

    importing_graph: BoolProperty(default=False)
    package_path: StringProperty()

    texture_name: StringProperty(default="")
    input_id: StringProperty(default="")

    def clean(self, context):
        self.do_clean()

    def invoke(self, context, event):
        if self.importing_graph:
            self.task_id = self.package_path
        else:
            material_inst = utils.find_active_mat(context)
            if material_inst is None:
                self.report({"WARNING"}, "No material is selected or given")
                return {"CANCELLED"}
            self.material_name = material_inst.name
            self.task_id = self.material_name
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def import_graph(self, context):
        preferences = context.preferences.addons["sublender"].preferences
        importing_graph_items = context.scene.sublender_settings.importing_graphs
        start = datetime.datetime.now()
        await asyncio.gather(
            *map(
                lambda x: self.do_import_graph(preferences, x),
                importing_graph_items,
            )
        )
        end = datetime.datetime.now()
        self.report(
            {"INFO"},
            "Render Done! Time spent: {0}s.".format((end - start).total_seconds()),
        )

    async def update_texture(self, context):
        preferences = context.preferences.addons["sublender"].preferences
        if self.texture_name == "":
            await asyncio.sleep(preferences.render_delay)
        self.report({"INFO"}, "Starting Render")
        start = datetime.datetime.now()
        await self.do_update_texture(preferences, self.texture_name, self.input_id)
        end = datetime.datetime.now()
        self.report(
            {"INFO"},
            "Render Done! Time spent: {0}s.".format((end - start).total_seconds()),
        )

    async def async_execute(self, context):
        if self.importing_graph:
            await self.import_graph(context)
        else:
            await self.update_texture(context)


def register():
    bpy.utils.register_class(SublenderOTRenderTexture)


def unregister():
    bpy.utils.unregister_class(SublenderOTRenderTexture)
