import asyncio
import pathlib

import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty, CollectionProperty)
from bpy.types import Operator, OperatorFileListElement
from bpy_extras.io_utils import ImportHelper

from . import globalvar, utils, async_loop, template
from .settings import Sublender_Material_MT_Setting, new_graph_item
from .utils import new_material_name, EvalDelegate


class SublenderOTImportGraph(Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    package_path: StringProperty(name='Current Graph')
    use_same_config: BoolProperty(default=True, name="Use Same Config")
    use_fake_user: BoolProperty(name="Fake User", default=True)
    assign_to_selection: BoolProperty(name='Append to selected mesh', default=False)
    material_template: EnumProperty(items=globalvar.material_template_enum, name='Template')

    def execute(self, context):
        importing_graph_items = context.scene.sublender_settings.importing_graphs
        for importing_graph in importing_graph_items:
            if not importing_graph.enable:
                continue
            active_material_template = self.material_template if self.use_same_config \
                else importing_graph.material_template
            material = bpy.data.materials.new(importing_graph.material_name)
            # Reassign material name
            importing_graph.material_name = material.name
            material.use_nodes = True
            material.use_fake_user = self.use_fake_user if self.use_same_config \
                else importing_graph.use_fake_user
            assign_to_selection = self.assign_to_selection if self.use_same_config \
                else importing_graph.assign_to_selection
            active_obj = bpy.context.view_layer.objects.active
            if assign_to_selection and active_obj is not None:
                active_obj.data.materials.append(material)

            m_sublender: Sublender_Material_MT_Setting = material.sublender
            m_sublender.graph_url = importing_graph.graph_url
            m_sublender.package_path = self.package_path
            m_sublender.material_template = active_material_template
            m_sublender.package_loaded = True

            if importing_graph.library_uid != "":
                m_sublender.library_uid = importing_graph.library_uid
            bpy.context.scene.sublender_settings.active_graph = importing_graph.graph_url
            sbs_package = None
            for graph in globalvar.sbsar_dict.get(self.package_path)['graphs']:
                if graph['pkgUrl'] == importing_graph.graph_url:
                    sbs_package = graph
                    break
            clss_name, clss_info = utils.dynamic_gen_clss_graph(sbs_package, importing_graph.graph_url)
            preferences = context.preferences.addons[__package__].preferences
            if preferences.enable_visible_if:
                globalvar.eval_delegate_map[material.name] = EvalDelegate(material.name, clss_name)

            graph_setting = getattr(material, clss_name)
            if active_material_template != utils.consts.CUSTOM:
                material_template = globalvar.material_templates.get(active_material_template)
                output_info_usage: dict = clss_info['output_info']['usage']
                for template_texture in material_template['texture']:
                    if output_info_usage.get(template_texture) is not None:
                        name = output_info_usage.get(template_texture)[0]
                        setattr(graph_setting, utils.sb_output_to_prop(name), True)
                template.inflate_template(material, self.material_template, True)
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
        importing_graph_items = context.scene.sublender_settings.importing_graphs
        if len(importing_graph_items) > 1:
            self.layout.prop(self, "use_same_config", toggle=1)
        if self.use_same_config:
            for importing_graph in importing_graph_items:
                self.layout.prop(importing_graph, "enable", text="Import {}".format(importing_graph.graph_url))
                self.layout.prop(importing_graph, "material_name")
            self.layout.prop(self, "material_template")
            row = self.layout.row()
            row.prop(self, "use_fake_user", icon='FAKE_USER_ON')
            row.prop(self, "assign_to_selection", toggle=1)
        else:
            for importing_graph in importing_graph_items:
                self.layout.prop(importing_graph, "enable", text="Import {}".format(importing_graph.graph_url))
                self.layout.prop(importing_graph, "material_name")
                self.layout.prop(importing_graph, "material_template")
                row = self.layout.row()
                row.prop(importing_graph, "use_fake_user", icon='FAKE_USER_ON')
                row.prop(importing_graph, "assign_to_selection", toggle=1)


# TODO register importer to import menu
class SublenderOTSelectSbsar(Operator, ImportHelper):
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


class SublenderOTImportSbsar(async_loop.AsyncModalOperatorMixin, Operator):
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
            sbs_graph_info = globalvar.library["materials"].get(active_material)
            self.sbsar_path = sbs_graph_info["sbsar_path"]
            self.pkg_url = sbs_graph_info["pkg_url"]
        sbs_pkg = await utils.load_sbsar_to_dict_async(self.sbsar_path, self.report)
        if sbs_pkg is not None:
            importing_graph_items = context.scene.sublender_settings.importing_graphs
            importing_graph_items.clear()
            for graph_info in sbs_pkg['graphs']:
                if self.pkg_url != "" and graph_info["pkgUrl"] != self.pkg_url:
                    continue
                importing_graph = importing_graph_items.add()
                importing_graph.graph_url = graph_info["pkgUrl"]
                importing_graph.material_name = new_material_name(graph_info['label'])
                if self.from_library:
                    label = graph_info['label']
                    if label == "":
                        label = bpy.utils.escape_identifier(importing_graph.graph_url).replace("://", "")
                    importing_graph.library_uid = "{}_{}".format(label, sbs_pkg["asmuid"])
                    active_material = context.scene.sublender_library.active_material
                    if len(globalvar.library_material_preset_map.get(active_material)) > 0:
                        if context.scene.sublender_library.material_preset != "$DEFAULT$":
                            importing_graph.preset_name = context.scene.sublender_library.material_preset
                            importing_graph.material_name = new_material_name(importing_graph.preset_name)
            bpy.ops.sublender.import_graph('INVOKE_DEFAULT', package_path=self.sbsar_path)


class SublenderOTSelectSbsarLibrary(Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar_to_library"
    bl_label = "Import Sbsar to Library"
    bl_description = "Import Sbsar to Library"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(default="*.sbsar", options={'HIDDEN'}, maxlen=255)
    # https://gist.github.com/batFINGER/2c0604be3620def01c4eeaff6ceb22f4
    files: CollectionProperty(name="Sbsar files", type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    @classmethod
    def poll(cls, context):
        return len(context.scene.sublender_library.importing_graphs) == 0

    def execute(self, context):
        files_str = ""
        importing_graphs = context.scene.sublender_library.importing_graphs
        importing_graphs.clear()
        for file in self.files:
            if pathlib.Path(file.name).suffix != ".sbsar":
                self.report({'WARNING'}, "File extension doesn't match")
                return {'CANCELLED'}
            files_str += "%s|" % str(pathlib.Path(self.directory, file.name))
        bpy.ops.sublender.parse_selected_sbsars(files_list=files_str)
        return {'FINISHED'}


class SublenderOTParseSelectedSbsars(async_loop.AsyncModalOperatorMixin, Operator):
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
                for graph_info in sbs_pkg['graphs']:
                    adding_graph = importing_graphs.add()
                    adding_graph.graph_url = graph_info["pkgUrl"]
                    adding_graph.category_str = graph_info["category"]
                    adding_graph.package_path = sbsar_path
                    for preset_name in graph_info['presets'].keys():
                        importing_preset = adding_graph.importing_presets.add()
                        importing_preset.name = preset_name
        bpy.ops.sublender.import_graphs_to_library('INVOKE_DEFAULT')


class SublenderOTImportGraphesToLibrary(Operator):
    bl_idname = "sublender.import_graphs_to_library"
    bl_label = "Import Package"
    engine: EnumProperty(items=[("eevee", "Eevee", ""), ("cycles", "Cycles", "")], name="Engine")
    invert_normal: BoolProperty(
        name="Invert Normal",
        description="Blender use OpenGL's Normal Format, while most substance materials use DirectX's "
        "Normal Format. "
        "Usually there is parameter included in the substance material controlling the Normal Format. "
        "Conversion can be done by inverting the G channel of Normal texture.")
    cloth_template: BoolProperty(default=False, name="Use Cloth Template")

    def execute(self, context):
        graphtask_list = []
        for importing_graph in context.scene.sublender_library.importing_graphs:
            if not importing_graph.enable:
                continue
            category = importing_graph.category
            if category == "$CUSTOM$":
                category = importing_graph.category_str
            graph_item = new_graph_item(importing_graph.graph_url, category, importing_graph.package_path)
            for preset in importing_graph.importing_presets:
                if not preset.enable:
                    continue
                graph_item["presets"].append(preset.name)
            graphtask_list.append(graph_item)
        globalvar.queue.put_nowait(graphtask_list)
        context.scene.sublender_library.importing_graphs.clear()
        bpy.ops.sublender.render_preview_async(engine=self.engine,
                                               invert_normal=self.invert_normal,
                                               cloth_template=self.cloth_template)
        return {'FINISHED'}

    def cancel(self, context):
        context.scene.sublender_library.importing_graphs.clear()

    def invoke(self, context, _):
        wm = context.window_manager
        preferences = bpy.context.preferences.addons[__package__].preferences
        self.engine = preferences.library_preview_engine
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        for importing_graph in context.scene.sublender_library.importing_graphs:
            self.layout.prop(importing_graph, "enable", text="Import {}".format(importing_graph.graph_url))
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
                    column.prop(importing_preset, "enable", text="Preset {}".format(importing_preset.name))
                column.enabled = importing_graph.enable
            self.layout.separator()
        self.layout.prop(self, 'engine')
        row = self.layout.row()
        row.prop(self, 'invert_normal', toggle=1)
        row.prop(self, 'cloth_template', toggle=1)


def register():
    bpy.utils.register_class(SublenderOTImportGraph)
    bpy.utils.register_class(SublenderOTImportSbsar)
    bpy.utils.register_class(SublenderOTSelectSbsar)
    bpy.utils.register_class(SublenderOTImportGraphesToLibrary)
    bpy.utils.register_class(SublenderOTParseSelectedSbsars)
    bpy.utils.register_class(SublenderOTSelectSbsarLibrary)


def unregister():
    bpy.utils.unregister_class(SublenderOTSelectSbsarLibrary)
    bpy.utils.unregister_class(SublenderOTImportGraph)
    bpy.utils.unregister_class(SublenderOTImportSbsar)
    bpy.utils.unregister_class(SublenderOTSelectSbsar)
    bpy.utils.unregister_class(SublenderOTImportGraphesToLibrary)
    bpy.utils.unregister_class(SublenderOTParseSelectedSbsars)
