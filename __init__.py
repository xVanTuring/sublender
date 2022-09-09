if "bpy" in locals():
    from importlib import reload
    template = reload(template)
    utils = reload(utils)
    settings = reload(settings)
    parser = reload(parser)
    consts = reload(consts)
    globals = reload(globals)
    importer = reload(importer)
else:
    from sublender import template, utils, settings, parser, consts, globals, importer
import pprint
import subprocess
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.batchtools import batchtools
from pysbs import sbsarchive
from pysbs.sbsarchive import SBSARInputGui
from pysbs.sbsarchive import SBSARGuiComboBox
from typing import List
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


def init_system():
    sublender_settings: settings.SublenderSetting = bpy.context.scene.sublender_settings
    if sublender_settings.uuid == "":
        import uuid
        sublender_settings.uuid = str(uuid.uuid4())
    globals.current_uuid = sublender_settings.uuid
    pathlib.Path(globals.SUBLENDER_DIR).mkdir(parents=True, exist_ok=True)
    print("Current UUID {0}".format(globals.current_uuid))


class Sublender_Init(Operator):
    bl_idname = "sublender.init"
    bl_label = "Init Sublender"
    bl_description = "Init Sublender"

    def execute(self, context):
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
        if globals.current_uuid == "" or globals.current_uuid != sublender_settings.uuid:
            self.layout.operator("sublender.init")
        else:
            mats = bpy.data.materials
            self.layout.operator("sublender.import_sbsar", icon='IMPORT')
            if sublender_settings.active_instance != "$DUMMY$" or sublender_settings.active_instance != "":
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
                    self.layout.operator(
                        "sublender.render_texture", icon='TEXTURE')
                    self.layout.prop(
                        sublender_settings,"live_update", icon='FILE_REFRESH')
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
           importer.Sublender_Import_Sbsar, template.Sublender_Render_TEXTURE, Sublender_New_Instance,
           importer.Sublender_Import_Graph, settings.Sublender_Material_MT_Setting, Sublender_Init)


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
