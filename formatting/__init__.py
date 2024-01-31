import bpy

from ..datatypes import OutputInfoData


def sb_output_to_prop(uid: str):
    return "sbo_{0}".format(uid)


def sb_output_format_to_prop(uid: str):
    return "sbo_format_{0}".format(uid)


def sb_output_dep_to_prop(uid: str):
    return "sbo_dep_{0}".format(uid)


def gen_clss_name(graph_url: str):
    return "sb" + graph_url.replace("pkg://", "_")


def sub_panel_name(group_key: str, graph_url: str):
    return "SBS_PT_k{0}".format(str(hash(group_key + graph_url)).replace("-", "_"))


def gen_image_name(material_name: str, output_info: OutputInfoData) -> str:
    """
    Generates an image name by concatenating the material_name with either the first usage in output_info.usages
    or the output_info.name if there are no usages.

    Args:
        material_name (str): The name of the material.
        output_info (OutputInfoData): An object containing information about the output.

    Returns:
        str: The generated image name.
    """
    if output_info.usages:
        return f"{material_name}_{output_info.usages[0]}"
    else:
        return f"{material_name}_{output_info.name}"


def new_material_name(material_name: str) -> str:
    """
    Generate a new material name that does not conflict with existing material names in the Blender scene.

    Args:
        material_name: The desired name for the material.

    Returns:
        The new material name that does not conflict with existing material names.
    """
    existing_names = [mat.name for mat in bpy.data.materials]
    if material_name not in existing_names:
        return material_name

    base_name, suffix = (
        material_name.rsplit(".", 1) if "." in material_name else (material_name, "")
    )
    if suffix == "":
        return f"{material_name}.001"
    try:
        num = int(suffix)
        new_suffix = str(num + 1).zfill(3)
        new_name = f"{base_name}.{new_suffix}"
    except ValueError:
        new_name = f"{material_name}.001"

    return new_name
