import bpy
from bpy.props import StringProperty
from .. import (
    utils,
    async_loop,
    props,
    globalvar,
    sbsar_import,
    formatting,
)
from ..props import ImportingGraphItem


class SublenderOTImportSbsarFromLibrary(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.import_sbsar_from_library"
    bl_label = "Import"
    bl_description = "Import"
    task_id = "SublenderOTImportSbsarFromLibrary"
    sbsar_path = ""
    pkg_url = ""

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        if not utils.sublender_inited(context):
            await utils.init_sublender_async(self, context)

        self.load_package_source(context)

        sbs_pkg = await sbsar_import.load_sbsar_to_dict_async(
            self.sbsar_path, self.report
        )
        if sbs_pkg is None:
            self.report({"INFO"}, "Failed to load sbsar package")
            return

        importing_graphs = props.scene.get_scene_setting(context).importing_graphs
        importing_graphs.clear()

        for graph_info in sbs_pkg.graphs:
            if self.pkg_url != "" and graph_info.pkgUrl != self.pkg_url:
                continue
            await self.configure_graph_importing(context, graph_info, importing_graphs, sbs_pkg)

        bpy.ops.sublender.import_graph("INVOKE_DEFAULT")

    def load_package_source(self, context: bpy.types.Context):
        sbs_graph_info = globalvar.library["materials"].get(context.scene.sublender_library.active_material)
        self.sbsar_path = sbs_graph_info["sbsar_path"]
        self.pkg_url = sbs_graph_info["pkg_url"]

    async def configure_graph_importing(self, context, graph_info, importing_graphs, sbs_pkg):
        importing_graph: ImportingGraphItem = importing_graphs.add()
        importing_graph.graph_url = graph_info.pkgUrl
        importing_graph.material_name = formatting.new_material_name(
            graph_info.label
        )
        importing_graph.package_path = self.sbsar_path
        label = graph_info.label or bpy.utils.escape_identifier(
            importing_graph.graph_url
        ).replace("://", "")
        importing_graph.library_uid = "{}_{}".format(label, sbs_pkg.asmuid)
        self.apply_preset(context, importing_graph)

    def apply_preset(self, context, importing_graph):
        active_material = context.scene.sublender_library.active_material
        if len(globalvar.library_material_preset_map.get(active_material)) == 0:
            return
        if context.scene.sublender_library.material_preset == "$DEFAULT$":
            return

        importing_graph.preset_name = context.scene.sublender_library.material_preset
        importing_graph.material_name = formatting.new_material_name(
            importing_graph.preset_name
        )


cls_list = [
    SublenderOTImportSbsarFromLibrary
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
