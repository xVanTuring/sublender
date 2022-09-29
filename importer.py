import asyncio
import pathlib
from typing import List

import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from pysbs.sbsarchive.sbsarchive import SBSARGraph

from . import globalvar, utils, async_loop, consts, template
from .settings import Sublender_Material_MT_Setting
from .utils import new_material_name, EvalDelegate


class Sublender_Import_Graph(Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    graph_url: StringProperty(
        name='Current Graph')
    package_path: StringProperty(
        name='Current Graph')
    material_name: StringProperty(
        name='Material Name')
    use_fake_user: BoolProperty(
        name="Fake User",
        default=True
    )
    assign_to_selection: BoolProperty(
        name='Assign to Selected(append)',
        default=False
    )
    material_template: EnumProperty(
        items=globalvar.material_template_enum,
        name='Material Template'
    )

    def execute(self, context):
        # TODO better custom workflow
        material_name = new_material_name(self.material_name)
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
        material.use_fake_user = self.use_fake_user
        if self.assign_to_selection and bpy.context.view_layer.objects.active is not None:
            bpy.context.view_layer.objects.active.data.materials.append(material)

        m_sublender: Sublender_Material_MT_Setting = material.sublender
        m_sublender.graph_url = self.graph_url
        m_sublender.package_path = self.package_path
        m_sublender.material_template = self.material_template
        m_sublender.package_loaded = True

        bpy.context.scene.sublender_settings.active_graph = self.graph_url
        sbs_package = globalvar.sbsar_dict.get(self.package_path).getSBSGraphFromPkgUrl(self.graph_url)
        clss_name, clss_info = utils.dynamic_gen_clss_graph(sbs_package, self.graph_url)
        preferences = context.preferences.addons[__package__].preferences
        if preferences.enable_visible_if:
            globalvar.eval_delegate_map[material.name] = EvalDelegate(
                material.name,
                clss_name
            )

        material_template = globalvar.material_templates.get(self.material_template)
        output_info_usage: dict = clss_info['output_info']['usage']
        graph_setting = getattr(material, clss_name)
        for template_texture in material_template['texture']:
            if output_info_usage.get(template_texture) is not None:
                name = output_info_usage.get(template_texture)[0]
                setattr(graph_setting, utils.sb_output_to_prop(name), True)
        if self.material_template != consts.CUSTOM:
            template.inflate_template(material, self.material_template, True)
        bpy.ops.sublender.render_texture_async(
            material_name=material.name, assign_material=True)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.label(text="Import " + self.graph_url, icon="IMPORT")
        col = self.layout.column()
        col.alignment = 'CENTER'
        col.prop(self, "material_name")
        col.prop(self, "use_fake_user", icon='FAKE_USER_ON')
        col.prop(self, "assign_to_selection")
        col.prop(self, "material_template")


class Sublender_Sbsar_Selector(Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    filename_ext = ".sbsar"
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
            bpy.ops.sublender.import_sbsar(sbsar_path=self.filepath)
        return {'FINISHED'}


class Sublender_Import_Sbsar(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.import_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    sbsar_path: StringProperty()

    async def async_execute(self, context):
        print("Sublender_Import_Sbsar")
        print("self.filepath {0}".format(self.sbsar_path))
        loop = asyncio.get_event_loop()
        self.report({"INFO"}, "Parsing package: {0}".format(self.sbsar_path))
        sbs_pkg = await loop.run_in_executor(None, utils.load_sbsar_package, self.sbsar_path)
        sbs_graph_list: List[SBSARGraph] = sbs_pkg.getSBSGraphList()
        globalvar.sbsar_dict[self.sbsar_path] = sbs_pkg
        # TODO Better multiple graph popover
        for graph in sbs_graph_list:
            bpy.ops.sublender.import_graph(
                'INVOKE_DEFAULT', package_path=self.sbsar_path,
                graph_url=graph.mPkgUrl, material_name=graph.mLabel)


def register():
    bpy.utils.register_class(Sublender_Import_Graph)
    bpy.utils.register_class(Sublender_Import_Sbsar)
    bpy.utils.register_class(Sublender_Sbsar_Selector)


def unregister():
    bpy.utils.unregister_class(Sublender_Import_Graph)
    bpy.utils.unregister_class(Sublender_Import_Sbsar)
    bpy.utils.unregister_class(Sublender_Sbsar_Selector)
