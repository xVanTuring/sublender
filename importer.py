from bpy.props import (PointerProperty, StringProperty, BoolProperty, CollectionProperty,
                       EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)

from . utils import new_material_name, dynamic_gen_clss
from . import globalvar, consts
import bpy
import pathlib
from . template import inflate_template
from . settings import Sublender_Material_MT_Setting
from pysbs import sbsarchive
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from typing import List
from pysbs.sbsarchive.sbsarchive import SBSARGraph


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
        name='Assign to Selected(Override all texture)',
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

        m_sublender: Sublender_Material_MT_Setting = material.sublender
        m_sublender.graph_url = self.graph_url
        m_sublender.package_path = self.package_path
        m_sublender.material_template = self.material_template

        bpy.context.scene.sublender_settings.active_graph = self.graph_url
        dynamic_gen_clss(
            self.package_path, self.graph_url)
        if self.material_template != consts.CUSTOM:
            inflate_template(material, self.material_template)

        bpy.ops.sublender.render_texture_async(
            assign_texture=self.material_template != consts.CUSTOM,
            material_name=material.name)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Import " + self.graph_url, icon="IMPORT")
        col = layout.column()
        col.alignment = 'CENTER'
        col.prop(self, "material_name")
        col.prop(self, "use_fake_user", icon='FAKE_USER_ON')
        col.prop(self, "assign_to_selection")
        col.prop(self, "material_template")


class Sublender_Import_Sbsar(Operator, ImportHelper):
    bl_idname = "sublender.import_sbsar"
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
            importing_package = sbsarchive.SBSArchive(
                globalvar.aContext, self.filepath)
            importing_package.parseDoc()

            sbs_graph_list: List[SBSARGraph] = importing_package.getSBSGraphList(
            )
            globalvar.sbsar_dict[self.filepath] = importing_package
            for graph in sbs_graph_list:
                # INVOKE_DEFAULT
                bpy.ops.sublender.import_graph(
                    'INVOKE_DEFAULT', package_path=self.filepath,
                    graph_url=graph.mPkgUrl, material_name=graph.mLabel)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(Sublender_Import_Graph)
    bpy.utils.register_class(Sublender_Import_Sbsar)


def unregister():
    bpy.utils.unregister_class(Sublender_Import_Graph)
    bpy.utils.unregister_class(Sublender_Import_Sbsar)
