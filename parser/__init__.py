from __future__ import annotations

import typing
from dataclasses import dataclass

import bpy

from .sbsarlite import SbsarPackageData, SbsarGraphData

sbsar_name_to_label: typing.Dict[str, str] = {
    "$outputsize": "Output Size",
    "$randomseed": "Random Seed",
}


def hash_prop(value: str):
    return "sbp_{0}".format(bpy.path.clean_name(str(hash(value))))


def uid_prop(uid: str):
    return "sbp_{0}".format(bpy.path.clean_name(uid))


def combine_group(parent: str, group: str):
    if parent == "":
        return group
    else:
        return "{0}/{1}".format(parent, group)


@dataclass
class GroupInfoData:
    identifier: str
    sub_group: typing.List[GroupInfoData]
    inputs: typing.List[GroupInputInfoData]
    nameInShort: str


@dataclass
class GroupInputInfoData:
    identifier: str
    prop: str
    label: str
    visibleIf: str | None = None
    togglebutton: bool | None = None


def ensure_gui_group(
        gui_group_name: str,
        gui_group_map: typing.Dict[str, GroupInfoData],
        group_tree: typing.List[GroupInfoData],
) -> GroupInfoData:
    group_path = gui_group_name.split("/")
    parent_group_id = ""
    for group in group_path:
        current_group = combine_group(parent_group_id, group)
        if gui_group_map.get(current_group) is None:
            group_info = GroupInfoData(
                identifier=current_group,
                sub_group=[],
                inputs=[],
                nameInShort=group,
            )
            if parent_group_id == "":
                group_tree.append(group_info)
            else:
                gui_group_map.get(parent_group_id).sub_group.append(group_info)
            gui_group_map[current_group] = group_info

        parent_group_id = current_group
    return gui_group_map[gui_group_name]


def parse_sbsar_group(
        sbsar_graph: sbsarlite.SbsarGraphData,
) -> typing.Tuple[typing.List[GroupInfoData], typing.Dict[str, GroupInfoData]]:
    group_tree: typing.List[GroupInfoData] = []
    group_map: typing.Dict[str, GroupInfoData] = {}
    for sb_input in sbsar_graph.inputs:
        group_name = sb_input.group
        if group_name is None:
            group_name = "$UNGROUPED$"
        group_obj = ensure_gui_group(group_name, group_map, group_tree)
        input_info = GroupInputInfoData(
            identifier=sb_input.identifier,
            prop=sb_input.prop,
            label=sbsar_name_to_label.get(sb_input.identifier, sb_input.identifier),
        )
        if input_info.identifier == "$randomseed":
            input_info.prop = "$randomseed"
        if sb_input.label is not None:
            input_info.label = sb_input.label
        if sb_input.visibleIf is not None:
            input_info.visibleIf = sb_input.visibleIf
        if sb_input.widget == "togglebutton":
            input_info.togglebutton = True
        group_obj.inputs.append(input_info)
    return group_tree, group_map
