from typing import List
import typing
from pysbs.sbsarchive import SBSARGuiComboBox
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.sbsarchive.sbsargraph import SBSARInput, SBSARInputGui
import bpy
from .consts import sbsar_name_to_label, UNGROUPED, sbsar_name_prop


def hash_prop(value: str):
    return "sbp_{0}".format(bpy.path.clean_name(str(hash(value))))


def uid_prop(uid: str):
    return "sbp_{0}".format(bpy.path.clean_name(uid))


class SBInputInfo(object):
    mIdentifier: str
    prop: str
    label: str
    mVisibleIf: typing.Optional[str]


class SBGroupInfo(object):
    mIdentifier: str
    sub_group: typing.List
    inputs: typing.List[SBInputInfo]


def combine_group(parent: str, group: str):
    if parent == "":
        return group
    else:
        return "{0}/{1}".format(parent, group)


def ensure_group(name: str, group_map, group_tree):
    group_path = name.split("/")
    parent_group = ""
    for group in group_path:
        current_group = combine_group(parent_group, group)
        if group_map.get(current_group) is None:
            group_info = {
                'mIdentifier': current_group,
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
    return group_map[name]


def parse_sbsar_group(graph: SBSARGraph):
    group_tree = []
    group_map = {}
    for sb_input in typing.cast(typing.List[SBSARInput], graph.getAllInputs()):
        group_name = sb_input.getGroup()

        if group_name is None:
            group_name = "$UNGROUPED$"
        group_obj = ensure_group(group_name, group_map, group_tree)
        input_info = {
            'mIdentifier': sb_input.mIdentifier,
            'prop': uid_prop(sb_input.mUID),
            'label': sb_input.mIdentifier,
            'mVisibleIf': None
        }
        gui_input: SBSARInputGui = sb_input.getInputGui()
        if gui_input is not None:
            if gui_input.mLabel is not None:
                input_info['label'] = gui_input.mLabel
            if gui_input.mVisibleIf is not None:
                input_info['mVisibleIf'] = gui_input.mVisibleIf
            if gui_input.mWidget == 'togglebutton':
                input_info['togglebutton'] = True
        group_obj['inputs'].append(input_info)
    return group_tree, group_map.keys()


def parse_sbsar_input(graph_inputs: List[SBSARInput]):
    input_list = []
    for sbsar_graph_input in graph_inputs:
        group = sbsar_graph_input.getGroup()
        gui: SBSARInputGui = sbsar_graph_input.getInputGui()
        label = sbsar_name_to_label.get(
            sbsar_graph_input.mIdentifier, sbsar_graph_input.mIdentifier)
        if gui is not None:
            label = gui.mLabel
        if group is None:
            group = UNGROUPED
        input_info = {
            'group': group,
            'mIdentifier': sbsar_graph_input.mIdentifier,
            'mType': sbsar_graph_input.mType,
            'default': sbsar_graph_input.getDefaultValue(),
            'label': label,
            'prop': uid_prop(sbsar_graph_input.mUID)
        }
        if gui is not None:
            if gui.mWidget in ['togglebutton', 'combobox', 'color']:
                input_info['mWidget'] = gui.mWidget
            if gui.mWidget == 'combobox':
                combobox_box: SBSARGuiComboBox = gui.mGuiComboBox
                drop_down_list = combobox_box.getDropDownList()
                if drop_down_list is not None:
                    drop_down_keys = list(drop_down_list.keys())
                    drop_down_keys.sort()
                    enum_items = []
                    for key in drop_down_keys:
                        enum_items.append(
                            (str(key), drop_down_list[key], drop_down_list[key]))
                    input_info['enum_items'] = enum_items
                    input_info['drop_down_list'] = enum_items
                    # assign default value to string here
                    if input_info.get('default') is not None:
                        input_info['default'] = str(input_info['default'])  # drop_down_list[input_info['default']]

        if sbsar_graph_input.getMaxValue() is not None:
            input_info['max'] = sbsar_graph_input.getMaxValue()
        if sbsar_graph_input.getMinValue() is not None:
            input_info['min'] = sbsar_graph_input.getMinValue()
        if sbsar_graph_input.getStep() is not None:
            input_info['step'] = int(sbsar_graph_input.getStep() * 100)
        input_list.append(input_info)
    return input_list
