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
    aContext, os.path.abspath(r"C:\Users\xVan\Documents\Allegorithmic\Substance Designer\AdvancedParameters.sbsar"))
aSbsar.parseDoc()
first_graph: SBSARGraph = aSbsar.getSBSGraphList()[0]

prs = sbspreset.SBSPRSPresets(aContext, r"C:\Users\xVan\Documents\Allegorithmic\Substance Player\aaa.sbsprs")
prs.parseDoc()
# print(prs.getPresetCount())
for idx in range(prs.getPresetCount()):
    pr: sbspreset.SBSPRSPreset = prs.getPresetByIndex(idx)
    print(pr.getLabel())
