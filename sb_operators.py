from bpy.types import Operator
import bpy
import pathlib
from . import settings, utils, globalvar
from bpy.props import (StringProperty)


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
        return {'FINISHED'}


class Sublender_Reinflate_Material(Operator):
    bl_idname = "sublender.reinflate_material"
    bl_label = "Reinflate Material"
    bl_description = "Reinflate Material"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Select_Active(Operator):
    bl_idname = "sublender.select_active"
    bl_label = "Select Active"
    bl_description = "Select Active"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Copy_Texture_Path(Operator):
    bl_idname = "sublender.copy_texture_path"
    bl_label = "Copy Texture Path"
    bl_description = ""

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Render_All(Operator):
    bl_idname = "sublender.render_all"
    bl_label = "Render All Texture"
    bl_description = ""

    def execute(self, context):
        return {'FINISHED'}


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
        pathlib.Path(sublender_dir).mkdir(parents=True, exist_ok=True)
        print("Default Cache Path: {0}".format(sublender_dir))

        sublender_settings: settings.SublenderSetting = bpy.context.scene.sublender_settings
        if sublender_settings.uuid == "":
            import uuid
            sublender_settings.uuid = str(uuid.uuid4())
        globalvar.current_uuid = sublender_settings.uuid
        print("Current UUID {0}".format(globalvar.current_uuid))

        utils.load_sbsar()
        bpy.context.scene['sublender_settings']['active_instance_obj'] = 0
        bpy.context.scene['sublender_settings']['active_graph'] = 0
        bpy.context.scene['sublender_settings']['active_instance'] = 0
        # if sublender_settings.active_graph == '':
        #     print("No graph founded here, reset to DUMMY")
        # if sublender_settings.active_instance == '':
        #     print("Selected instance is missing, reset to first one")
        #     bpy.context.scene['sublender_settings']['active_instance'] = 0
        return {'FINISHED'}


class Sublender_New_Instance(Operator):
    bl_idname = "sublender.new_instance"
    bl_label = "New Instance"
    bl_description = "New Instance"
    mat_name: StringProperty()

    def execute(self, context):
        target_mat = bpy.data.materials.get(self.mat_name)
        if target_mat is not None:
            target_mat.copy()
        else:
            print("Missing Material with name: {0}".format(self.mat_name))
        return {'FINISHED'}


def register():
    bpy.utils.register_class(Sublender_Reinflate_Material)
    bpy.utils.register_class(Sublender_Reassign)
    bpy.utils.register_class(Sublender_Change_UUID)
    bpy.utils.register_class(Sublender_Select_Active)
    bpy.utils.register_class(Sublender_Copy_Texture_Path)
    bpy.utils.register_class(Sublender_Render_All)
    bpy.utils.register_class(Sublender_Clean_Unused_Image)
    bpy.utils.register_class(Sublender_Init)
    bpy.utils.register_class(Sublender_New_Instance)


def unregister():
    bpy.utils.unregister_class(Sublender_Reassign)
    bpy.utils.unregister_class(Sublender_Change_UUID)
    bpy.utils.unregister_class(Sublender_Select_Active)
    bpy.utils.unregister_class(Sublender_Copy_Texture_Path)
    bpy.utils.unregister_class(Sublender_Render_All)
    bpy.utils.unregister_class(Sublender_Clean_Unused_Image)
    bpy.utils.unregister_class(Sublender_Init)
    bpy.utils.unregister_class(Sublender_New_Instance)
    bpy.utils.unregister_class(Sublender_Reinflate_Material)
