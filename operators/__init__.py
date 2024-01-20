import bpy

from . import workflow, material, image, sublender_update, startup

mod_list = [workflow, material, image, sublender_update, startup]


def register():
    for mod in mod_list:
        mod.register()


def unregister():
    for mod in mod_list:
        mod.unregister()
