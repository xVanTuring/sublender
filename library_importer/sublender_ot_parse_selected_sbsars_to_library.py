import bpy
from bpy.props import StringProperty

from .. import sbsar_import, async_loop


class SublenderOTParseSelectedSbsarsToLibrary(
    async_loop.AsyncModalOperatorMixin, bpy.types.Operator
):
    bl_idname = "sublender.parse_selected_sbsars_to_library"
    bl_label = "Parse Sbsars"
    bl_description = "Parse Sbsars"

    files_list: StringProperty()
    task_id = "SublenderOTParseSelectedSbsarsToLibrary"

    async def parse_selected_sbsars_to_library(self, context):
        importing_graphs = context.scene.sublender_library.importing_graphs
        importing_graphs.clear()
        sbsar_files = filter(lambda x: x, self.files_list.split("|"))
        for sbsar_path in sbsar_files:
            sbs_pkg = await sbsar_import.load_sbsar_to_dict_async(sbsar_path, self.report)
            if sbs_pkg is None:
                continue

            for graph_info in sbs_pkg.graphs:
                adding_graph = importing_graphs.add()
                adding_graph.graph_url = graph_info.pkgUrl
                adding_graph.category_str = graph_info.category
                adding_graph.package_path = sbsar_path
                for preset_name in graph_info.presets.keys():
                    importing_preset = adding_graph.importing_presets.add()
                    importing_preset.name = preset_name

        bpy.ops.sublender.import_graphs_to_library("INVOKE_DEFAULT")

    async def async_execute(self, context):
        await self.parse_selected_sbsars_to_library(context)
