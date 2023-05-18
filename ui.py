import os

import bpy
from bpy.types import Panel

from . import settings, utils, globalvar, consts, sb_operators


def draw_instance_item(self, context, target_mat):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
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
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
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
    mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
    row = self.layout.row()
    row.prop(mat_setting, 'material_template', text='Workflow')
    row.operator("sublender.apply_workflow", icon='MATERIAL', text="")
    if mat_setting.library_uid in globalvar.library["materials"]:
        operator = row.operator("sublender.save_as_preset", icon='PRESET_NEW', text="")
        operator.material_name = target_mat.name
    if mat_setting.package_missing or not mat_setting.package_loaded:
        row.enabled = False


def draw_texture_item(self, context, target_mat):
    row = self.layout.row()
    render_ops = row.operator("sublender.render_texture_async", icon='TEXTURE')
    render_ops.importing_graph = False
    render_ops.texture_name = ""
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    mat_setting: settings.Sublender_Material_MT_Setting = target_mat.sublender
    row.prop(sublender_settings, 'live_update', icon='FILE_REFRESH', icon_only=True)
    if sublender_settings.live_update:
        row.prop(sublender_settings, 'catch_undo', icon='PROP_CON', icon_only=True)
    if mat_setting.package_missing or not mat_setting.package_loaded:
        row.enabled = False


def draw_install_deps(layout):
    box = layout.box()
    if globalvar.display_restart:
        box.label(text="Installation completed! Please restart blender")
        box.operator("wm.quit_blender")
    else:
        box.label(text="Install Dependencies and restart blender afterwards.")
        box.operator(sb_operators.Sublender_OT_Install_Deps.bl_idname)


class SUBLENDER_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'

    def draw(self, context):
        if not globalvar.py7zr_state:
            draw_install_deps(self.layout)
            return
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        if not utils.inited(context):
            if bpy.data.filepath == "":
                self.layout.operator("wm.save_mainfile")
                self.layout.box().label(text="Please save your file first.")
            operator = self.layout.operator("sublender.init_async")
            operator.pop_import = True
        else:
            if len(globalvar.graph_enum) > 0:
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


def calc_prop_visibility(eval_delegate, input_info: dict):
    if input_info.get('visibleIf') is None:
        return True
    eval_str: str = input_info.get('visibleIf').replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    if eval_delegate is None:
        return False
    eval_result = eval(eval_str, {'input': eval_delegate, 'true': True, 'false': False})
    if eval_result:
        return True
    return False


def calc_group_visibility(eval_delegate, group_info: dict, debug=False):
    for input_info in group_info['inputs']:
        input_visibility = calc_prop_visibility(eval_delegate, input_info)
        if debug:
            print("Calc Prop Visi {0}:{1}".format(input_info.get('visibleIf'), input_visibility))
        if input_visibility:
            return True

    for group_info in group_info['sub_group']:
        if calc_group_visibility(eval_delegate, group_info, debug):
            return True
    return False


class SUBLENDER_PT_Material_Prop_Panel(Panel):
    bl_label = "Material Parameters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not utils.inited(context) or len(globalvar.graph_enum) == 0:
            return False
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        return True

    def draw(self, context):
        active_mat = utils.find_active_mat(context)

        ao_intensity = active_mat.node_tree.nodes.get('AO Intensity')
        if ao_intensity is not None and isinstance(ao_intensity, bpy.types.ShaderNodeMixRGB):
            self.layout.prop(ao_intensity.inputs.get('Fac'), 'default_value', text="AO Intensity")

        normal_node = active_mat.node_tree.nodes.get('Normal Map')
        if normal_node is not None and isinstance(normal_node, bpy.types.ShaderNodeNormalMap):
            self.layout.prop(normal_node.inputs.get('Strength'), 'default_value', text="Normal Strength")
        displacement_node = active_mat.node_tree.nodes.get('Displacement')
        if displacement_node is not None and isinstance(displacement_node, bpy.types.ShaderNodeDisplacement):
            self.layout.prop(displacement_node.inputs.get('Midlevel'), 'default_value', text="Displacement Midlevel")
            self.layout.prop(displacement_node.inputs.get('Scale'), 'default_value', text="Displacement Scale")


class SUBLENDER_PT_SB_Output_Panel(Panel):
    bl_label = "Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not utils.inited(context) or len(globalvar.graph_enum) == 0:
            return False
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        clss_name = utils.gen_clss_name(active_graph)
        if globalvar.graph_clss.get(clss_name) is None:
            # class removed
            return False
        return True

    def draw(self, context):
        active_mat, active_graph = utils.find_active_graph(context)
        clss_name = utils.gen_clss_name(active_graph)
        graph_setting = getattr(active_mat, clss_name)
        open_texture_dir = self.layout.operator("wm.path_open", text="Open Texture Folder", icon="VIEWZOOM")
        material_output_folder = utils.texture_output_dir(active_mat.name)
        open_texture_dir.filepath = material_output_folder
        display_output_params = context.preferences.addons[__package__].preferences.enable_output_params

        for output_info in globalvar.graph_clss.get(clss_name)['output_info']['list']:
            sbo_prop_name = utils.sb_output_to_prop(output_info['name'])
            sbo_format_name = utils.sb_output_format_to_prop(output_info['name'])
            sbo_dep_name = utils.sb_output_dep_to_prop(output_info['name'])
            row = self.layout.row()
            row.prop(graph_setting, sbo_prop_name)
            if display_output_params:
                row.prop(graph_setting, sbo_format_name, text="")
                row.prop(graph_setting, sbo_dep_name, text="")
            bl_img_name = utils.gen_image_name(active_mat.name, output_info)
            bpy_image = bpy.data.images.get(bl_img_name)
            if getattr(graph_setting, sbo_prop_name):
                render_texture = row.operator("sublender.render_texture_async", text="", icon="RENDER_STILL")
                render_texture.texture_name = output_info['name']
                render_texture.importing_graph = False
            if bpy_image is not None:
                if len(output_info['usages']) > 0:
                    apply_image_node_name = output_info['usages'][0]
                else:
                    apply_image_node_name = output_info['name']
                apply_image = row.operator('sublender.apply_image', text='', icon='NODE_TEXTURE')
                apply_image.bl_img_name = bl_img_name
                apply_image.material_name = active_mat.name
                apply_image.node_name = apply_image_node_name

                row.prop(bpy_image, 'use_fake_user', icon_only=True)
                open_image = row.operator("wm.path_open", text="", icon="HIDE_OFF")
                open_image.filepath = bpy.path.abspath(bpy_image.filepath)

                delete_image = row.operator("sublender.delete_image", text="", icon="TRASH")
                delete_image.filepath = bpy.path.abspath(bpy_image.filepath)
                delete_image.bl_img_name = bl_img_name
            else:
                output_format = getattr(graph_setting, utils.sb_output_format_to_prop(output_info['name']), "png")
                image_file_path = os.path.join(material_output_folder,
                                               "{0}.{1}".format(output_info['name'], output_format))
                if globalvar.file_existence_dict.get(image_file_path) is None:
                    globalvar.file_existence_dict[image_file_path] = os.path.exists(image_file_path)
                if globalvar.file_existence_dict.get(image_file_path, False):
                    load_image = row.operator("sublender.load_image", text="", icon="IMPORT")
                    load_image.filepath = image_file_path
                    load_image.bl_img_name = bl_img_name
                    if output_info['usages']:
                        load_image.usage = output_info['usages'][0]

                    open_image = row.operator("wm.path_open", text="", icon="HIDE_OFF")
                    open_image.filepath = image_file_path

                    delete_image = row.operator("sublender.delete_image", text="", icon="TRASH")
                    delete_image.filepath = image_file_path


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
        if not utils.inited(context) or len(globalvar.graph_enum) == 0:
            return False
        preferences = context.preferences.addons[__package__].preferences
        if preferences.hide_channels and cls.bl_label == "Channels":
            return False
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        if active_graph == cls.graph_url and not active_mat.sublender.package_missing:
            if preferences.enable_visible_if:
                clss_name = utils.gen_clss_name(cls.graph_url)
                if globalvar.eval_delegate_map.get(active_mat.name) is None:
                    globalvar.eval_delegate_map[active_mat.name] = utils.EvalDelegate(active_mat.name, clss_name)
                else:
                    # assign again, undo/redo will change the memory address
                    globalvar.eval_delegate_map[active_mat.name].graph_setting = getattr(active_mat, clss_name)
                visible = calc_group_visibility(globalvar.eval_delegate_map.get(active_mat.name), cls.group_info)
                return visible
            return True
        return False

    def draw(self, context):
        layout = self.layout
        target_mat = utils.find_active_mat(context)
        sublender_setting = target_mat.sublender
        clss_name = utils.gen_clss_name(sublender_setting.graph_url)
        graph_setting = getattr(target_mat, clss_name)
        preferences = context.preferences.addons[__package__].preferences
        eval_dele = globalvar.eval_delegate_map.get(target_mat.name)
        for prop_info in self.group_info['inputs']:
            if prop_info.get('identifier') == '$outputsize':
                row = layout.row()
                row.prop(graph_setting, consts.output_size_x, text='Size')
                row.prop(graph_setting, consts.output_size_lock, toggle=1, icon_only=True, icon="LINKED")
                if getattr(graph_setting, consts.output_size_lock):
                    row.prop(graph_setting, consts.output_size_x, text='')
                else:
                    row.prop(graph_setting, consts.output_size_y, text='')
                if context.scene.sublender_settings.live_update:
                    row.prop(graph_setting, consts.update_when_sizing, toggle=1, icon_only=True, icon="UV_SYNC_SELECT")
            elif prop_info.get('identifier') == "$randomseed":
                row = layout.row()
                row.prop(graph_setting, prop_info['prop'], text=prop_info['label'])
                row.operator('sublender.randomseed', icon="LIGHT_DATA", text="")
            else:
                if preferences.enable_visible_if:
                    visible = calc_prop_visibility(eval_dele, prop_info)
                    if not visible:
                        continue
                toggle = -1
                if prop_info.get('togglebutton', False):
                    toggle = 1
                layout.prop(graph_setting, prop_info['prop'], text=prop_info['label'], toggle=toggle)


class SUBLENDER_PT_Library_Panel(Panel):
    bl_label = "Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_order = 1

    @classmethod
    def poll(cls, _):
        return globalvar.py7zr_state

    def draw(self, context):
        self.layout.operator(
            'sublender.select_sbsar_to_library',
            icon='IMPORT',
            text='Import to Library',
        )
        if len(globalvar.library_category_material_map["$ALL$"]) > 0:
            properties = context.scene.sublender_library
            self.layout.prop(properties, "categories", text="")
            if len(globalvar.library_category_material_map.get(properties.categories, [])) == 0:
                self.layout.box().label(text="No material is in this category")
                return
            active_material = properties.active_material
            row = self.layout.row()
            row.template_icon_view(properties, "active_material", show_labels=True)
            has_presets = len(globalvar.library_material_preset_map.get(active_material, [])) > 0
            if has_presets:
                row.template_icon_view(properties, "material_preset", show_labels=True)
            row = self.layout.row()
            import_sbsar_operator = row.operator("sublender.import_sbsar")
            import_sbsar_operator.from_library = True
            row.operator("sublender.remove_material", icon="PANEL_CLOSE")
            active_mat = utils.find_active_mat(context)
            if active_mat is not None:
                material_id = active_mat.sublender.library_uid
                if material_id != '' and material_id == active_material:
                    row = self.layout.row()
                    row.operator("sublender.apply_preset")
                    if has_presets and properties.material_preset != "$DEFAULT$":
                        row.operator("sublender.save_to_preset")


def register():
    bpy.utils.register_class(SUBLENDER_PT_Library_Panel)
    bpy.utils.register_class(SUBLENDER_PT_Main)
    bpy.utils.register_class(SUBLENDER_PT_SB_Output_Panel)
    bpy.utils.register_class(SUBLENDER_PT_Material_Prop_Panel)


def unregister():
    bpy.utils.unregister_class(SUBLENDER_PT_Main)
    bpy.utils.unregister_class(SUBLENDER_PT_SB_Output_Panel)
    bpy.utils.unregister_class(SUBLENDER_PT_Material_Prop_Panel)
    bpy.utils.unregister_class(SUBLENDER_PT_Library_Panel)
