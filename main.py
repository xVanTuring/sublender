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
aContext = context.Context()
aSbsar = sbsarchive.SBSArchive(
    aContext, os.path.abspath(r"E:\Baidu Net Disk Downloads\Daniel Thiger Source Substance Designer\SubstanceSourceSignature\Signature\desert_sandstone_dark.sbsar"))
aSbsar.parseDoc()
graph_list: List[SBSARGraph] = aSbsar.getSBSGraphList()
graph_first = graph_list[0]
graph_inputs: List[SBSARInput] = graph_first.getAllInputs()
UNGROUPPED = '$UNGROUPPED$'
input_dict = {
}
input_dict[UNGROUPPED] = []

input_list = []
for sbsa_graph_input in graph_inputs:
    group = sbsa_graph_input.getGroup()
    if group is None:
        group = UNGROUPPED
    if group not in input_dict:
        input_dict[group] = []
    gui: SBSARInputGui = sbsa_graph_input.getInputGui()
    if gui is not None:
        if gui.mWidget =="combobox":
            print(sbsa_graph_input.getDefaultValue())
            print(gui.getDropDownList()[sbsa_graph_input.getDefaultValue()])

    # pprint(inputObj, indent=4)
    # if sbsa_graph_input.mUserTag is not None:
    #     print(sbsa_graph_input.mUserTag)

# # pprint(input_dict, indent=4)
