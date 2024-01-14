import bpy
from bpy.props import StringProperty
import os

from .. import utils


class SublenderOTDeleteImage(bpy.types.Operator):
    bl_idname = "sublender.delete_image"
    bl_label = "Delete image"
    bl_description = "Remove target image"
    filepath: StringProperty()
    bl_img_name: StringProperty()

    def execute(self, _):
        if self.bl_img_name != "":
            bl_image = bpy.data.images.get(self.bl_img_name)
            if bl_image is not None:
                bpy.data.images.remove(bl_image)
        os.remove(self.filepath)
        utils.globalvar.file_existence_dict[self.filepath] = False
        return {'FINISHED'}


class SublenderOTLoadImage(bpy.types.Operator):
    bl_idname = "sublender.load_image"
    bl_label = "Load image"
    bl_description = "Load target image"
    filepath: StringProperty()
    bl_img_name: StringProperty()
    usage: StringProperty()

    def execute(self, _):
        bl_img = bpy.data.images.load(self.filepath, check_existing=True)
        bl_img.name = self.bl_img_name
        utils.globalvar.file_existence_dict[self.filepath] = True
        if self.usage != "" and self.usage not in utils.consts.usage_color_dict:
            bl_img.colorspace_settings.name = 'Non-Color'
        return {'FINISHED'}


class SublenderOTApplyImage(bpy.types.Operator):
    bl_idname = "sublender.apply_image"
    bl_label = "Apply image"
    bl_description = "Apply target image into material"
    bl_img_name: StringProperty()
    material_name: StringProperty()
    node_name: StringProperty()

    usage_to_label = {
        'baseColor': 'Base Color',
        'metallic': 'Metallic',
        'roughness': 'Roughness',
        'normal': 'Normal',
        'ambientOcclusion': 'Ambient Occlusion',
        'height': 'Height'
    }

    def execute(self, _):
        target_mat: bpy.types.Material = bpy.data.materials.get(self.material_name)
        if target_mat is not None:
            target_node = target_mat.node_tree.nodes.get(self.node_name)
            if target_node is not None and isinstance(target_node, bpy.types.ShaderNodeTexImage):
                target_node.image = bpy.data.images.get(self.bl_img_name)
            else:
                bl_texture_node = target_mat.node_tree.nodes.new('ShaderNodeTexImage')
                bl_texture_node.name = self.node_name
                bl_texture_node.image = bpy.data.images.get(self.bl_img_name)
                bl_texture_node.label = self.usage_to_label.get(self.node_name, self.node_name)
        return {'FINISHED'}


# class SublenderOTRenderAll(Operator):
#     bl_idname = "sublender.render_all"
#     bl_label = "Render All Texture"
#     bl_description = ""

#     def execute(self, _):
#         return {'FINISHED'}

cls_list = [SublenderOTDeleteImage, SublenderOTLoadImage, SublenderOTApplyImage]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
