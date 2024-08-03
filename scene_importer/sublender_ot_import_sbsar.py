import asyncio
import typing

import bpy
from bpy.props import StringProperty

from .. import (
    utils,
    async_loop,
    props,
    sbsar_import,
    formatting,

)
from ..parser import SbsarPackageData
from ..props import ImportingGraphItem


class SublenderOTImportSbsar(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    """
    Import Sbsbar from file(path)
    """
    bl_idname = "sublender.import_sbsar"
    bl_label = "Import"
    bl_description = "Import"
    task_id = "SublenderOTImportSbsar"
    sbsar_paths: StringProperty()

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        await self.import_sbsar(context)

    async def import_sbsar(self, context):
        if not utils.sublender_inited(context):
            await utils.init_sublender_async(self, context)

        sbsar_paths = self.sbsar_paths.split("|")
        tasks = map(lambda x: sbsar_import.load_sbsar_to_dict_with_path_async(x, self.report), sbsar_paths)
        result = await asyncio.gather(*tasks)
        sbs_pkgs: typing.List[typing.Tuple[str, 'SbsarPackageData']] = list(filter(lambda x: x[1], result))
        if len(sbs_pkgs) == 0:
            self.report({"INFO"}, "Unable to find valid package")
            return

        await self.prepare_import_graph(context, sbs_pkgs)
        bpy.ops.sublender.import_graph("INVOKE_DEFAULT")

    async def prepare_import_graph(self, context, sbs_pkgs):
        importing_graphs = props.scene.get_scene_setting(context).importing_graphs
        importing_graphs.clear()

        for (file, sbs_pkg) in sbs_pkgs:
            for graph_info in sbs_pkg.graphs:
                importing_graph: ImportingGraphItem = importing_graphs.add()
                importing_graph.graph_url = graph_info.pkgUrl
                importing_graph.material_name = formatting.new_material_name(
                    graph_info.label
                )
                importing_graph.package_path = file
