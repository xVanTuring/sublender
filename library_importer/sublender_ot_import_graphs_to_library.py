import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty

from .. import preference, props, globalvar


class SublenderOTImportGraphsToLibrary(bpy.types.Operator):
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
        return self.import_graphs_to_library(context)

    def import_graphs_to_library(self, context):
        graphtask_list = []
        for importing_graph in context.scene.sublender_library.importing_graphs:
            if not importing_graph.enable:
                continue
            category = importing_graph.category
            if category == "$CUSTOM$":
                category = importing_graph.category_str
            graph_item = props.new_graph_item(
                importing_graph.graph_url, category, importing_graph.package_path
            )
            for preset in importing_graph.importing_presets:
                if not preset.enable:
                    continue
                graph_item["presets"].append(preset.name)
            graphtask_list.append(graph_item)

        print(graphtask_list)
        globalvar.queue.put_nowait(graphtask_list)
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
        preferences = preference.get_preferences()
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
