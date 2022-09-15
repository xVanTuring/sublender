import bpy
from bpy.types import Panel, Menu

from . import settings, utils, globalvar, consts


class Sublender_MT_context_menu(Menu):
    bl_label = "Sublender Settings"

    def draw(self, _context):
        layout = self.layout
        layout.operator("sublender.copy_texture_path", icon='COPYDOWN')
        layout.operator("sublender.clean_unused_image", icon='BRUSH_DATA')
        layout.operator("sublender.render_all", icon='NODE_TEXTURE')
        layout.operator(
            "sublender.reload_texture", icon='FILE_REFRESH', )
        layout.operator(
            "sublender.change_uuid", icon='FILE', )


def find_active_mat(context):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    if sublender_settings.follow_selection:
        if bpy.context.view_layer.objects.active is None or len(
                bpy.context.view_layer.objects.active.material_slots) == 0:
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
        dup_op = row.operator(
            "sublender.new_instance", icon='DUPLICATE', text="")
        dup_op.mat_name = target_mat.name


def draw_texture_item(self, context, target_mat):
    if target_mat is None:
        return
    row = self.layout.row()
    render_texture = row.operator(
        "sublender.render_texture_async", icon='TEXTURE')
    render_texture.material_name = target_mat.name
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    row.prop(sublender_settings,
             'live_update', icon='PLAY', icon_only=True)
    row.menu("Sublender_MT_context_menu", icon="DOWNARROW_HLT", text="")


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
            draw_sub_layout = True
            layout = self.layout
            if group_key != consts.UNGROUPED:
                gp_toggle_name = utils.substance_group_to_toggle_name(group_key)
                self.layout.prop(graph_setting, gp_toggle_name, toggle=1)
                draw_sub_layout = getattr(graph_setting, gp_toggle_name)
                if draw_sub_layout:
                    layout = self.layout.box()
            if draw_sub_layout:
                input_group = input_dict[group_key]
                for input_info in input_group:
                    if input_info['mIdentifier'] == '$outputsize':
                        row = layout.row()
                        row.prop(graph_setting,
                                 'output_size_x', text='Size')
                        row.prop(graph_setting, 'output_size_lock',
                                 toggle=1, icon_only=True, icon="LINKED", )
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
                        layout.prop(graph_setting,
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
        if globalvar.current_uuid == "" or globalvar.current_uuid != sublender_settings.uuid:
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


def register():
    bpy.utils.register_class(Sublender_PT_Main)
    bpy.utils.register_class(Sublender_MT_context_menu)


def unregister():
    bpy.utils.unregister_class(Sublender_PT_Main)
    bpy.utils.unregister_class(Sublender_MT_context_menu)
