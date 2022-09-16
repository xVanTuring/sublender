import subprocess
from pprint import pprint
from typing import List
import pysbs
from pysbs import sbsarchive, context
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.sbsarchive.sbsargraph import SBSARInput, SBSAROutput, SBSARGuiGroup
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
from pysbs.sbsarchive import SBSARInputGui
from pysbs.sbsarchive import SBSARGuiComboBox
from pysbs.batchtools import batchtools
import os
import typing
import pprint

aContext = context.Context()
aSbsar = sbsarchive.SBSArchive(
    aContext, os.path.abspath(r"C:\Program Files\Allegorithmic\Substance Player\data\rock_cliff_stylized_mossy.sbsar"))
aSbsar.parseDoc()
first_graph: SBSARGraph = aSbsar.getSBSGraphList()[0]


class SBInputInfo(typing.TypedDict):
    mIdentifier: str


class SBGroupInfo(typing.TypedDict):
    mIdentifier: str
    sub_group: typing.List
    inputs: typing.List[SBInputInfo]


group_tree: typing.List[SBInputInfo] = []
group_map: typing.Dict[str, SBGroupInfo] = {

}


def combine_group(parent: str, group: str):
    if parent == "":
        return group
    else:
        return "{0}/{1}".format(parent, group)


def ensure_group(name: str, group_map: typing.Dict[str, SBGroupInfo]):
    group_path = name.split("/")
    parent_group = ""
    for group in group_path:
        current_group = combine_group(parent_group, group)
        if group_map.get(current_group) is None:
            group_info = {
                'mIdentifier': current_group,
                'sub_group': [],
                "inputs": []
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


all_gp = first_graph.getAllInputGroups()
print("Advanced parameters/Moss/Mask" in all_gp)
for sb_input in typing.cast(typing.List[SBSARInput], first_graph.getAllInputs()):
    group_name = sb_input.getGroup()

    if group_name is None:
        group_name = "$UNGROUPED$"
    group_obj = ensure_group(group_name)
    group_obj['inputs'].append({
        'mIdentifier': sb_input.mIdentifier
    })

# def walk_tree(tree: List):
#     for group in tree:
#         print(group['mIdentifier'])
#         for sb_input in group['inputs']:
#             print('\t{0}'.format(sb_input['mIdentifier']))
#         walk_tree(group['sub_group'])
#
#
# walk_tree(group_tree)
# print(len(group_map.keys()))
#
#
# print(graph_first.getAllInputs()[50].mIdentifier)
# for group in typing.cast(typing.List[str], graph_first.getAllInputGroups()):
#     # print(group)
#     group_path = group.split('/')
#     current_group = group_tree
#     current_obj = None
#     for group_name in group_path:
#         if current_group.get(group_name) is None:
#             group_obj = {
#                 'inputs': [],
#                 'sub_group': {},
#                 'raw_group_name': group
#             }
#             current_group[group_name] = group_obj
#             current_obj = group_obj
#         current_group = current_group.get(group_name)['sub_group']
#
#     group_obj = current_obj
#     for sb_input in typing.cast(typing.List[SBSARInput], graph_first.getAllInputsInGroup(group)):
#         input_info = {
#             'mIdentifier': sb_input.mIdentifier,
#             'prop': sb_input.mIdentifier
#         }
#         gui_input: SBSARInputGui = sb_input.getInputGui()
#         if gui_input is not None:
#             if gui_input.mVisibleIf is not None:
#                 input_info['mVisibleIf'] = gui_input.mVisibleIf
#
#         group_obj['inputs'].append(input_info)

# print(group_tree)

# count = 0
#
#
# def walk_group_tree(tree: dict):
#     global count
#     for key in tree:
#         ct_group = tree[key]
#         for input_info in ct_group['inputs']:
#             # count += 1
#             print(input_info['mIdentifier'])
#         if ct_group.get('sub_group') is not None:
#             walk_group_tree(ct_group.get('sub_group'))
#
#
# print(len(graph_first.getAllInputs()))
# walk_group_tree(group_tree)
# print(count)
# print(len(graph_first.getAllInputsInGroup(None)))
# import json
#
# print(json.dumps(group_tree, indent=4))
# #
# for input in graph_first.getAllInputs():
#     input_gui: SBSARInputGui = input.getInputGui()
#     if input_gui is not None:
#         print(input_gui.mVisibleIf)
