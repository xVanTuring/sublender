import bpy

from .. import utils, globalvar
from ..parser import GroupInputInfoData, GroupInfoData


def calc_prop_visibility(eval_delegate, input_info: GroupInputInfoData):
    if input_info.visibleIf is None:
        return True
    eval_str: str = (
        input_info.visibleIf
        .replace("&&", " and ")
        .replace("||", " or ")
        .replace("!", " not ")
    )
    if eval_delegate is None:
        return False
    eval_result = eval(eval_str, {"input": eval_delegate, "true": True, "false": False})
    if eval_result:
        return True
    return False


def calc_group_visibility(eval_delegate, group_info: GroupInfoData, debug=False):
    for input_info in group_info.inputs:
        input_visibility = calc_prop_visibility(eval_delegate, input_info)
        if debug:
            print(
                "Calc Prop Visi {0}:{1}".format(
                    input_info.visibleIf, input_visibility
                )
            )
        if input_visibility:
            return True

    for group_info in group_info.sub_group:
        if calc_group_visibility(eval_delegate, group_info, debug):
            return True
    return False


class SUBLENDER_PT_MaterialProp(bpy.types.Panel):
    bl_label = "Material Parameters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sublender"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        if not utils.sublender_inited(context) or len(globalvar.graph_enum) == 0:
            return False
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        return True

    def draw(self, context):
        active_mat = utils.find_active_material(context)

        ao_intensity = active_mat.node_tree.nodes.get("AO Intensity")
        if ao_intensity is not None and isinstance(
                ao_intensity, bpy.types.ShaderNodeMixRGB
        ):
            self.layout.prop(
                ao_intensity.inputs.get("Fac"), "default_value", text="AO Intensity"
            )

        normal_node = active_mat.node_tree.nodes.get("Normal Map")
        if normal_node is not None and isinstance(
                normal_node, bpy.types.ShaderNodeNormalMap
        ):
            self.layout.prop(
                normal_node.inputs.get("Strength"),
                "default_value",
                text="Normal Strength",
            )
        displacement_node = active_mat.node_tree.nodes.get("Displacement")
        if displacement_node is not None and isinstance(
                displacement_node, bpy.types.ShaderNodeDisplacement
        ):
            self.layout.prop(
                displacement_node.inputs.get("Midlevel"),
                "default_value",
                text="Displacement Midlevel",
            )
            self.layout.prop(
                displacement_node.inputs.get("Scale"),
                "default_value",
                text="Displacement Scale",
            )


cls_list = [SUBLENDER_PT_MaterialProp]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
