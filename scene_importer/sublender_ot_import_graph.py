import os.path
import typing

import bpy
from bpy.props import BoolProperty, EnumProperty

from .. import (
    utils,
    workflow,
    preference,
    props,
    globalvar,
    consts,
    property_group,
    sbsar_import,
    formatting,
    datatypes
)

from ..props import ImportingGraphItem


class SublenderOTImportGraph(bpy.types.Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    use_same_config: BoolProperty(default=True, name="Use Same Config")
    use_fake_user: BoolProperty(name="Fake User", default=True)
    assign_to_selection: BoolProperty(name="Append to selected mesh", default=False)
    material_template: EnumProperty(
        items=globalvar.material_template_enum, name="Template"
    )

    def execute(self, context):
        return self.import_graph(context)

    def import_graph(self, context):
        importing_graphs: typing.List[ImportingGraphItem] = props.scene.get_scene_setting(context).importing_graphs
        render_package = []
        for importing_graph in importing_graphs:
            if not importing_graph.enable:
                continue
            render_package.append(importing_graph.package_path)
            self.import_one_graph(context, importing_graph)

        bpy.ops.sublender.render_texture_async(
            issused_by_importing=True, package_paths="|".join(render_package)
        )
        return {"FINISHED"}

    def import_one_graph(self, context, importing_graph: ImportingGraphItem):

        active_material_template = (
            self.material_template
            if self.use_same_config
            else importing_graph.material_template
        )
        material = self.build_material(importing_graph, active_material_template)

        assign_to_selection = (
            self.assign_to_selection
            if self.use_same_config
            else importing_graph.assign_to_selection
        )
        if assign_to_selection:
            self.apply_to_selected_object(importing_graph, material)

        m_sublender = props.get_material_sublender(material)

        props.scene.get_scene_setting(
            context
        ).active_graph = importing_graph.graph_url

        clss_info, clss_name = self.find_sbs_graph_class(importing_graph, m_sublender)

        if preference.get_preferences().enable_visible_if:
            self.apply_visible_if_setting(clss_name, material)

        self.apply_template_to_material(active_material_template, clss_info, clss_name, material)

        if importing_graph.preset_name != "":
            utils.apply_preset(material, importing_graph.preset_name)

    def apply_visible_if_setting(self, clss_name, material):
        globalvar.eval_delegate_map[
            material.name
        ] = sbsar_import.helper_class.EvalDelegate(material.name, clss_name)

    def find_sbs_graph_class(self, importing_graph: ImportingGraphItem, m_sublender):
        sbs_graph = None
        for graph in globalvar.sbsar_dict.get(m_sublender.package_path).graphs:
            if graph.pkgUrl == importing_graph.graph_url:
                sbs_graph = graph
                break
        clss_name, clss_info = property_group.ensure_graph_property_group(
            sbs_graph, importing_graph.graph_url
        )
        return clss_info, clss_name

    def apply_template_to_material(self, active_material_template, clss_info, clss_name, material):
        graph_setting = getattr(material, clss_name)
        if active_material_template != consts.CUSTOM:
            self.inflate_material_by_template(active_material_template, clss_info, graph_setting, material)
        else:
            self.enable_all_output(clss_info, graph_setting)
        setattr(graph_setting, consts.SBS_CONFIGURED, True)

    def enable_all_output(self, clss_info, graph_setting):
        for output_info in clss_info.output_info.list:
            setattr(
                graph_setting,
                formatting.sb_output_to_prop(output_info.name),
                True,
            )

    def inflate_material_by_template(self, active_material_template: str, clss_info: 'datatypes.GraphClassInfoData',
                                     graph_setting, material: 'bpy.types.Material'):
        material_template = globalvar.material_templates.get(
            active_material_template
        )
        output_info_usage = clss_info.output_info.usage
        for template_texture in material_template["texture"]:
            if output_info_usage.get(template_texture) is not None:
                name = output_info_usage.get(template_texture)[0]
                setattr(graph_setting, formatting.sb_output_to_prop(name), True)
        workflow.inflate_template(material, self.material_template, True)

    def apply_to_selected_object(self, importing_graph: ImportingGraphItem, material: bpy.types.Material):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            active_obj.data.materials.append(material)

    def build_material(self, importing_graph: ImportingGraphItem, active_material_template) -> bpy.types.Material:
        material = bpy.data.materials.new(importing_graph.material_name)

        importing_graph.material_name = material.name
        material.use_nodes = True
        material.use_fake_user = (
            self.use_fake_user
            if self.use_same_config
            else importing_graph.use_fake_user
        )

        m_sublender = props.get_material_sublender(material)
        m_sublender.graph_url = importing_graph.graph_url
        m_sublender.package_path = importing_graph.package_path
        m_sublender.material_template = active_material_template
        m_sublender.package_loaded = True
        if importing_graph.library_uid != "":
            m_sublender.library_uid = importing_graph.library_uid
        return material

    def invoke(self, context, _):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=350, title="Import Setting")

    def draw(self, context):
        importing_graphs = props.scene.get_scene_setting(context).importing_graphs
        if len(importing_graphs) > 1:
            self.layout.prop(self, "use_same_config", toggle=1)
        previous_package_file = ""
        if self.use_same_config:
            self.draw_with_same_config(importing_graphs, previous_package_file)
        else:
            self.draw_with_diff_config(importing_graphs)

    def draw_with_same_config(self, importing_graphs, previous_package_file):
        for importing_graph in importing_graphs:
            if previous_package_file != importing_graph.package_path:
                previous_package_file = importing_graph.package_path
                self.layout.label(text=os.path.basename(previous_package_file))
            self.layout.prop(
                importing_graph,
                "enable",
                text="Import {}".format(importing_graph.graph_url),
            )
            self.layout.prop(importing_graph, "material_name")
        self.layout.separator()
        self.layout.prop(self, "material_template")
        row = self.layout.row()
        row.prop(self, "use_fake_user", icon="FAKE_USER_ON")
        row.prop(self, "assign_to_selection", toggle=1)

    def draw_with_diff_config(self, importing_graphs):
        for importing_graph in importing_graphs:
            self.layout.prop(
                importing_graph,
                "enable",
                text="Import {}".format(importing_graph.graph_url),
            )
            self.layout.prop(importing_graph, "material_name")
            self.layout.prop(importing_graph, "material_template")
            row = self.layout.row()
            row.prop(importing_graph, "use_fake_user", icon="FAKE_USER_ON")
            row.prop(importing_graph, "assign_to_selection", toggle=1)
            self.layout.separator()
