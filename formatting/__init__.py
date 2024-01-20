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


def gen_image_name(material_name: str, output_info: OutputInfoData):
    if len(output_info.usages) > 0:
        return "{0}_{1}".format(material_name, output_info.usages[0])
    else:
        graph_identifier = output_info.name
        return "{0}_{1}".format(material_name, graph_identifier)


def new_material_name(material_name: str) -> str:
    """Make Sure No Name Conflict"""
    for mat in bpy.data.materials:
        name: str = mat.name
        if name == material_name:
            try:
                base, suffix = name.rsplit(".", 1)
                num = int(suffix, 10)
                material_name = base + "." + "%03d" % (num + 1)
            except ValueError:
                material_name = material_name + ".001"

    return material_name
