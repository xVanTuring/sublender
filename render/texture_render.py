import asyncio
import datetime
import logging

import bpy
from bpy.props import StringProperty, BoolProperty

from .texture_render_base import RenderTextureBase
from .. import utils, async_loop, preference
from ..props.scene import get_scene_setting, ImportingGraphItem

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
            material_inst = utils.find_active_material(context)
            if material_inst is None:
                self.report({"WARNING"}, "No material is selected or given")
                return {"CANCELLED"}
            self.material_name = material_inst.name
            self.task_id = self.material_name
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def import_graph(self, context):
        preferences = preference.get_preferences()
        importing_graph_items: list[ImportingGraphItem] = get_scene_setting(context).importing_graphs
        start = datetime.datetime.now()
        for importing_graph in importing_graph_items:
            await self.do_import_graph(preferences, importing_graph)
        end = datetime.datetime.now()
        log.debug("Import Graph Completed in {} seconds".format(end - start))
        self.report(
            {"INFO"},
            "Render Done! Time spent: {0}s.".format((end - start).total_seconds()),
        )

    async def update_texture(self, _):
        preferences = preference.get_preferences()

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
        import traceback

        log.debug("SublenderOTRenderTexture.async_execute starting")
        try:
            log.debug("self.importing_graph is %s", self.importing_graph)
            if self.importing_graph:
                await self.import_graph(context)
            else:
                await self.update_texture(context)
        except TypeError as e:
            print(e)
            print(traceback.format_exc())


def register():
    bpy.utils.register_class(SublenderOTRenderTexture)


def unregister():
    bpy.utils.unregister_class(SublenderOTRenderTexture)
