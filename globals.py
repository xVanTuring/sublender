import pysbs
import pathlib
import os
instance_map = {
}

sbsar_dict = {}
"""key->{clss,input}"""
graph_clss = {}

material_templates = {}
material_template_enum = []
aContext = pysbs.context.Context()
current_uuid = ""

HOME = str(pathlib.Path.home())
SUBLENDER_DIR = os.path.join(HOME, ".sublender")
