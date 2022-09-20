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
material_output_dict = {}
aContext: typing.Optional[pysbs.context.Context] = None
current_uuid = ""


# active_material_name: typing.Optional[str] = None

async_task: typing.Optional[asyncio.Future] = None

HOME = str(pathlib.Path.home())
SUBLENDER_DIR = os.path.join(HOME, ".sublender")
# Eval map
# eval_delegate = None
eval_delegate_map = {}
