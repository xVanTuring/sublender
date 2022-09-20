import typing

import bpy
from bpy.types import Panel, Menu

from . import settings, utils, globalvar, consts, parser
from pysbs.sbsarchive.sbsarchive import SBSARGraph
import mathutils


class Sublender_MT_context_menu(Menu):
    bl_label = "Sublender Settings"

    def draw(self, context):
        layout = self.layout
        layout.operator("sublender.copy_texture_path", icon='COPYDOWN')
        layout.operator("sublender.clean_unused_image", icon='BRUSH_DATA')
        layout.operator("sublender.render_all", icon='NODE_TEXTURE')
        # layout.operator(
        #     "sublender.reload_texture", icon='FILE_REFRESH', )
        layout.operator(
            "sublender.change_uuid", icon='FILE', )


def draw_instance_item(self, context, target_mat):
    # TODO follow selection instance list
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    row = self.layout.row()
    instance_info_column = row.column()
    if sublender_settings.follow_selection:
        instance_info_column.prop(target_mat, "name", text="Instance")
    else:
        instance_info_column.prop(
            sublender_settings, "active_instance", text="Instance")
    row.prop(target_mat, 'use_fake_user',
             icon_only=True)
    dup_op = row.operator(
        "sublender.new_instance", icon='DUPLICATE', text="")
    dup_op.target_material = target_mat.name


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
    mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
    row = self.layout.row()
    row.prop(mat_setting,
             'material_template', text='Workflow')
    row.operator(
        "sublender.apply_workflow", icon='MATERIAL', text="")
    if mat_setting.package_missing:
        row.enabled = False


def draw_texture_item(self, context, target_mat):
    row = self.layout.row()
    row.operator(
        "sublender.render_texture_async", icon='TEXTURE')
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
    row.prop(mat_setting,
             'render_policy', text='')
    row.prop(sublender_settings,
             'live_update', icon='FILE_REFRESH', icon_only=True)
    row.menu("Sublender_MT_context_menu", icon="DOWNARROW_HLT", text="")
    if mat_setting.package_missing:
        row.enabled = False


def calc_prop_visibility(input_info: dict):
    if input_info.get('mVisibleIf') is None:
        return True
    eval_str: str = input_info.get('mVisibleIf').replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    eval_result = eval(eval_str, {
        'input': globalvar.eval_delegate,
        'true': True,
        'false': False
    })
    if eval_result:
        return True
    return False


def calc_group_visibility(group_info: dict):
    for input_info in group_info['inputs']:
        input_visibility = calc_prop_visibility(input_info)
        if input_visibility:
            return True

    for group_info in group_info['sub_group']:
        if calc_group_visibility(group_info):
            return True
    return False


# def group_walker(group_tree: typing.List,
#                  layout: bpy.types.UILayout,
#                  graph_setting):
#     for group_info in group_tree:
#         if group_info['mIdentifier'] == consts.UNGROUPED:
#             for input_info in group_info['inputs']:
#                 if input_info.get('mIdentifier') == '$outputsize':
#                     row = layout.row()
#                     row.prop(graph_setting,
#                              consts.output_size_x, text='Size')
#                     row.prop(graph_setting, consts.output_size_lock,
#                              toggle=1, icon_only=True, icon="LINKED", )
#                     if getattr(graph_setting, consts.output_size_lock):
#                         row.prop(graph_setting,
#                                  consts.output_size_x, text='')
#                     else:
#                         row.prop(graph_setting,
#                                  consts.output_size_y, text='')
#                 elif input_info.get('mIdentifier') == "$randomseed":
#                     row = layout.row()
#                     row.prop(graph_setting, input_info['prop'], text=input_info['label'])
#                     row.operator('sublender.randomseed', icon="LIGHT_DATA", text="")
#                 else:
#                     prop_visibility = calc_prop_visibility(input_info)
#                     if not prop_visibility:
#                         continue
#                     layout.prop(graph_setting, input_info['prop'], text=input_info['label'])
#             continue
#         visible_control = calc_group_visibility(group_info)
#         if not visible_control:
#             continue
#
#         group_prop = utils.substance_group_to_toggle_name(group_info['mIdentifier'])
#         row = layout.row()
#         icon = "RIGHTARROW_THIN"
#         display_group = getattr(graph_setting, group_prop)
#         if display_group:
#             icon = "DOWNARROW_HLT"
#         row.prop(graph_setting, group_prop, icon=icon, icon_only=True)
#         row.label(text=group_info['nameInShort'])
#         if display_group:
#             box = layout.box()
#             for input_info in group_info['inputs']:
#                 prop_visibility = calc_prop_visibility(input_info)
#                 if not prop_visibility:
#                     continue
#                 toggle = -1
#                 if input_info.get('togglebutton', False):
#                     toggle = 1
#                 box.prop(graph_setting, input_info['prop'], text=input_info['label'], toggle=toggle)
#
#             group_walker(group_info['sub_group'], box, graph_setting)
#
# def draw_parameters_item(self, context, target_mat):
#     mat_setting = target_mat.sublender
#     if mat_setting.package_missing:
#         self.layout.label(text="Sbsar file is missing, Please reselect it")
#         self.layout.prop(mat_setting, "package_path")
#         return
#     try:
#         clss_name, clss_info = utils.dynamic_gen_clss(
#             mat_setting.package_path, mat_setting.graph_url)
#         self.layout.prop(
#             mat_setting, 'show_setting', icon="OPTIONS")
#         if mat_setting.show_setting:
#             graph_setting = getattr(target_mat, clss_name)
#             group_tree = clss_info['group_tree']
#             # if globalvar.eval_delegate_map.get(clss_name) is None:
#             #     globalvar.eval_delegate_map[clss_name] = EvalDelegate(clss_name, graph_setting, clss_info['graph'])
#             # else:
#             #     globalvar.eval_delegate.graph_setting = graph_setting
#             #     globalvar.eval_delegate.sbs_graph = clss_info['graph']
#             #     globalvar.eval_delegate.identity = clss_name
#
#             group_walker(group_tree, self.layout, graph_setting)
#     except FileNotFoundError as e:
#         mat_setting.package_missing = True
#         print(e)


class Sublender_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'

    # bl_space_type = "PROPERTIES"
    # bl_region_type = "WINDOW"
    # bl_context = 'material'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        if globalvar.current_uuid == "" or globalvar.current_uuid != sublender_settings.uuid:
            self.layout.operator("sublender.init")
        else:
            if sublender_settings.active_instance != "$DUMMY$":
                target_mat = utils.find_active_mat(context)
                draw_graph_item(self, context, target_mat)
                if target_mat is not None:
                    # globalvar.active_material_name = target_mat.name
                    draw_instance_item(self, context, target_mat)
                    draw_workflow_item(self, context, target_mat)
                    draw_texture_item(self, context, target_mat)

                    mat_setting = target_mat.sublender
                    if mat_setting.package_missing:
                        self.layout.label(text="SBSAR Missing")
            else:
                self.layout.operator("sublender.import_sbsar", icon='IMPORT')


def register():
    bpy.utils.register_class(Sublender_PT_Main)
    bpy.utils.register_class(Sublender_MT_context_menu)


def unregister():
    bpy.utils.unregister_class(Sublender_PT_Main)
    bpy.utils.unregister_class(Sublender_MT_context_menu)
