import os

from pysbs import sbsarchive, context
from pysbs.sbsarchive.sbsarchive import SBSARGraph

aContext = context.Context()
aSbsar = sbsarchive.SBSArchive(
    aContext, os.path.abspath(r"D:\temp\2.sbsar"))
# r"C:\Users\xVan\Documents\Allegorithmic\Substance Designer\AdvancedParameters.sbsar"
aSbsar.parseDoc()
first_graph: SBSARGraph = aSbsar.getSBSGraphList()[0]
for sbs_input in first_graph.getAllInputs():
    print(sbs_input.mType)
# inputs: List[SBSARInput] = first_graph.getAllInputsInGroup("Channels")
# for item in inputs:
#     print(item)
# outputs: List[SBSAROutput] = first_graph.getGraphOutputs()
# for output in outputs:
#     print(output.getUsages()[0].mName)
# prs = sbspreset.SBSPRSPresets(aContext, r"C:\Users\xVan\Documents\Allegorithmic\Substance Player\aaa.sbsprs")
# prs.parseDoc()
# for idx in range(prs.getPresetCount()):
#     pr: sbspreset.SBSPRSPreset = prs.getPresetByIndex(idx)
#     print(pr.getLabel())
