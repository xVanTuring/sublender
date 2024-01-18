import pathlib

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

from .. import utils, async_loop
from ..props import new_graph_item


class SublenderOTSelectSbsarLibrary(bpy.types.Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar_to_library"
    bl_label = "Import Sbsar to Library"
    bl_description = "Import Sbsar to Library"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(default="*.sbsar", options={"HIDDEN"}, maxlen=255)
    # https://gist.github.com/batFINGER/2c0604be3620def01c4eeaff6ceb22f4
    files: CollectionProperty(
        name="Sbsar files", type=bpy.types.OperatorFileListElement
    )
    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        return len(context.scene.sublender_library.importing_graphs) == 0

    def execute(self, context):
        files_str = ""
        importing_graphs = context.scene.sublender_library.importing_graphs
        importing_graphs.clear()
        for file in self.files:
            if pathlib.Path(file.name).suffix != ".sbsar":
                self.report({"WARNING"}, "File extension doesn't match")
                return {"CANCELLED"}
            files_str += "%s|" % str(pathlib.Path(self.directory, file.name))
        bpy.ops.sublender.parse_selected_sbsars(files_list=files_str)
        return {"FINISHED"}


class SublenderOTParseSelectedSbsars(
    async_loop.AsyncModalOperatorMixin, bpy.types.Operator
):
    bl_idname = "sublender.parse_selected_sbsars"
    bl_label = "Parse Sbsars"
    bl_description = "Parse Sbsars"

    files_list: StringProperty()
    task_id = "SublenderOTParseSelectedSbsars"

    async def async_execute(self, context):
        importing_graphs = context.scene.sublender_library.importing_graphs
        importing_graphs.clear()
        sbsar_files = filter(lambda x: x, self.files_list.split("|"))
        for sbsar_path in sbsar_files:
            sbs_pkg = await utils.load_sbsar_to_dict_async(sbsar_path, self.report)
            if sbs_pkg is not None:
                for graph_info in sbs_pkg["graphs"]:
                    adding_graph = importing_graphs.add()
                    adding_graph.graph_url = graph_info["pkgUrl"]
                    adding_graph.category_str = graph_info["category"]
                    adding_graph.package_path = sbsar_path
                    for preset_name in graph_info["presets"].keys():
                        importing_preset = adding_graph.importing_presets.add()
                        importing_preset.name = preset_name
        bpy.ops.sublender.import_graphs_to_library("INVOKE_DEFAULT")


class SublenderOTImportGraphesToLibrary(bpy.types.Operator):
    bl_idname = "sublender.import_graphs_to_library"
    bl_label = "Import Package"
    engine: EnumProperty(
        items=[("eevee", "Eevee", ""), ("cycles", "Cycles", "")], name="Engine"
    )
    invert_normal: BoolProperty(
        name="Invert Normal",
        description="Blender use OpenGL's Normal Format, while most substance materials use DirectX's "
        "Normal Format. "
        "Usually there is parameter included in the substance material controlling the Normal Format. "
        "Conversion can be done by inverting the G channel of Normal texture.",
    )
    cloth_template: BoolProperty(default=False, name="Use Cloth Template")

    def execute(self, context):
        graphtask_list = []
        for importing_graph in context.scene.sublender_library.importing_graphs:
            if not importing_graph.enable:
                continue
            category = importing_graph.category
            if category == "$CUSTOM$":
                category = importing_graph.category_str
            graph_item = new_graph_item(
                importing_graph.graph_url, category, importing_graph.package_path
            )
            for preset in importing_graph.importing_presets:
                if not preset.enable:
                    continue
                graph_item["presets"].append(preset.name)
            graphtask_list.append(graph_item)
        utils.globalvar.queue.put_nowait(graphtask_list)
        context.scene.sublender_library.importing_graphs.clear()
        bpy.ops.sublender.render_preview_async(
            engine=self.engine,
            invert_normal=self.invert_normal,
            cloth_template=self.cloth_template,
        )
        return {"FINISHED"}

    def cancel(self, context):
        context.scene.sublender_library.importing_graphs.clear()

    def invoke(self, context, _):
        wm = context.window_manager
        preferences = utils.get_addon_preferences(context)
        self.engine = preferences.library_preview_engine
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        for importing_graph in context.scene.sublender_library.importing_graphs:
            self.layout.prop(
                importing_graph,
                "enable",
                text="Import {}".format(importing_graph.graph_url),
            )
            row = self.layout.row()
            row.prop(importing_graph, "category", text="Category")
            if importing_graph.category == "$CUSTOM$":
                row.prop(importing_graph, "category_str", text="")
            if len(importing_graph.importing_presets) > 0:
                row = self.layout.row()
                space = row.column()
                space.separator()
                column = row.column()
                for importing_preset in importing_graph.importing_presets:
                    column.prop(
                        importing_preset,
                        "enable",
                        text="Preset {}".format(importing_preset.name),
                    )
                column.enabled = importing_graph.enable
            self.layout.separator()
        self.layout.prop(self, "engine")
        row = self.layout.row()
        row.prop(self, "invert_normal", toggle=1)
        row.prop(self, "cloth_template", toggle=1)


cls_list = [
    SublenderOTImportGraphesToLibrary,
    SublenderOTParseSelectedSbsars,
    SublenderOTSelectSbsarLibrary,
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
