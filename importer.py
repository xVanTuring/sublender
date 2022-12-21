import asyncio
import pathlib

import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from . import globalvar, utils, async_loop, consts, template
from .settings import Sublender_Material_MT_Setting
from .utils import new_material_name, EvalDelegate


class Sublender_Import_Graph(Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    package_path: StringProperty(
        name='Current Graph')
    use_same_config: BoolProperty(default=True, name="Use Same Config")
    use_fake_user: BoolProperty(
        name="Fake User",
        default=True
    )
    assign_to_selection: BoolProperty(
        name='Append to selected mesh',
        default=False
    )
    material_template: EnumProperty(
        items=globalvar.material_template_enum,
        name='Template'
    )

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

            bpy.context.scene.sublender_settings.active_graph = importing_graph.graph_url
            sbs_package = None
            for graph in globalvar.sbsar_dict.get(self.package_path)['graphs']:
                if graph['pkgUrl'] == importing_graph.graph_url:
                    sbs_package = graph
                    break
            clss_name, clss_info = utils.dynamic_gen_clss_graph(sbs_package, importing_graph.graph_url)
            preferences = context.preferences.addons[__package__].preferences
            if preferences.enable_visible_if:
                globalvar.eval_delegate_map[material.name] = EvalDelegate(
                    material.name,
                    clss_name
                )

            graph_setting = getattr(material, clss_name)
            if active_material_template != consts.CUSTOM:
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
            setattr(graph_setting, consts.SBS_CONFIGURED, True)
        bpy.ops.sublender.render_texture_async(importing_graph=True, package_path=self.package_path)
        return {'FINISHED'}

    def invoke(self, context, event):
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


class Sublender_Sbsar_Selector(Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    filename_ext = ".sbsar"
    to_library: BoolProperty(default=False, name="Import To Library")
    filter_glob: StringProperty(
        default="*.sbsar",
        options={'HIDDEN'},
        maxlen=255
    )

    def execute(self, context):
        file_extension = pathlib.Path(self.filepath).suffix
        if not file_extension == ".sbsar":
            self.report({'WARNING'}, "File extension doesn't match")
            return {'CANCELLED'}
        else:
            if self.to_library:
                bpy.ops.sublender.import_sbsar_to_library(sbsar_path=self.filepath)
            else:
                bpy.ops.sublender.import_sbsar(sbsar_path=self.filepath, from_library=False)
        return {'FINISHED'}


class Sublender_Import_Sbsar_To_Library(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.import_sbsar_to_library"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    sbsar_path: StringProperty()
    task_id = "Sublender_Import_Sbsar_To_Library"

    async def async_execute(self, context):
        loop = asyncio.get_event_loop()
        self.report({"INFO"}, "Parsing package: {0}".format(self.sbsar_path))
        sbs_pkg = await loop.run_in_executor(None, utils.load_sbsar_package, self.sbsar_path)
        if sbs_pkg is not None:
            globalvar.sbsar_dict[self.sbsar_path] = sbs_pkg

            importing_graphs = context.scene.sublender_library.importing_graphs
            importing_graphs.clear()
            for graph_info in sbs_pkg['graphs']:
                adding_graph = importing_graphs.add()
                adding_graph.graph_url = graph_info["pkgUrl"]
            bpy.ops.sublender.import_graph_to_library(
                'INVOKE_DEFAULT', package_path=self.sbsar_path)


class Sublender_Import_Sbsar(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.import_sbsar"
    bl_label = "Import"
    bl_description = "Import"
    sbsar_path: StringProperty()
    task_id = "Sublender_Import_Sbsar"
    from_library: BoolProperty(default=False)
    pkg_url = ""

    @classmethod
    def poll(cls, context):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        if not utils.inited(context):
            await utils.init_sublender_async(self, context)
        loop = asyncio.get_event_loop()
        if self.from_library:
            selected_label = context.scene.sublender_library.library_preview
            sbs_graph_info = globalvar.library["materials"].get(selected_label)
            self.sbsar_path = sbs_graph_info["sbsar_path"]
            self.pkg_url = sbs_graph_info["pkg_url"]
        self.report({"INFO"}, "Parsing package: {0}".format(self.sbsar_path))
        sbs_pkg = await loop.run_in_executor(None, utils.load_sbsar_package, self.sbsar_path)
        if sbs_pkg is not None:
            globalvar.sbsar_dict[self.sbsar_path] = sbs_pkg

            importing_graph_items = context.scene.sublender_settings.importing_graphs
            importing_graph_items.clear()
            for graph_info in sbs_pkg['graphs']:
                if self.pkg_url != "" and graph_info["pkgUrl"] != self.pkg_url:
                    continue
                importing_graph = importing_graph_items.add()
                importing_graph.graph_url = graph_info["pkgUrl"]
                importing_graph.material_name = new_material_name(graph_info['label'])
            bpy.ops.sublender.import_graph(
                'INVOKE_DEFAULT', package_path=self.sbsar_path)


class Sublender_Import_Graph_To_Library(Operator):
    bl_idname = "sublender.import_graph_to_library"
    bl_label = "Import Package"
    package_path: StringProperty(
        name='Current Graph')
    engine: EnumProperty(items=[("eevee", "Eevee", ""), ("cycles", "Cycles", "")], name="Preview Engine")

    def execute(self, context):
        bpy.ops.sublender.render_preview_async(package_path=self.package_path)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        for graph in context.scene.sublender_library.importing_graphs:
            self.layout.prop(graph, "enable", text="Import {}".format(graph.graph_url))
        self.layout.prop(self, 'engine')


def register():
    bpy.utils.register_class(Sublender_Import_Graph)
    bpy.utils.register_class(Sublender_Import_Sbsar)
    bpy.utils.register_class(Sublender_Sbsar_Selector)
    bpy.utils.register_class(Sublender_Import_Graph_To_Library)
    bpy.utils.register_class(Sublender_Import_Sbsar_To_Library)


def unregister():
    bpy.utils.unregister_class(Sublender_Import_Graph)
    bpy.utils.unregister_class(Sublender_Import_Sbsar)
    bpy.utils.unregister_class(Sublender_Sbsar_Selector)
    bpy.utils.unregister_class(Sublender_Import_Graph_To_Library)
    bpy.utils.unregister_class(Sublender_Import_Sbsar_To_Library)
