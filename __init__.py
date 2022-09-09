if "bpy" in locals():
    from importlib import reload
    template = reload(template)
    utils = reload(utils)
    settings = reload(settings)
    parser = reload(parser)
    consts = reload(consts)
    globals = reload(globals)
else:
    from sublender import template, utils, settings, parser, consts, globals

import pprint
import subprocess
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.batchtools import batchtools
from pysbs import sbsarchive
from pysbs.sbsarchive import SBSARInputGui
from pysbs.sbsarchive import SBSARGuiComboBox
from typing import List
from bpy_extras.io_utils import ImportHelper
from bpy.utils import register_class
from bpy.types import Panel, Operator, Menu
import pathlib
import json
import bpy
import os
from bpy.props import (PointerProperty, StringProperty, BoolProperty, CollectionProperty,
                       EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)

bl_info = {
    "name": "Sublender",
    "author": "xVanTuring(@outlook.com)",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (0, 0, 1),
    "location": "View3D > Properties > Sublender",
    "description": "A addon for sbsar",
    "category": "Material"
}


def sbsar_input_updated():
    pass


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
        name='Assign to Selected',
        default=False
    )
    material_template: EnumProperty(
        items=globals.material_template_enum,
        name='Material Template'
    )

    def execute(self, context):
        material_name = utils.new_material_name(self.material_name)
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
        material.use_fake_user = self.use_fake_user

        m_sublender: settings.Sublender_Material_MT_Setting = material.sublender
        m_sublender.graph_url = self.graph_url
        m_sublender.package_path = self.package_path
        m_sublender.material_template = self.material_template

        bpy.context.scene.sublender_settings.active_graph = self.graph_url
        clss_name, clss = utils.dynamic_gen_clss(
            self.package_path, self.graph_url)
        template.inflate_template(material, self.material_template)
        # generate material and texture
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Import "+self.graph_url, icon="IMPORT")
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
                globals.aContext, self.filepath)
            importing_package.parseDoc()

            sbs_graph_list: List[SBSARGraph] = importing_package.getSBSGraphList(
            )
            globals.sbsar_dict[self.filepath] = importing_package
            for graph in sbs_graph_list:
                bpy.ops.sublender.import_graph(
                    'INVOKE_DEFAULT', package_path=self.filepath, graph_url=graph.mPkgUrl, material_name=graph.mLabel)
        return {'FINISHED'}


class Sublender_Render_TEXTURE(Operator):
    bl_idname = "sublender.render_texture"
    bl_label = "Render Texture"
    bl_description = "Render Texture"

    def execute(self, context):
        # read all params
        mats = bpy.data.materials
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        target_mat = mats.get(sublender_settings.active_instance)
        if target_mat is not None:
            m_sublender: settings.Sublender_Material_MT_Setting = target_mat.sublender
            clss_name, clss_info = utils.dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)
            graph_setting = getattr(target_mat, clss_name)
            input_dict = clss_info['input']
            param_list = []
            param_list.append("--input")
            param_list.append(m_sublender.package_path)
            param_list.append("--input-graph")
            param_list.append(m_sublender.graph_url)
            for group_key in input_dict:
                input_group = input_dict[group_key]
                for input_info in input_group:
                    value = graph_setting.get(input_info['prop'])
                    if value is not None:
                        param_list.append("--set-value")
                        to_list = getattr(value, 'to_list', None)
                        if to_list is not None:
                            value = ','.join(map(str, to_list()))
                        param_list.append("{0}@{1}".format(
                            input_info['mIdentifier'], value))
            param_list.append("--output-path")
            target_dir = os.path.join(
                globals.SUBLENDER_DIR, sublender_settings.uuid, clss_name)
            pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
            param_list.append(target_dir)
            out = batchtools.sbsrender_render(
                *param_list, output_handler=True)
            print(param_list)
        return {'FINISHED'}


class Sublender_New_Instance(Operator):
    bl_idname = "sublender.new_instance"
    bl_label = "New Instance"
    bl_description = "New Instance"

    def execute(self, context):
        return {'FINISHED'}

def load_sbsar():
        mats = bpy.data.materials.items()
        for mat_name, mat in mats:
            m_sublender: settings.Sublender_Material_MT_Setting = mat.sublender
            if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
                utils.dynamic_gen_clss(
                    m_sublender.package_path, m_sublender.graph_url)



current_uuid=""
def init_system():
    global current_uuid
    sublender_settings: settings.SublenderSetting = bpy.context.scene.sublender_settings
    if sublender_settings.uuid == "":
        import uuid
        sublender_settings.uuid = str(uuid.uuid4())
    current_uuid=sublender_settings.uuid
    pathlib.Path(globals.SUBLENDER_DIR).mkdir(parents=True, exist_ok=True)
    print("Current UUID {0}".format(current_uuid))
class Sublender_Init(Operator):
    bl_idname = "sublender.init"
    bl_label = "Init Sublender"
    bl_description = "Init Sublender"
    def execute(self,context):
        init_system()
        load_sbsar()
        return {'FINISHED'}

class Sublender_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES', 'BLENDER_EEVEE'}

    def draw(self, context):
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        if current_uuid == "" or current_uuid != sublender_settings.uuid:
            self.layout.operator("sublender.init")
        else:
            mats = bpy.data.materials
            self.layout.operator("sublender.import_sbsar", icon='IMPORT')
            if sublender_settings.active_instance != "$DUMMY$" or sublender_settings.active_instance != "" :
                target_mat = mats.get(sublender_settings.active_instance)
                if target_mat is not None:
                    self.layout.prop(sublender_settings,
                                    'show_preview', icon='MATERIAL')
                    if sublender_settings.show_preview:
                        self.layout.template_preview(
                            target_mat)
                        self.layout.separator()
                    self.layout.prop(sublender_settings,
                                            'active_graph')
                    self.layout.prop(sublender_settings,
                                        'active_instance')
                    self.layout.prop(target_mat, 'use_fake_user')
                    m_sublender: settings.Sublender_Material_MT_Setting = target_mat.sublender
                    # can't really generate here it's readonly when drawing
                    self.layout.prop(m_sublender,
                                    'material_template', text='Material Template')

                    # self.layout.operator("sublender.new_instance", icon='PRESET_NEW')
                    self.layout.operator("sublender.render_texture", icon='TEXTURE')

                    self.layout.prop(m_sublender, 'show_setting')
                    if m_sublender.show_setting:
                        clss_name, clss_info = utils.dynamic_gen_clss(
                            m_sublender.package_path, m_sublender.graph_url)
                        graph_setting = getattr(target_mat, clss_name)
                        input_dict = clss_info['input']
                        for group_key in input_dict:
                            if group_key != consts.UNGROUPED:
                                self.layout.label(text=group_key)
                            input_group = input_dict[group_key]
                            for input_info in input_group:
                                toggle = -1
                                if input_info['mWidget'] == 'togglebutton':
                                    toggle = 1
                                self.layout.prop(graph_setting,
                                                input_info['prop'], text=input_info['label'], toggle=toggle)


classes = (Sublender_PT_Main, settings.SublenderSetting,
           Sublender_Import_Sbsar, Sublender_Render_TEXTURE, Sublender_New_Instance,
           Sublender_Import_Graph, settings.Sublender_Material_MT_Setting, Sublender_Init)





def register():
    template.load_material_templates()
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.sublender_settings = bpy.props.PointerProperty(
        type=settings.SublenderSetting, name="Sublender")
    bpy.types.Material.sublender = bpy.props.PointerProperty(
        type=settings.Sublender_Material_MT_Setting)



def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    for clss_name in globals.graph_clss:
        clss_info = globals.graph_clss.get(clss_name)
        unregister_class(clss_info['clss'])


# if __name__ == "__main__":
#     # unregister()
#     register()
