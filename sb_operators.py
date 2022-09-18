from bpy.types import Operator
import bpy
import pathlib
from . import settings, utils, globalvar, consts, template
from bpy.props import (StringProperty)
import uuid


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


class Sublender_Inflate_Material(Operator):
    bl_idname = "sublender.inflate_material"
    bl_label = "Inflate Material"
    bl_description = "Inflate Material, this will remove all existing nodes"
    target_material: StringProperty()

    def execute(self, context):
        print("Inflate material {0}".format(self.target_material))
        material_instance = bpy.data.materials.get(self.target_material)
        mat_setting: settings.Sublender_Material_MT_Setting = material_instance.sublender
        workflow_name: str = mat_setting.material_template
        # FIX Texture Missing
        if workflow_name != consts.CUSTOM:
            template.inflate_template(material_instance, workflow_name, True)
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
    target_material: StringProperty()

    def execute(self, context):
        material_inst = bpy.data.materials.get(self.target_material)
        if material_inst is not None:
            m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
            output_dir = utils.texture_output_dir(utils.gen_clss_name(m_sublender.graph_url), self.target_material)
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
        bpy.context.scene['sublender_settings']['active_instance_obj'] = 0
        bpy.context.scene['sublender_settings']['active_graph'] = 0
        bpy.context.scene['sublender_settings']['active_instance'] = 0
        # TODO better state saving
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
    target_material: StringProperty()

    def execute(self, context):
        material_instance = bpy.data.materials.get(self.target_material)
        if material_instance is not None:
            material_instance.copy()
        else:
            print("Missing Material with name: {0}".format(self.mat_name))
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


# class ModalTimerOperator(bpy.types.Operator):
#     """Operator which runs its self from a timer"""
#     bl_idname = "sublender.watch_material"
#     bl_label = "Modal Timer Operator"
#     _timer = None
#
#     def modal(self, context, event):
#         if event.type in {'RIGHTMOUSE', 'ESC'}:
#             self.cancel(context)
#             return {'CANCELLED'}
#         if globalvar.reload_texture_status == -1:
#             self.cancel(context)
#             return {'CANCELLED'}
#
#         if event.type == 'TIMER':
#             if globalvar.reload_texture_status == 1:
#                 material_inst: bpy.types.Material = bpy.data.materials.get(globalvar.active_material_name)
#                 m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
#                 m_template = globalvar.material_templates.get(
#                     m_sublender.material_template)
#                 template.ensure_assets(material_inst, m_template,
#                                        globalvar.material_output_dict.get(material_inst.name))
#                 globalvar.reload_texture_status = 0
#                 print("Updating texture for {0}".format(globalvar.active_material_name))
#             else:
#                 print("Empty Loop")
#         return {'PASS_THROUGH'}
#
#     def execute(self, context):
#         wm = context.window_manager
#         self._timer = wm.event_timer_add(0.1, window=context.window)
#         wm.modal_handler_add(self)
#         return {'RUNNING_MODAL'}
#
#     def cancel(self, context):
#         wm = context.window_manager
#         wm.event_timer_remove(self._timer)


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
    # bpy.utils.register_class(ModalTimerOperator)


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
    # bpy.utils.unregister_class(ModalTimerOperator)
