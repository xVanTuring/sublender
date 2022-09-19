from bpy.types import Operator
import bpy
import pathlib
from . import settings, utils, globalvar, consts, template
from bpy.props import (StringProperty)
import uuid
import random


# TODO
class Sublender_Reassign(Operator):
    bl_idname = "sublender.reload_texture"
    bl_label = "Reload Texture"
    bl_description = "Reload Texture"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Change_UUID(Operator):
    bl_idname = "sublender.change_uuid"
    bl_label = "Change UUID"
    bl_description = "Change UUID, useful if you want to duplicate the .blend file"

    def execute(self, context):
        sublender_settings: settings.SublenderSetting = bpy.context.scene.sublender_settings
        sublender_settings.uuid = str(uuid.uuid4())
        globalvar.current_uuid = sublender_settings.uuid
        self.report({'INFO'}, "New UUID {0}".format(sublender_settings.uuid))
        return {'FINISHED'}


class Sublender_Base_Operator(object):

    @classmethod
    def poll(cls, context):
        return utils.find_active_mat(context) is not None


class Sublender_Inflate_Material(Sublender_Base_Operator, Operator):
    bl_idname = "sublender.apply_workflow"
    bl_label = "Apply Workflow"
    bl_description = "Apply Workflow, this will remove all existing nodes"

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        print("Inflate material {0}".format(material_instance.name))
        mat_setting: settings.Sublender_Material_MT_Setting = material_instance.sublender

        workflow_name: str = mat_setting.material_template
        if workflow_name != consts.CUSTOM:
            template.inflate_template(material_instance, workflow_name, True)
            # resource_dict = globalvar.material_output_dict.get(material_instance.name)
            # if resource_dict is not None:
            #     workflow = globalvar.material_templates.get(workflow_name)
            #     template.ensure_assets(context, material_instance, workflow, resource_dict)
            # else:
            # TODO check rendered workflow
            bpy.ops.sublender.render_texture_async()
        return {'FINISHED'}


class Sublender_Select_Active(Operator):
    bl_idname = "sublender.select_active"
    bl_label = "Select Active"
    bl_description = "Select Active"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Random_Seed(Sublender_Base_Operator, Operator):
    bl_idname = "sublender.randomseed"
    bl_label = "Random Seed"
    bl_description = "Random Seed"

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        m_sublender: settings.Sublender_Material_MT_Setting = material_instance.sublender
        clss_name = utils.gen_clss_name(m_sublender.graph_url)
        pkg_setting = getattr(material_instance, clss_name)
        setattr(pkg_setting, '$randomseed', random.randint(0, 9999999))
        return {'FINISHED'}


class Sublender_Copy_Texture_Path(Sublender_Base_Operator, Operator):
    bl_idname = "sublender.copy_texture_path"
    bl_label = "Copy Texture Path"
    bl_description = ""

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        m_sublender: settings.Sublender_Material_MT_Setting = material_instance.sublender
        output_dir = utils.texture_output_dir(utils.gen_clss_name(m_sublender.graph_url), material_instance.name)
        bpy.context.window_manager.clipboard = output_dir
        self.report({"INFO"}, "Copied")
        return {'FINISHED'}


class Sublender_Render_All(Operator):
    bl_idname = "sublender.render_all"
    bl_label = "Render All Texture"
    bl_description = ""

    def execute(self, context):
        return {'FINISHED'}


# Pro Feature
class Sublender_Clean_Unused_Image(Operator):
    bl_idname = "sublender.clean_unused_image"
    bl_label = "Clean Unused Texture"
    bl_description = "Remove Unused Image in this Blender Project"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Init(Operator):
    bl_idname = "sublender.init"
    bl_label = "Init Sublender"
    bl_description = "Init Sublender"

    def execute(self, context):
        print("Sublender Init")
        import pysbs
        globalvar.aContext = pysbs.context.Context()
        preferences = context.preferences.addons[__package__].preferences
        sublender_dir = preferences.cache_path
        globalvar.SUBLENDER_DIR = sublender_dir
        pathlib.Path(globalvar.SUBLENDER_DIR).mkdir(parents=True, exist_ok=True)
        print("Default Cache Path: {0}".format(globalvar.SUBLENDER_DIR))

        sublender_settings: settings.SublenderSetting = bpy.context.scene.sublender_settings
        if sublender_settings.uuid == "":
            sublender_settings.uuid = str(uuid.uuid4())
        globalvar.current_uuid = sublender_settings.uuid
        print("Current UUID {0}".format(globalvar.current_uuid))

        utils.load_sbsar()
        if sublender_settings.active_graph == '':
            print(
                "No graph with given index {0} founded here, reset to 0".format(sublender_settings['active_graph']))
            bpy.context.scene['sublender_settings']['active_graph'] = 0
            bpy.context.scene['sublender_settings']['active_instance'] = 0
        if sublender_settings.active_instance == '':
            print("Selected instance is missing, reset to 0")
            bpy.context.scene['sublender_settings']['active_instance'] = 0
        return {'FINISHED'}


class Sublender_New_Instance(Sublender_Base_Operator, Operator):
    bl_idname = "sublender.new_instance"
    bl_label = "New Instance"
    bl_description = "New Instance"
    target_material: StringProperty()

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        material_instance.copy()
        return {'FINISHED'}


class Sublender_Reload_Texture(Operator):
    bl_idname = "sublender.reload_texture"
    bl_label = "Clean reload_texture"
    image_name: StringProperty()

    def execute(self, context):
        print("Sublender_Reload_Texture")
        texture_img: bpy.types.Image = bpy.data.images.get(self.image_name)
        texture_img.reload()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(Sublender_Inflate_Material)
    bpy.utils.register_class(Sublender_Reassign)
    bpy.utils.register_class(Sublender_Change_UUID)
    bpy.utils.register_class(Sublender_Select_Active)
    bpy.utils.register_class(Sublender_Copy_Texture_Path)
    bpy.utils.register_class(Sublender_Render_All)
    bpy.utils.register_class(Sublender_Clean_Unused_Image)
    bpy.utils.register_class(Sublender_Init)
    bpy.utils.register_class(Sublender_New_Instance)
    bpy.utils.register_class(Sublender_Reload_Texture)
    bpy.utils.register_class(Sublender_Random_Seed)


def unregister():
    bpy.utils.unregister_class(Sublender_Reassign)
    bpy.utils.unregister_class(Sublender_Change_UUID)
    bpy.utils.unregister_class(Sublender_Select_Active)
    bpy.utils.unregister_class(Sublender_Copy_Texture_Path)
    bpy.utils.unregister_class(Sublender_Render_All)
    bpy.utils.unregister_class(Sublender_Clean_Unused_Image)
    bpy.utils.unregister_class(Sublender_Init)
    bpy.utils.unregister_class(Sublender_New_Instance)
    bpy.utils.unregister_class(Sublender_Inflate_Material)
    bpy.utils.unregister_class(Sublender_Reload_Texture)
    bpy.utils.unregister_class(Sublender_Random_Seed)
