from . import sbsarlite

import bpy

sbsar_name_to_label = {"$outputsize": "Output Size", "$randomseed": "Random Seed"}


def hash_prop(value: str):
    return "sbp_{0}".format(bpy.path.clean_name(str(hash(value))))


def uid_prop(uid: str):
    return "sbp_{0}".format(bpy.path.clean_name(uid))


def combine_group(parent: str, group: str):
    if parent == "":
        return group
    else:
        return "{0}/{1}".format(parent, group)


def ensure_group(group_name: str, group_map, group_tree):
    group_path = group_name.split("/")
    parent_group = ""
    for group in group_path:
        current_group = combine_group(parent_group, group)
        if group_map.get(current_group) is None:
            group_info = {
                "identifier": current_group,
                "sub_group": [],
                "inputs": [],
                "nameInShort": group,
            }
            if parent_group == "":
                group_tree.append(group_info)
            else:
                group_map.get(parent_group)["sub_group"].append(group_info)
            group_map[current_group] = group_info

        parent_group = current_group
    return group_map[group_name]


def parse_sbsar_group(graph):
    group_tree = []
    group_map = {}
    for sb_input in graph["inputs"]:
        group_name = sb_input.get("group")
        if group_name is None:
            group_name = "$UNGROUPED$"
        group_obj = ensure_group(group_name, group_map, group_tree)
        input_info = {
            "identifier": sb_input["identifier"],
            "prop": sb_input["prop"],
            "label": sbsar_name_to_label.get(
                sb_input["identifier"], sb_input["identifier"]
            ),
        }
        if input_info["identifier"] == "$randomseed":
            input_info["prop"] = "$randomseed"
        if sb_input.get("label") is not None:
            input_info["label"] = sb_input["label"]
        if sb_input.get("visibleIf") is not None:
            input_info["visibleIf"] = sb_input["visibleIf"]
        if sb_input.get("widget") == "togglebutton":
            input_info["togglebutton"] = True
        group_obj["inputs"].append(input_info)
    return group_tree, group_map
