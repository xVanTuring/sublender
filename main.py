import os

import pysbs
from pysbs import sbsarchive, context
from pysbs.sbsarchive.sbsarchive import SBSARGraph

aContext = context.Context()
aSbsar = sbsarchive.SBSArchive(
    aContext, os.path.abspath(r"D:\temp\2.sbsar"))
# r"C:\Users\xVan\Documents\Allegorithmic\Substance Designer\AdvancedParameters.sbsar"
aSbsar.parseDoc()
first_graph: SBSARGraph = aSbsar.getSBSGraphList()[0]
print(pysbs.__version__)
# for sbs_input in first_graph.getAllInputs():
#     print(sbs_input.mType)
