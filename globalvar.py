import pysbs
import typing

instance_map = {
}

sbsar_dict = {}
"""key->{clss,input}"""
graph_clss = {}

material_templates = {}
material_template_enum = []

aContext: typing.Optional[pysbs.context.Context] = None
current_uuid = ""
