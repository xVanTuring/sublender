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
from pysbs.sbspreset import sbspreset
import os
import typing
import pprint

aContext = context.Context()
aSbsar = sbsarchive.SBSArchive(
    aContext, os.path.abspath(r"C:\Program Files\Allegorithmic\Substance Player\data\plastic_stripes.sbsar"))
# r"C:\Users\xVan\Documents\Allegorithmic\Substance Designer\AdvancedParameters.sbsar"
aSbsar.parseDoc()
first_graph: SBSARGraph = aSbsar.getSBSGraphList()[0]
inputs: List[SBSARInput] = first_graph.getAllInputsInGroup("Channels")
for item in inputs:
    print(item)
outputs: List[SBSAROutput] = first_graph.getGraphOutputs()
for output in outputs:
    print(output.getUsages()[0].mName)
# prs = sbspreset.SBSPRSPresets(aContext, r"C:\Users\xVan\Documents\Allegorithmic\Substance Player\aaa.sbsprs")
# prs.parseDoc()
# for idx in range(prs.getPresetCount()):
#     pr: sbspreset.SBSPRSPreset = prs.getPresetByIndex(idx)
#     print(pr.getLabel())
