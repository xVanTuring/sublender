import subprocess
from pprint import pprint
from typing import List
import pysbs
from pysbs import sbsarchive, context
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.sbsarchive.sbsargraph import SBSARInput
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
from pysbs.sbsarchive import SBSARInputGui
from pysbs.sbsarchive import SBSARGuiComboBox
from pysbs.batchtools import batchtools
import os
out = batchtools.sbsrender_render(
    "--input", "E:/Sublender/sa_aged_wood_planks.sbsar", "--input-graph",
    "pkg://wood_planks_aged", "--output-path", "E:/Sublender/output",
    '--set-value', '$randomseed@14',
    '--set-value', 'roughness_amount@0.9700000286102295',
    stdout=subprocess.PIPE, output_handler=True)
# print("out.output", out.output)
# for graph in out.get_results():
#     print("graph.identifier", graph.identifier)
#     for output in graph.outputs:
#         print("output.identifier", output.identifier, type(output.identifier))
#         print("output.label", output.label, type(output.label))
#         print("output.type", output.type, type(output.type))
#         print("output.uid", output.uid, type(output.uid))
#         print("output.usages", output.usages, type(output.usages))
#         print("output.value", output.value, type(output.value))
# print("rendering Finish")
# print(p.stdout.readlines())
# aContext = context.Context()
# # sa_aged_wood_planks.sbsar
# # wood_cedar_white.sbsar
# aSbsar = sbsarchive.SBSArchive(
#     aContext, os.path.abspath("./wood_cedar_white.sbsar"))
# aSbsar.parseDoc()
# # print(os.path.abspath("./wood_cedar_white.sbsar"))
# graph_list: List[SBSARGraph] = aSbsar.getSBSGraphList()
# graph_first = graph_list[0]
# graph_inputs: List[SBSARInput] = graph_first.getAllInputs()
# UNGROUPPED = '$UNGROUPPED$'
# input_dict = {
# }
# input_dict[UNGROUPPED] = []

# input_list = []
# for sbsa_graph_input in graph_inputs:
#     # group = sbsa_graph_input.getGroup()
#     # if group is None:
#     #     group = UNGROUPPED
#     # if group not in input_dict:
#     #     input_dict[group] = []
#     gui: SBSARInputGui = sbsa_graph_input.getInputGui()
#     if gui is not None:
#         if gui.mLabel == 'Wood Color':
#             print(gui.mLabel)
#             print(gui.mWidget)
#             print(sbsa_graph_input.mType)
#             print(sbsa_graph_input.mDefault)
#     # print(gui.mLabel)
#     #     if gui.mWidget == 'combobox':
#     #         comboxBox: SBSARGuiComboBox = gui.mGuiComboBox
#     #         print(sbsa_graph_input.mDefault)
#     #         print(comboxBox.getDropDownList())
#     # else:
#     #     print(sbsa_graph_input.mIdentifier)
#     # inputObj = {
#     #     'group': group,
#     #     'mIdentifier': sbsa_graph_input.mIdentifier,
#     #     'mType': sbsa_graph_input.mType,
#     #     'mTypeStr': type_dict[sbsa_graph_input.mType],
#     #     'default': sbsa_graph_input.getDefaultValue()
#     # }
#     # if sbsa_graph_input.getMaxValue() is not None:
#     #     inputObj['max'] = sbsa_graph_input.getMaxValue()
#     # if sbsa_graph_input.getMinValue() is not None:
#     #     inputObj['min'] = sbsa_graph_input.getMinValue()
#     # if sbsa_graph_input.getStep() is not None:
#     #     inputObj['step'] = sbsa_graph_input.getStep()
#     # input_list.append(inputObj)
#     # pprint(inputObj, indent=4)
#     # if sbsa_graph_input.mUserTag is not None:
#     #     print(sbsa_graph_input.mUserTag)

# # pprint(input_dict, indent=4)
