import asyncio
import os.path
import typing

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

from .. import (
    utils,
    async_loop,
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
from ..parser import SbsarPackageData, SbsarGraphData
from ..props import ImportingGraphItem


class SublenderOTSelectSbsar(bpy.types.Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(default="*.sbsar", options={"HIDDEN"}, maxlen=255)
    directory: StringProperty(subtype='DIR_PATH')
    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    def execute(self, _):

        import os
        if self.files:
            file_paths = list(map(lambda x: os.path.join(self.directory, x.name), self.files))
            bpy.ops.sublender.import_sbsar(sbsar_paths="|".join(file_paths))
            print("file_paths", file_paths)
            return {"FINISHED"}
        else:
            # bpy.ops.sublender.import_sbsar(sbsar_path=self.filepath)
            return {"FINISHED"}
        return {"FINISHED"}


class SublenderOTImportSbsarFromLibrary(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.import_sbsar_from_library"
    bl_label = "Import"
    bl_description = "Import"
    task_id = "SublenderOTImportSbsarFromLibrary"
    sbsar_path: StringProperty()
    pkg_url = ""

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    def load_from_library(self, context: bpy.types.Context):
        active_material = context.scene.sublender_library.active_material
        sbs_graph_info = globalvar.library["materials"].get(active_material)
        self.sbsar_path = sbs_graph_info["sbsar_path"]
        self.pkg_url = sbs_graph_info["pkg_url"]

    async def async_execute(self, context):
        if not utils.sublender_inited(context):
            await utils.init_sublender_async(self, context)
        self.load_from_library(context)

        sbs_pkg = await sbsar_import.load_sbsar_to_dict_async(
            self.sbsar_path, self.report
        )
        if sbs_pkg is None:
            # TODO: warning not found!
            return

        importing_graphs = props.scene.get_scene_setting(context).importing_graphs
        importing_graphs.clear()

        for graph_info in sbs_pkg.graphs:
            if self.pkg_url != "" and graph_info.pkgUrl != self.pkg_url:
                continue
            importing_graph: ImportingGraphItem = importing_graphs.add()
            importing_graph.graph_url = graph_info.pkgUrl
            importing_graph.material_name = formatting.new_material_name(
                graph_info.label
            )
            importing_graph.package_path = self.sbsar_path
            self.load_from_library_after(context, sbs_pkg, graph_info, importing_graph)
        bpy.ops.sublender.import_graph("INVOKE_DEFAULT")

    def load_from_library_after(
            self,
            context: bpy.types.Context,
            sbs_pkg: SbsarPackageData,
            graph_info: SbsarGraphData,
            importing_graph: ImportingGraphItem,
    ):
        label = graph_info.label or bpy.utils.escape_identifier(
            importing_graph.graph_url
        ).replace("://", "")
        importing_graph.library_uid = "{}_{}".format(label, sbs_pkg.asmuid)
        active_material = context.scene.sublender_library.active_material
        if len(globalvar.library_material_preset_map.get(active_material)) == 0:
            return
        if context.scene.sublender_library.material_preset == "$DEFAULT$":
            return

        importing_graph.preset_name = context.scene.sublender_library.material_preset
        importing_graph.material_name = formatting.new_material_name(
            importing_graph.preset_name
        )


class SublenderOTImportSbsar(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.import_sbsar"
    bl_label = "Import"
    bl_description = "Import"
    task_id = "SublenderOTImportSbsar"
    sbsar_paths: StringProperty()

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        if not utils.sublender_inited(context):
            await utils.init_sublender_async(self, context)
        sbsar_paths = self.sbsar_paths.split("|")
        tasks = map(lambda x: sbsar_import.load_sbsar_to_dict_with_path_async(x, self.report), sbsar_paths)
        result = await asyncio.gather(*tasks)
        sbs_pkgs: typing.List[typing.Tuple[str, 'SbsarPackageData']] = list(filter(lambda x: x[1], result))
        if len(sbs_pkgs) == 0:
            # TODO: warning not found!
            return

        importing_graphs = props.scene.get_scene_setting(context).importing_graphs
        importing_graphs.clear()
        #
        for sbs_pkg in sbs_pkgs:
            for graph_info in sbs_pkg[1].graphs:
                importing_graph: ImportingGraphItem = importing_graphs.add()
                importing_graph.graph_url = graph_info.pkgUrl
                importing_graph.material_name = formatting.new_material_name(
                    graph_info.label
                )
                importing_graph.package_path = sbs_pkg[0]
        bpy.ops.sublender.import_graph("INVOKE_DEFAULT")


class SublenderOTImportGraph(bpy.types.Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    use_same_config: BoolProperty(default=True, name="Use Same Config")
    use_fake_user: BoolProperty(name="Fake User", default=True)
    assign_to_selection: BoolProperty(name="Append to selected mesh", default=False)
    material_template: EnumProperty(
        items=globalvar.material_template_enum, name="Template"
    )

    def handle_import_graph(self, context, importing_graph: ImportingGraphItem, render_package):
        if not importing_graph.enable:
            return
        render_package.append(importing_graph.package_path)
        active_material_template = (
            self.material_template
            if self.use_same_config
            else importing_graph.material_template
        )
        material = self.new_material(importing_graph, active_material_template)

        self.apply_to_selected_object(importing_graph, material)

        m_sublender = props.get_material_sublender(material)

        # FIXME: required when render texture
        props.scene.get_scene_setting(
            context
        ).active_graph = importing_graph.graph_url

        clss_info, clss_name = self.find_sbs_graph_class(importing_graph, m_sublender)
        self.apply_visible_if_setting(clss_name, material)

        self.configure_graph(active_material_template, clss_info, clss_name, material)
        if importing_graph.preset_name != "":
            utils.apply_preset(material, importing_graph.preset_name)

    def execute(self, context):
        importing_graphs: typing.List[ImportingGraphItem] = props.scene.get_scene_setting(context).importing_graphs
        render_package = []
        for importing_graph in importing_graphs:
            self.handle_import_graph(context, importing_graph, render_package)
            
        bpy.ops.sublender.render_texture_async(
            importing_graph=True, package_paths="|".join(render_package)
        )
        return {"FINISHED"}

    def apply_visible_if_setting(self, clss_name, material):
        preferences = preference.get_preferences()
        if preferences.enable_visible_if:
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

    def configure_graph(self, active_material_template, clss_info, clss_name, material):
        graph_setting = getattr(material, clss_name)
        setattr(graph_setting, consts.SBS_CONFIGURED, True)
        if active_material_template != consts.CUSTOM:
            self.inflate_material_by_template(active_material_template, clss_info, graph_setting, material)
        else:
            self.enable_all_output(clss_info, graph_setting)

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
        assign_to_selection = (
            self.assign_to_selection
            if self.use_same_config
            else importing_graph.assign_to_selection
        )
        active_obj = bpy.context.view_layer.objects.active
        if assign_to_selection and active_obj is not None:
            active_obj.data.materials.append(material)

    def new_material(self, importing_graph: ImportingGraphItem, active_material_template) -> bpy.types.Material:
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
        else:
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


cls_list = [
    SublenderOTImportGraph,
    SublenderOTImportSbsar,
    SublenderOTSelectSbsar,
    SublenderOTImportSbsarFromLibrary
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
