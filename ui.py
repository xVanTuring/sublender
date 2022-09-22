import typing

import bpy
from bpy.types import Panel, Menu

from . import settings, utils, globalvar, consts, parser


class Sublender_MT_context_menu(Menu):
    bl_label = "Sublender Settings"

    def draw(self, context):
        layout = self.layout
        layout.operator("sublender.copy_texture_path", icon='COPYDOWN')
        # layout.operator("sublender.clean_unused_image", icon='BRUSH_DATA')
        # layout.operator("sublender.render_all", icon='NODE_TEXTURE')
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
    if sublender_settings.live_update:
        row.prop(sublender_settings,
                 'catch_undo', icon='FILE_REFRESH', icon_only=True)
    row.menu("Sublender_MT_context_menu", icon="DOWNARROW_HLT", text="")
    if mat_setting.package_missing:
        row.enabled = False


# def calc_prop_visibility(input_info: dict):
#     if input_info.get('mVisibleIf') is None:
#         return True
#     eval_str: str = input_info.get('mVisibleIf').replace("&&", " and ").replace("||", " or ").replace("!", " not ")
#     eval_result = eval(eval_str, {
#         'input': globalvar.eval_delegate,
#         'true': True,
#         'false': False
#     })
#     if eval_result:
#         return True
#     return False
#
#
# def calc_group_visibility(group_info: dict, debug=False):
#     for input_info in group_info['inputs']:
#         input_visibility = calc_prop_visibility(input_info)
#         if debug:
#             print("Calc Prop Visi :{0}".format(input_visibility))
#         if input_visibility:
#             return True
#
#     for group_info in group_info['sub_group']:
#         if calc_group_visibility(group_info, debug):
#             return True
#     return False


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


def calc_prop_visibility(eval_delegate, input_info: dict):
    if input_info.get('mVisibleIf') is None:
        return True
    eval_str: str = input_info.get('mVisibleIf').replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    if eval_delegate is None:
        return False
    eval_result = eval(eval_str, {
        'input': eval_delegate,
        'true': True,
        'false': False
    })
    if eval_result:
        return True
    return False


def calc_group_visibility(eval_delegate, group_info: dict, debug=False):
    for input_info in group_info['inputs']:
        input_visibility = calc_prop_visibility(eval_delegate, input_info)
        if debug:
            print("Calc Prop Visi {0}:{1}".format(input_info.get('mVisibleIf'), input_visibility))
        if input_visibility:
            return True

    for group_info in group_info['sub_group']:
        if calc_group_visibility(eval_delegate, group_info, debug):
            return True
    return False


class Sublender_Prop_BasePanel(Panel):
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_options = {'DEFAULT_CLOSED'}
    graph_url = ""
    group_info = None

    @classmethod
    def poll(cls, context):
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        preferences = bpy.context.preferences.addons[__package__].preferences
        if preferences.enable_visible_if:
            clss_name = utils.gen_clss_name(cls.graph_url)
            if globalvar.eval_delegate_map.get(active_mat.name) is None:
                globalvar.eval_delegate_map[active_mat.name] = utils.EvalDelegate(
                    globalvar.graph_clss.get(clss_name)['sbs_graph'],
                    getattr(active_mat, clss_name)
                )
            else:
                # assign again, undo/redo will change the memory address
                globalvar.eval_delegate_map[active_mat.name].graph_setting = getattr(active_mat, clss_name)
        visible = active_graph == cls.graph_url and not active_mat.sublender.package_missing and (
                not preferences.enable_visible_if or
                calc_group_visibility(
                    globalvar.eval_delegate_map.get(active_mat.name),
                    cls.group_info))
        return visible

    def draw(self, context):
        layout = self.layout
        target_mat = utils.find_active_mat(context)
        sublender_setting = target_mat.sublender
        clss_name = utils.gen_clss_name(sublender_setting.graph_url)
        graph_setting = getattr(target_mat, clss_name)
        for prop_info in self.group_info['inputs']:
            if prop_info.get('mIdentifier') == '$outputsize':
                row = layout.row()
                row.prop(graph_setting,
                         consts.output_size_x, text='Size')
                row.prop(graph_setting, consts.output_size_lock,
                         toggle=1, icon_only=True, icon="LINKED", )
                if getattr(graph_setting, consts.output_size_lock):
                    row.prop(graph_setting,
                             consts.output_size_x, text='')
                else:
                    row.prop(graph_setting,
                             consts.output_size_y, text='')
            elif prop_info.get('mIdentifier') == "$randomseed":
                row = layout.row()
                row.prop(graph_setting, prop_info['prop'], text=prop_info['label'])
                row.operator('sublender.randomseed', icon="LIGHT_DATA", text="")
            else:
                toggle = -1
                if prop_info.get('togglebutton', False):
                    toggle = 1
                layout.prop(graph_setting, prop_info['prop'], text=prop_info['label'], toggle=toggle)


def register():
    bpy.utils.register_class(Sublender_PT_Main)
    bpy.utils.register_class(Sublender_MT_context_menu)


def unregister():
    bpy.utils.unregister_class(Sublender_PT_Main)
    bpy.utils.unregister_class(Sublender_MT_context_menu)
