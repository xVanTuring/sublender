import bpy
import mathutils

from .. import globalvar, consts
from .. import parser


class VectorWrapper(object):
    def __init__(self, vec):
        self.vec = vec

    @property
    def x(self):
        return self.vec[0]

    @property
    def y(self):
        return self.vec[1]

    @property
    def z(self):
        return self.vec[2]

    @property
    def w(self):
        return self.vec[3]


class EvalDelegate(object):
    material_name = ""
    clss_name = ""

    def __init__(self, material_name, clss_name):
        self.material_name = material_name
        self.clss_name = clss_name

    def __getitem__(self, identifier: str):
        sbs_graph = globalvar.graph_clss.get(self.clss_name, {}).get("sbs_graph")

        graph_setting = getattr(
            bpy.data.materials.get(self.material_name), self.clss_name
        )
        if identifier == "$outputsize":
            if getattr(graph_setting, consts.output_size_lock):
                return VectorWrapper(
                    [
                        int(getattr(graph_setting, consts.output_size_x)),
                        int(getattr(graph_setting, consts.output_size_x)),
                    ]
                )
            else:
                return VectorWrapper(
                    [
                        int(getattr(graph_setting, consts.output_size_x)),
                        int(getattr(graph_setting, consts.output_size_y)),
                    ]
                )
        prop_name = None

        for i in sbs_graph["inputs"]:
            if i["identifier"] == identifier:
                prop_name = parser.uid_prop(i["uid"])
        if prop_name is None:
            return False
        value = getattr(graph_setting, prop_name, None)
        if isinstance(value, mathutils.Color) or isinstance(
            value, bpy.types.bpy_prop_array
        ):
            return VectorWrapper(value)
        if isinstance(value, str) and value.startswith("$NUM:"):
            value = int(value.replace("$NUM:", ""))
        return value
