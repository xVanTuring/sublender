import pysbs
import typing
import asyncio

instance_map = {
}

sbsar_dict = {}
"""key->{clss,input}"""
graph_clss = {}

material_templates = {}
material_template_enum = []

aContext: typing.Optional[pysbs.context.Context] = None
current_uuid = ""
task_id = 0
active_material_name: typing.Optional[str] = None


def get_id():
    global task_id
    task_id += 1
    return task_id


async_task: typing.Optional[asyncio.Future] = None
