import bpy
import pathlib, tempfile, os
from . import texture_render
from . import sublender_library
from ..utils import globalvar


def texture_output_dir(material_name: str):
    if bpy.data.filepath != "":
        current_file = pathlib.Path(bpy.data.filepath)
        parent_dir = current_file.parent
        file_name = bpy.path.clean_name(current_file.name)
        return str(
            parent_dir.joinpath(
                file_name, "mat_{0}".format(bpy.path.clean_name(material_name))
            )
        )
    temp_dir = tempfile.gettempdir()
    return os.path.join(
        temp_dir,
        "sublender",
        globalvar.current_uuid,
        "mat_{0}".format(bpy.path.clean_name(material_name)),
    )


def register():
    texture_render.register()
    sublender_library.register()


def unregister():
    texture_render.unregister()
    sublender_library.unregister()
