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


def gen_image_name(material_name, output_info):
    if len(output_info["usages"]) > 0:
        return "{0}_{1}".format(material_name, output_info["usages"][0])
    else:
        graph_identifier = output_info["name"]
        return "{0}_{1}".format(material_name, graph_identifier)
