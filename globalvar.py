import pysbs
import typing
import asyncio
import pathlib
import os

instance_map = {
}

sbsar_dict = {}

graph_clss = {}
"""clss_name->{clss,input...}"""

material_templates = {}
material_template_enum = []
# material_output_dict = {}
aContext: typing.Optional[pysbs.context.Context] = None
current_uuid = ""

async_task: typing.Optional[asyncio.Future] = None

HOME = str(pathlib.Path.home())
SUBLENDER_DIR = os.path.join(HOME, ".sublender")

eval_delegate_map = {}
load_status = -1
