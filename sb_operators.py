import random
import os

import bpy
from bpy.props import (StringProperty, BoolProperty)
from bpy.types import Operator

from . import props, utils, template, async_loop, render


class SublenderBaseOperator(object):
    @classmethod
    def poll(cls, context):
        return utils.find_active_mat(context) is not None


class SublenderOTApplyWorkflow(SublenderBaseOperator, Operator):
    bl_idname = "sublender.apply_workflow"
    bl_label = "Apply Workflow"
    bl_description = "Apply Workflow, this will remove all existing nodes"

    def execute(self, context):
        material_inst = utils.find_active_mat(context)
        mat_setting = material_inst.sublender
        workflow_name: str = mat_setting.material_template
        self.report({"INFO"}, "Inflating material {0}".format(material_inst.name))

        material_template = utils.globalvar.material_templates.get(mat_setting.material_template)
        clss_name = utils.gen_clss_name(mat_setting.graph_url)
        clss_info = utils.globalvar.graph_clss.get(clss_name)
        output_info_usage: dict = clss_info['output_info']['usage']
        graph_setting = getattr(material_inst, clss_name)

        setattr(graph_setting, utils.consts.SBS_CONFIGURED, False)
        if workflow_name != utils.consts.CUSTOM:
            for template_texture in material_template['texture']:
                if output_info_usage.get(template_texture) is not None:
                    name = output_info_usage.get(template_texture)[0]
                    setattr(graph_setting, utils.sb_output_to_prop(name), True)
            setattr(graph_setting, utils.consts.SBS_CONFIGURED, True)
            template.inflate_template(material_inst, workflow_name, True)
        else:
            for output_info in clss_info['output_info']['list']:
                setattr(graph_setting, utils.sb_output_to_prop(output_info['name']), True)
        setattr(graph_setting, utils.consts.SBS_CONFIGURED, True)
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name='')
        return {'FINISHED'}


class SublenderOTSelectActive(Operator):
    bl_idname = "sublender.select_active"
    bl_label = "Select Active"
    bl_description = "Select Active"

    def execute(self, _):
        return {'FINISHED'}


class SublenderOTRandomSeed(SublenderBaseOperator, Operator):
    bl_idname = "sublender.randomseed"
    bl_label = "Random Seed"
    bl_description = "Random Seed"

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        m_sublender = material_instance.sublender
        clss_name = utils.gen_clss_name(m_sublender.graph_url)
        pkg_setting = getattr(material_instance, clss_name)
        setattr(pkg_setting, '$randomseed', random.randint(0, 9999999))
        return {'FINISHED'}


class SublenderOTCopyTexturePath(SublenderBaseOperator, Operator):
    bl_idname = "sublender.copy_texture_path"
    bl_label = "Copy Texture Path"
    bl_description = ""

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        output_dir = render.texture_output_dir(material_instance.name)
        bpy.context.window_manager.clipboard = output_dir
        self.report({"INFO"}, "Copied")
        return {'FINISHED'}


class SublenderOTRenderAll(Operator):
    bl_idname = "sublender.render_all"
    bl_label = "Render All Texture"
    bl_description = ""

    def execute(self, _):
        return {'FINISHED'}


class SublenderOTDeleteImage(Operator):
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


class SublenderOTLoadImage(Operator):
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


usage_to_label = {
    'baseColor': 'Base Color',
    'metallic': 'Metallic',
    'roughness': 'Roughness',
    'normal': 'Normal',
    'ambientOcclusion': 'Ambient Occlusion',
    'height': 'Height'
}


class SublenderOTApplyImage(Operator):
    bl_idname = "sublender.apply_image"
    bl_label = "Apply image"
    bl_description = "Apply target image into material"
    bl_img_name: StringProperty()
    material_name: StringProperty()
    node_name: StringProperty()

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
                bl_texture_node.label = usage_to_label.get(self.node_name, self.node_name)

        return {'FINISHED'}


class SublenderOTLoadMissingSbsar(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.load_missing_sbsar"
    bl_label = "Load Sbsar"
    bl_description = "Load Sbsar"
    sbsar_path: StringProperty()
    task_id = "Sublender_Load_Missing_SBSAR"

    async def async_execute(self, _):
        preferences = bpy.context.preferences.addons["sublender"].preferences
        force = True
        for material in bpy.data.materials:
            m_sublender = material.sublender
            if (m_sublender is not None and m_sublender.graph_url != ""
                    and m_sublender.package_path == self.sbsar_path):
                m_sublender.package_loaded = False
            await utils.gen_clss_from_material_async(material, preferences.enable_visible_if, force, self.report)
            m_sublender.package_loaded = True
            # only force load once
            force = False


class SublenderOTInitAsync(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.init_async"
    bl_label = "Init & Import"
    bl_description = "Init Sublender"
    task_id = "Sublender_Init_Async"
    pop_import: BoolProperty(default=False, name="Pop Import")

    @classmethod
    def poll(cls, context):
        return not bpy.data.filepath == ""

    async def async_execute(self, context):
        await utils.init_sublender_async(self, context)
        if self.pop_import:
            bpy.ops.sublender.select_sbsar('INVOKE_DEFAULT')


class SublenderOTNewInstance(SublenderBaseOperator, Operator):
    bl_idname = "sublender.new_instance"
    bl_label = "New Instance"
    bl_description = "New Instance"
    target_material: StringProperty()

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        material_instance.copy()
        return {'FINISHED'}


def ShowMessageBox(message="", title="Message Box", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


class SublenderOTInstallDeps(Operator):
    bl_idname = "sublender.install_deps"
    bl_label = "Install Dependencies"
    bl_description = "Install Dependencies"

    def execute(self, context):
        state = utils.install_lib.ensure_libs()
        utils.refresh_panel(context)
        if state:
            utils.globalvar.display_restart = True
        else:
            ShowMessageBox("Something went wrong! Please contact the developer.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SublenderOTInitAsync)
    bpy.utils.register_class(SublenderOTApplyWorkflow)
    bpy.utils.register_class(SublenderOTSelectActive)
    bpy.utils.register_class(SublenderOTCopyTexturePath)
    bpy.utils.register_class(SublenderOTRenderAll)
    bpy.utils.register_class(SublenderOTDeleteImage)
    bpy.utils.register_class(SublenderOTLoadImage)
    bpy.utils.register_class(SublenderOTLoadMissingSbsar)
    bpy.utils.register_class(SublenderOTNewInstance)
    bpy.utils.register_class(SublenderOTRandomSeed)
    bpy.utils.register_class(SublenderOTApplyImage)
    bpy.utils.register_class(SublenderOTInstallDeps)


def unregister():
    bpy.utils.unregister_class(SublenderOTInitAsync)
    bpy.utils.unregister_class(SublenderOTSelectActive)
    bpy.utils.unregister_class(SublenderOTCopyTexturePath)
    bpy.utils.unregister_class(SublenderOTRenderAll)
    bpy.utils.unregister_class(SublenderOTDeleteImage)
    bpy.utils.unregister_class(SublenderOTLoadImage)
    bpy.utils.unregister_class(SublenderOTLoadMissingSbsar)
    bpy.utils.unregister_class(SublenderOTNewInstance)
    bpy.utils.unregister_class(SublenderOTApplyWorkflow)
    bpy.utils.unregister_class(SublenderOTRandomSeed)
    bpy.utils.unregister_class(SublenderOTApplyImage)
    bpy.utils.unregister_class(SublenderOTInstallDeps)
