import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from bpy_extras.io_utils import ImportHelper

from .. import utils, async_loop, workflow
from ..utils import new_material_name


# TODO batch import
# TODO register importer to import menu
class SublenderOTSelectSbsar(bpy.types.Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(default="*.sbsar", options={'HIDDEN'}, maxlen=255)
    filepath: StringProperty(subtype='FILE_PATH')

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    def execute(self, _):
        bpy.ops.sublender.import_sbsar(sbsar_path=self.filepath, from_library=False)
        return {'FINISHED'}


class SublenderOTImportSbsar(async_loop.AsyncModalOperatorMixin, bpy.types.Operator):
    bl_idname = "sublender.import_sbsar"
    bl_label = "Import"
    bl_description = "Import"
    sbsar_path: StringProperty()
    task_id = "SublenderOTImportSbsar"
    from_library: BoolProperty(default=False)
    pkg_url = ""

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        if not utils.sublender_inited(context):
            await utils.init_sublender_async(self, context)
        if self.from_library:
            active_material = context.scene.sublender_library.active_material
            sbs_graph_info = utils.globalvar.library["materials"].get(active_material)
            self.sbsar_path = sbs_graph_info["sbsar_path"]
            self.pkg_url = sbs_graph_info["pkg_url"]
        sbs_pkg = await utils.load_sbsar_to_dict_async(self.sbsar_path, self.report)
        if sbs_pkg is not None:
            importing_graphs = context.scene.sublender_settings.importing_graphs
            importing_graphs.clear()
            for graph_info in sbs_pkg['graphs']:
                if self.pkg_url != "" and graph_info["pkgUrl"] != self.pkg_url:
                    continue
                importing_graph = importing_graphs.add()
                importing_graph.graph_url = graph_info["pkgUrl"]
                importing_graph.material_name = new_material_name(graph_info['label'])
                if self.from_library:
                    label = graph_info['label']
                    if label == "":
                        label = bpy.utils.escape_identifier(importing_graph.graph_url).replace("://", "")
                    importing_graph.library_uid = "{}_{}".format(label, sbs_pkg["asmuid"])
                    active_material = context.scene.sublender_library.active_material
                    if len(utils.globalvar.library_material_preset_map.get(active_material)) > 0:
                        if context.scene.sublender_library.material_preset != "$DEFAULT$":
                            importing_graph.preset_name = context.scene.sublender_library.material_preset
                            importing_graph.material_name = new_material_name(importing_graph.preset_name)
            bpy.ops.sublender.import_graph('INVOKE_DEFAULT', package_path=self.sbsar_path)


class SublenderOTImportGraph(bpy.types.Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    package_path: StringProperty(name='Current Graph')
    use_same_config: BoolProperty(default=True, name="Use Same Config")
    use_fake_user: BoolProperty(name="Fake User", default=True)
    assign_to_selection: BoolProperty(name='Append to selected mesh', default=False)
    material_template: EnumProperty(items=utils.globalvar.material_template_enum, name='Template')

    def execute(self, context):
        importing_graphs = context.scene.sublender_settings.importing_graphs
        for importing_graph in importing_graphs:
            if not importing_graph.enable:
                continue
            active_material_template = (self.material_template
                                        if self.use_same_config else importing_graph.material_template)
            material = bpy.data.materials.new(importing_graph.material_name)
            # Reassign material name
            importing_graph.material_name = material.name
            material.use_nodes = True
            material.use_fake_user = (self.use_fake_user if self.use_same_config else importing_graph.use_fake_user)
            assign_to_selection = (self.assign_to_selection
                                   if self.use_same_config else importing_graph.assign_to_selection)
            active_obj = bpy.context.view_layer.objects.active
            if assign_to_selection and active_obj is not None:
                active_obj.data.materials.append(material)

            m_sublender = material.sublender
            m_sublender.graph_url = importing_graph.graph_url
            m_sublender.package_path = self.package_path
            m_sublender.material_template = active_material_template
            m_sublender.package_loaded = True

            if importing_graph.library_uid != "":
                m_sublender.library_uid = importing_graph.library_uid
            bpy.context.scene.sublender_settings.active_graph = importing_graph.graph_url
            sbs_package = None
            for graph in utils.globalvar.sbsar_dict.get(self.package_path)['graphs']:
                if graph['pkgUrl'] == importing_graph.graph_url:
                    sbs_package = graph
                    break
            clss_name, clss_info = utils.ensure_graph_property_group(sbs_package, importing_graph.graph_url)
            preferences = utils.get_addon_preferences(context)
            if preferences.enable_visible_if:
                utils.globalvar.eval_delegate_map[material.name] = utils.helper_class.EvalDelegate(material.name, clss_name)

            graph_setting = getattr(material, clss_name)
            if active_material_template != utils.consts.CUSTOM:
                material_template = utils.globalvar.material_templates.get(active_material_template)
                output_info_usage: dict = clss_info['output_info']['usage']
                for template_texture in material_template['texture']:
                    if output_info_usage.get(template_texture) is not None:
                        name = output_info_usage.get(template_texture)[0]
                        setattr(graph_setting, utils.sb_output_to_prop(name), True)
                workflow.inflate_template(material, self.material_template, True)
            else:
                for output_info in clss_info['output_info']['list']:
                    setattr(graph_setting, utils.sb_output_to_prop(output_info['name']), True)
            setattr(graph_setting, utils.consts.SBS_CONFIGURED, True)
            if importing_graph.preset_name != "":
                utils.apply_preset(material, importing_graph.preset_name)
        bpy.ops.sublender.render_texture_async(importing_graph=True, package_path=self.package_path)
        return {'FINISHED'}

    def invoke(self, context, _):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=350)

    def draw(self, context):
        importing_graphs = context.scene.sublender_settings.importing_graphs
        if len(importing_graphs) > 1:
            self.layout.prop(self, "use_same_config", toggle=1)
        if self.use_same_config:
            for importing_graph in importing_graphs:
                self.layout.prop(importing_graph, "enable", text="Import {}".format(importing_graph.graph_url))
                self.layout.prop(importing_graph, "material_name")
            self.layout.prop(self, "material_template")
            row = self.layout.row()
            row.prop(self, "use_fake_user", icon='FAKE_USER_ON')
            row.prop(self, "assign_to_selection", toggle=1)
        else:
            for importing_graph in importing_graphs:
                self.layout.prop(importing_graph, "enable", text="Import {}".format(importing_graph.graph_url))
                self.layout.prop(importing_graph, "material_name")
                self.layout.prop(importing_graph, "material_template")
                row = self.layout.row()
                row.prop(importing_graph, "use_fake_user", icon='FAKE_USER_ON')
                row.prop(importing_graph, "assign_to_selection", toggle=1)


cls_list = [
    SublenderOTImportGraph,
    SublenderOTImportSbsar,
    SublenderOTSelectSbsar,
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
