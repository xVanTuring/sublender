if "bpy" in locals():
    from importlib import reload
    template = reload(template)
    utils = reload(utils)
    settings = reload(settings)
    parser = reload(parser)
    consts = reload(consts)
    globals = reload(globals)
    importer = reload(importer)
    preference = reload(preference)
else:
    from sublender import template, utils, settings, parser, consts, globals, importer, preference
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

# move to importer


class Sublender_Reassign(Operator):
    bl_idname = "sublender.reassign_texture"
    bl_label = "Reassign Texture"
    bl_description = "Reassign Texture"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Reinflate_Material(Operator):
    bl_idname = "sublender.reinflate_material"
    bl_label = "Reinflate Material"
    bl_description = "Reinflate Material"

    def execute(self, context):
        return {'FINISHED'}


def load_sbsar():
    mats = bpy.data.materials.items()
    for mat_name, mat in mats:
        m_sublender: settings.Sublender_Material_MT_Setting = mat.sublender
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            utils.dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)


class Sublender_Select_Active(Operator):
    bl_idname = "sublender.select_active"
    bl_label = "Select Active"
    bl_description = "Select Active"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Init(Operator):
    bl_idname = "sublender.init"
    bl_label = "Init Sublender"
    bl_description = "Init Sublender"

    def execute(self, context):
        preferences = context.preferences
        SUBLENDER_DIR = preferences.addons[__package__].preferences.cache_path
        pathlib.Path(SUBLENDER_DIR).mkdir(parents=True, exist_ok=True)
        print("Default Cache Path: {0}".format(SUBLENDER_DIR))

        sublender_settings: settings.SublenderSetting = bpy.context.scene.sublender_settings
        if sublender_settings.uuid == "":
            import uuid
            sublender_settings.uuid = str(uuid.uuid4())
        # else:
        #     # open file  to check uuid
        #     pass
        globals.current_uuid = sublender_settings.uuid
        print("Current UUID {0}".format(globals.current_uuid))

        load_sbsar()
        bpy.context.scene['sublender_settings']['active_instance_obj'] = 0
        if sublender_settings.active_graph == '':
            print("No graph founded here, reset to DUMMY")
            bpy.context.scene['sublender_settings']['active_graph'] = 0
            bpy.context.scene['sublender_settings']['active_instance'] = 0
        if sublender_settings.active_instance == '':
            print("Selected instance is missing, reset to first one")
            bpy.context.scene['sublender_settings']['active_instance'] = 0
        return {'FINISHED'}


def find_active_mat(context):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    detectd_active = False
    if sublender_settings.follow_selection:
        if bpy.context.view_layer.objects.active is None or len(bpy.context.view_layer.objects.active.material_slots) == 0:
            return None
        mt_index = bpy.context.object.active_material_index
        active_mt = bpy.context.view_layer.objects.active.material_slots[
            mt_index].material
        if active_mt is not None:
            mat_setting: settings.Sublender_Material_MT_Setting = active_mt.sublender
            if mat_setting.package_path != '' and mat_setting.graph_url != '':
                return active_mt
        return None
    mats = bpy.data.materials
    target_mat = mats.get(sublender_settings.active_instance)
    return target_mat


def draw_instance_item(self, context, target_mat):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    if target_mat is not None:
        row = self.layout.row()
        instance_info_column = row.column()
        if sublender_settings.follow_selection:
            # instance_info_column.prop(
            #     sublender_settings, "active_instance_obj", text="Instance")
            instance_info_column.prop(target_mat, "name", text="Instance")
        else:
            instance_info_column.prop(
                sublender_settings, "active_instance", text="Instance")
        row.prop(target_mat, 'use_fake_user',
                 icon_only=True)
        row.operator('sublender.select_active',
                     icon='RESTRICT_SELECT_ON', text='')


def draw_graph_item(self, context, target_mat):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    row = self.layout.row()
    graph_info_column = row.column()
    if sublender_settings.follow_selection:
        graph_info_column.enabled = False
    if sublender_settings.follow_selection and target_mat is not None:
        mat_setting = target_mat.sublender
        graph_info_column.prop(mat_setting,
                               'graph_url', text="Graph")
    else:
        graph_info_column.prop(sublender_settings,
                               'active_graph')

    row.prop(sublender_settings,
             'follow_selection', icon='RESTRICT_SELECT_OFF', icon_only=True)
    row.operator('sublender.import_sbsar',
                 icon='IMPORT', text='')


def draw_workflow_item(self, context, target_mat):
    if target_mat is not None:
        mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
        row = self.layout.row()
        row.prop(mat_setting,
                 'material_template', text='Workflow')
        row.operator(
            "sublender.reinflate_material", icon='MATERIAL', text="")
        row.operator("sublender.new_instance", icon='PRESET_NEW', text="")


def draw_texture_item(self, context, target_mat):
    if target_mat is None:
        return
    row = self.layout.row()
    render_texture = row.operator(
        "sublender.render_texture", icon='TEXTURE')
    render_texture.material_name = target_mat.name
    row.operator(
        "sublender.reassign_texture", icon='FILE_REFRESH',)


def draw_parameters_item(self, context, target_mat):
    if target_mat is None:
        return
    mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
    self.layout.prop(
        mat_setting, 'show_setting', icon="OPTIONS")
    if mat_setting.show_setting:
        clss_name, clss_info = utils.dynamic_gen_clss(
            mat_setting.package_path, mat_setting.graph_url)
        graph_setting = getattr(target_mat, clss_name)
        input_dict = clss_info['input']
        for group_key in input_dict:
            if group_key != consts.UNGROUPED:
                self.layout.label(text=group_key)
            input_group = input_dict[group_key]
            for input_info in input_group:
                if input_info['mIdentifier'] == '$outputsize':
                    row = self.layout.row()
                    row.prop(graph_setting,
                                 'output_size_x', text='Size')
                    row.prop(graph_setting, 'output_size_lock',
                                 toggle=1, icon_only=True, icon="LINKED",)
                    if graph_setting.output_size_lock:
                        row.prop(graph_setting,
                                 'output_size_x', text='')
                    else:
                        row.prop(graph_setting,
                                 'output_size_y', text='')
                else:
                    toggle = -1
                    if input_info['mWidget'] == 'togglebutton':
                        toggle = 1
                    self.layout.prop(graph_setting,
                                     input_info['prop'], text=input_info['label'], toggle=toggle)


class Sublender_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    # bl_space_type = "PROPERTIES"
    # bl_region_type = "WINDOW"
    # bl_context = 'material'
    # bl_options = {'DEFAULT_CLOSED'}

    # add go to texture dir
    # show_more_control: BoolProperty(name="Show More Control")
    # TODO add selected active operator

    def draw(self, context):
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        if globals.current_uuid == "" or globals.current_uuid != sublender_settings.uuid:
            self.layout.operator("sublender.init")
        else:
            if sublender_settings.active_instance != "$DUMMY$":
                target_mat = find_active_mat(context)
                draw_graph_item(self, context, target_mat)
                draw_instance_item(self, context, target_mat)
                draw_workflow_item(self, context, target_mat)
                draw_texture_item(self, context, target_mat)
                draw_parameters_item(self, context, target_mat)
            else:
                self.layout.operator("sublender.import_sbsar", icon='IMPORT')


classes = (Sublender_Select_Active, Sublender_Reassign, Sublender_Reinflate_Material, Sublender_PT_Main, settings.SublenderSetting,
           importer.Sublender_Import_Sbsar, template.Sublender_Render_TEXTURE, Sublender_New_Instance,
           importer.Sublender_Import_Graph, settings.Sublender_Material_MT_Setting, Sublender_Init,
           preference.SublenderPreferences)


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
