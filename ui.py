import bpy
from bpy.types import Panel, Menu

from . import settings, utils, globalvar, consts


class SUBLENDER_MT_context_menu(Menu):
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
    row.operator('sublender.select_sbsar',
                 icon='IMPORT', text='')


def draw_workflow_item(self, context, target_mat):
    mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
    row = self.layout.row()
    row.prop(mat_setting,
             'material_template', text='Workflow')
    row.operator(
        "sublender.apply_workflow", icon='MATERIAL', text="")
    if mat_setting.package_missing or not mat_setting.package_loaded:
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
                 'catch_undo', icon='PROP_CON', icon_only=True)
    row.menu("SUBLENDER_MT_context_menu", icon="DOWNARROW_HLT", text="")
    if mat_setting.package_missing or not mat_setting.package_loaded:
        row.enabled = False


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
            self.layout.operator("sublender.init_async")
        else:
            if sublender_settings.active_instance != "$DUMMY$":
                target_mat = utils.find_active_mat(context)
                draw_graph_item(self, context, target_mat)
                if target_mat is not None:
                    draw_instance_item(self, context, target_mat)
                    draw_workflow_item(self, context, target_mat)
                    draw_texture_item(self, context, target_mat)

                    mat_setting = target_mat.sublender
                    if mat_setting.package_missing:
                        self.layout.label(text="Sbsar file is missing, Please reselect it")
                        self.layout.prop(mat_setting, "package_path")
                    elif not mat_setting.package_loaded:
                        self.layout.label(text="Loading...")
            else:
                self.layout.operator("sublender.select_sbsar", icon='IMPORT')


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
        if active_graph == cls.graph_url and not active_mat.sublender.package_missing:
            if preferences.enable_visible_if:
                clss_name = utils.gen_clss_name(cls.graph_url)
                if globalvar.eval_delegate_map.get(active_mat.name) is None:
                    globalvar.eval_delegate_map[active_mat.name] = utils.EvalDelegate(
                        active_mat.name,
                        clss_name
                    )
                else:
                    # assign again, undo/redo will change the memory address
                    globalvar.eval_delegate_map[active_mat.name].graph_setting = getattr(active_mat, clss_name)
                visible = calc_group_visibility(
                    globalvar.eval_delegate_map.get(active_mat.name),
                    cls.group_info)
                return visible
            return True
        return False

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
    bpy.utils.register_class(SUBLENDER_MT_context_menu)


def unregister():
    bpy.utils.unregister_class(Sublender_PT_Main)
    bpy.utils.unregister_class(SUBLENDER_MT_context_menu)
