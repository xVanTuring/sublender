import os

import bpy
from bpy.types import Panel

from .. import props, utils


def draw_instance_item(self, context, target_mat):
    sublender_settings = context.scene.sublender_settings
    row = self.layout.row()
    instance_info_column = row.column()
    if sublender_settings.follow_selection:
        instance_info_column.prop(sublender_settings, "object_active_instance", text="Instance")
    else:
        instance_info_column.prop(sublender_settings, "active_instance", text="Instance")
    if target_mat is not None:
        row.prop(target_mat, 'use_fake_user', icon_only=True)
        dup_op = row.operator("sublender.new_instance", icon='DUPLICATE', text="")
        dup_op.target_material = target_mat.name


def draw_graph_item(self, context, target_mat):
    sublender_settings = context.scene.sublender_settings
    row = self.layout.row()
    graph_info_column = row.column()
    if sublender_settings.follow_selection:
        graph_info_column.enabled = False
    if sublender_settings.follow_selection and target_mat is not None:
        mat_setting = target_mat.sublender
        graph_info_column.prop(mat_setting, 'graph_url', text="Graph")
    else:
        graph_info_column.prop(sublender_settings, 'active_graph')

    row.prop(sublender_settings, 'follow_selection', icon='RESTRICT_SELECT_OFF', icon_only=True)
    row.operator('sublender.select_sbsar', icon='IMPORT', text='')


def draw_workflow_item(self, _, target_mat):
    mat_setting = target_mat.sublender
    row = self.layout.row()
    row.prop(mat_setting, 'material_template', text='Workflow')
    row.operator("sublender.apply_workflow", icon='MATERIAL', text="")
    if mat_setting.library_uid in utils.globalvar.library["materials"]:
        operator = row.operator("sublender.save_as_preset", icon='PRESET_NEW', text="")
        operator.material_name = target_mat.name
    if mat_setting.package_missing or not mat_setting.package_loaded:
        row.enabled = False


def draw_texture_item(self, context, target_mat):
    row = self.layout.row()
    render_ops = row.operator("sublender.render_texture_async", icon='TEXTURE')
    render_ops.importing_graph = False
    render_ops.texture_name = ""
    sublender_settings = context.scene.sublender_settings
    mat_setting = target_mat.sublender
    row.prop(sublender_settings, 'live_update', icon='FILE_REFRESH', icon_only=True)
    if sublender_settings.live_update:
        row.prop(sublender_settings, 'catch_undo', icon='PROP_CON', icon_only=True)
    if mat_setting.package_missing or not mat_setting.package_loaded:
        row.enabled = False


def draw_install_deps(layout):
    box = layout.box()
    if utils.globalvar.display_restart:
        box.label(text="Installation completed! Please restart blender")
        box.operator("wm.quit_blender")
    else:
        box.label(text="Install Dependencies and restart blender afterwards.")
        box.operator("sublender.install_deps")


class SUBLENDER_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'

    def draw(self, context):
        if not utils.globalvar.py7zr_state:
            draw_install_deps(self.layout)
            return
        sublender_settings = context.scene.sublender_settings
        if not utils.sublender_inited(context):
            if bpy.data.filepath == "":
                self.layout.operator("wm.save_mainfile")
                self.layout.box().label(text="Please save your file first.")
            operator = self.layout.operator("sublender.init_async")
            operator.pop_import = True
        else:
            if len(utils.globalvar.graph_enum) > 0:
                target_mat = utils.find_active_mat(context)
                draw_graph_item(self, context, target_mat)
                if sublender_settings.follow_selection or target_mat is not None:
                    draw_instance_item(self, context, target_mat)
                if target_mat is not None:
                    draw_workflow_item(self, context, target_mat)
                    draw_texture_item(self, context, target_mat)
                    mat_setting = target_mat.sublender
                    if mat_setting.package_missing:
                        self.layout.label(text="Sbsar file is missing, Please reselect it")
                        self.layout.prop(mat_setting, "package_path")
                    elif not mat_setting.package_loaded:
                        self.layout.label(text="Loading...")
                else:
                    self.layout.label(text="No material is selected")
            else:
                self.layout.operator("sublender.select_sbsar", icon='IMPORT')


cls_list = [SUBLENDER_PT_Main]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)