import bpy
from bpy.props import StringProperty
import random

from .base import SublenderBaseOperator
from .. import utils, render, async_loop


class SublenderOTRandomSeed(SublenderBaseOperator, bpy.types.Operator):
    bl_idname = "sublender.randomseed"
    bl_label = "Random Seed"
    bl_description = "Random Seed"

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        m_sublender = material_instance.sublender
        clss_name = utils.format.gen_clss_name(m_sublender.graph_url)
        pkg_setting = getattr(material_instance, clss_name)
        setattr(pkg_setting, "$randomseed", random.randint(0, 9999999))
        return {"FINISHED"}


class SublenderOTCopyTexturePath(SublenderBaseOperator, bpy.types.Operator):
    bl_idname = "sublender.copy_texture_path"
    bl_label = "Copy Texture Path"
    bl_description = ""

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        output_dir = render.texture_output_dir(material_instance.name)
        bpy.context.window_manager.clipboard = output_dir
        self.report({"INFO"}, "Copied")
        return {"FINISHED"}


class SublenderOTLoadMissingSbsar(
    async_loop.AsyncModalOperatorMixin, bpy.types.Operator
):
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
            if (
                m_sublender is not None
                and m_sublender.graph_url != ""
                and m_sublender.package_path == self.sbsar_path
            ):
                m_sublender.package_loaded = False
            await utils.gen_clss_from_material_async(
                material, preferences.enable_visible_if, force, self.report
            )
            m_sublender.package_loaded = True
            # only force load once
            force = False


class SublenderOTNewInstance(SublenderBaseOperator, bpy.types.Operator):
    bl_idname = "sublender.new_instance"
    bl_label = "New Instance"
    bl_description = "New Instance"
    target_material: StringProperty()

    def execute(self, context):
        material_instance = utils.find_active_mat(context)
        material_instance.copy()
        return {"FINISHED"}


# class SublenderOTSelectActive(Operator):
#     bl_idname = "sublender.select_active"
#     bl_label = "Select Active"
#     bl_description = "Select Active"

#     def execute(self, _):
#         return {'FINISHED'}
cls_list = [
    SublenderOTRandomSeed,
    SublenderOTCopyTexturePath,
    SublenderOTLoadMissingSbsar,
    SublenderOTNewInstance,
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
