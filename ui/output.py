import os

import bpy
from bpy.types import Panel

from .. import utils, render


class SUBLENDER_PT_SbsarOutput(Panel):
    bl_label = "Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not utils.sublender_inited(context) or len(utils.globalvar.graph_enum) == 0:
            return False
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        clss_name = utils.gen_clss_name(active_graph)
        if utils.globalvar.graph_clss.get(clss_name) is None:
            # class removed
            return False
        return True

    def draw(self, context):
        active_mat, active_graph = utils.find_active_graph(context)
        clss_name = utils.gen_clss_name(active_graph)
        graph_setting = getattr(active_mat, clss_name)
        open_texture_dir = self.layout.operator("wm.path_open", text="Open Texture Folder", icon="VIEWZOOM")
        material_output_folder = render.texture_output_dir(active_mat.name)
        open_texture_dir.filepath = material_output_folder
        display_output_params = context.preferences.addons["sublender"].preferences.enable_output_params

        for output_info in utils.globalvar.graph_clss.get(clss_name)['output_info']['list']:
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
                if utils.globalvar.file_existence_dict.get(image_file_path) is None:
                    utils.globalvar.file_existence_dict[image_file_path] = os.path.exists(image_file_path)
                if utils.globalvar.file_existence_dict.get(image_file_path, False):
                    load_image = row.operator("sublender.load_image", text="", icon="IMPORT")
                    load_image.filepath = image_file_path
                    load_image.bl_img_name = bl_img_name
                    if output_info['usages']:
                        load_image.usage = output_info['usages'][0]

                    open_image = row.operator("wm.path_open", text="", icon="HIDE_OFF")
                    open_image.filepath = image_file_path

                    delete_image = row.operator("sublender.delete_image", text="", icon="TRASH")
                    delete_image.filepath = image_file_path


cls_list = [SUBLENDER_PT_SbsarOutput]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)