import typing
from typing import List

import bpy
from .consts import sbsar_name_to_label


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
                'identifier': current_group,
                'sub_group': [],
                "inputs": [],
                "nameInShort": group
            }
            if parent_group == "":
                group_tree.append(
                    group_info
                )
            else:
                group_map.get(parent_group)['sub_group'].append(group_info)
            group_map[current_group] = group_info

        parent_group = current_group
    return group_map[group_name]


def parse_sbsar_group(graph):
    group_tree = []
    group_map = {}
    for sb_input in typing.cast(List[dict], graph['inputs']):
        group_name = None
        if sb_input.get('gui') is not None:
            group_name = sb_input['gui']['group']

        if group_name is None:
            group_name = "$UNGROUPED$"
        group_obj = ensure_group(group_name, group_map, group_tree)
        input_info = {
            'identifier': sb_input['identifier'],
            'prop': sb_input['prop'],
            'label': sbsar_name_to_label.get(
                sb_input['identifier'], sb_input['identifier']),
        }
        if input_info['identifier'] == "$randomseed":
            input_info['prop'] = "$randomseed"
        gui_input = sb_input.get('gui')
        if gui_input is not None:
            if gui_input['label'] is not None:
                input_info['label'] = gui_input['label']
            if gui_input['visibleIf'] is not None:
                input_info['visibleIf'] = gui_input['visibleIf']
            if gui_input['widget'] == 'togglebutton':
                input_info['togglebutton'] = True
        group_obj['inputs'].append(input_info)
    return group_tree, group_map
