import typing

import bpy
from bpy.props import BoolProperty, EnumProperty

from .. import parser, globalvar, consts, ui, preference, props, formatting
from ..datatypes import GraphClassInfoData, GraphClassGroupInfoData, GraphClassOutputInfoData, OutputInfoData


def ensure_graph_property_group(
        sbs_graph: parser.sbsarlite.SbsarGraphData, graph_url: str
) -> typing.Tuple[str, GraphClassInfoData]:
    clss_name = formatting.gen_clss_name(graph_url)
    if globalvar.graph_clss.get(clss_name) is not None:
        return clss_name, globalvar.graph_clss.get(clss_name)

    all_inputs = sbs_graph.inputs
    all_outputs = sbs_graph.outputs
    _anno_obj = {}
    prop_input_map = {}

    def assign(obj_from: object, obj_to: typing.Dict, m_prop_name: str):
        if getattr(obj_from, m_prop_name) is not None:
            obj_to[m_prop_name] = getattr(obj_from, m_prop_name)

    for input_info in all_inputs:
        (prop_type, prop_size) = consts.sbsar_type_to_property[input_info.type]
        _anno_item = {}

        prop_input_map[input_info.prop] = input_info
        if prop_size is not None:
            _anno_item["size"] = prop_size
        assign(input_info, _anno_item, "default")
        assign(input_info, _anno_item, "min")
        assign(input_info, _anno_item, "max")
        assign(input_info, _anno_item, "step")
        if input_info.type == parser.sbsarlite.SBSARTypeEnum.INTEGER1:
            if input_info.widget == "togglebutton":
                prop_type = BoolProperty
            if input_info.widget == "combobox" and input_info.combo_items is not None:
                prop_type = EnumProperty
                _anno_item["items"] = input_info.combo_items
        if input_info.type == parser.sbsarlite.SBSARTypeEnum.IMAGE:
            _anno_item["subtype"] = "FILE_PATH"
        if input_info.type in [
            parser.sbsarlite.SBSARTypeEnum.FLOAT3,
            parser.sbsarlite.SBSARTypeEnum.FLOAT4,
        ]:
            if input_info.widget == "color":
                _anno_item["min"] = 0
                _anno_item["max"] = 1
                _anno_item["subtype"] = "COLOR"

        _anno_item["update"] = sbsar_input_updated_uid(input_info.uid)
        if input_info.identifier == "$outputsize":
            addon_prefs = preference.get_preferences()
            _anno_obj[consts.output_size_x] = EnumProperty(
                items=consts.output_size_one_enum,
                default=addon_prefs.output_size_x,
                update=output_size_x_updated,
            )
            _anno_obj[consts.output_size_y] = EnumProperty(
                items=consts.output_size_one_enum, default=addon_prefs.output_size_x
            )

            _anno_obj[consts.output_size_lock] = BoolProperty(
                default=addon_prefs.output_size_lock, update=output_size_x_updated
            )
            _anno_obj[consts.update_when_sizing] = BoolProperty(
                name="Update texture when change size", default=True
            )
        else:
            _anno_obj[input_info.prop] = prop_type(**_anno_item)

    def parse_output(_output: parser.sbsarlite.SbsarGraphOutputData):
        _anno_obj[formatting.sb_output_to_prop(_output.identifier)] = BoolProperty(
            name=_output.label,
            default=False,
            update=sbsar_output_updated_name(_output.identifier),
        )
        _anno_obj[formatting.sb_output_format_to_prop(_output.identifier)] = EnumProperty(
            name="Format", items=consts.format_list, default="png"
        )
        _anno_obj[formatting.sb_output_dep_to_prop(_output.identifier)] = EnumProperty(
            name="Bit Depth", items=consts.output_bit_depth, default="0"
        )

    output_info = graph_output_parse(all_outputs, parse_output)

    group_tree, group_map = parser.parse_sbsar_group(sbs_graph)
    generate_sub_panel(group_map, graph_url)
    _anno_obj[consts.SBS_CONFIGURED] = BoolProperty(
        name="SBS Configured",
        default=False,
    )
    clss = type(clss_name, (bpy.types.PropertyGroup,), {"__annotations__": _anno_obj})
    bpy.utils.register_class(clss)

    globalvar.graph_clss[clss_name] = GraphClassInfoData(
        clss=clss,
        input=all_inputs,
        prop_input_map=prop_input_map,
        group_info=GraphClassGroupInfoData(tree=group_tree, map=group_map),
        output_info=output_info,
        sbs_graph=sbs_graph,
    )
    setattr(bpy.types.Material, clss_name, bpy.props.PointerProperty(type=clss))

    return clss_name, globalvar.graph_clss.get(clss_name)


def sbsar_input_updated_uid(input_id: str):
    def fn(_, context):
        if (
                props.get_scene_setting(context).live_update
                and not globalvar.applying_preset
        ):
            # TODO pass input id
            bpy.ops.sublender.render_texture_async(
                importing_graph=False, texture_name="", input_id=input_id
            )

    return fn


def sbsar_output_updated_name(sbs_id: str):
    def sbsar_output_updated(self, _):
        prop_name = formatting.sb_output_to_prop(sbs_id)
        if getattr(self, consts.SBS_CONFIGURED) and getattr(self, prop_name):
            bpy.ops.sublender.render_texture_async(
                texture_name=sbs_id, importing_graph=False
            )

    return sbsar_output_updated


def output_size_x_updated(self, context):
    if getattr(self, consts.output_size_lock) and getattr(
            self, consts.output_size_y
    ) != getattr(self, consts.output_size_x):
        setattr(self, consts.output_size_y, getattr(self, consts.output_size_x))
        if getattr(self, consts.update_when_sizing):
            if (
                    props.get_scene_setting(context).live_update
                    and not globalvar.applying_preset
            ):
                bpy.ops.sublender.render_texture_async(
                    importing_graph=False, texture_name=""
                )


def generate_sub_panel(
        group_map: typing.Dict[str, parser.GroupInfoData], graph_url: str
):
    for group_key in group_map.keys():
        cur_group = group_map.get(group_key)
        group_name_map = {"$UNGROUPED$": "Parameters"}
        displace_name = group_name_map.get(cur_group.nameInShort, cur_group.nameInShort)
        parent_name = "/".join(group_key.split("/")[:-1])
        bl_parent_id = ""
        if parent_name != "":
            bl_parent_id = formatting.sub_panel_name(parent_name, graph_url)
        p_clss = type(
            formatting.sub_panel_name(group_key, graph_url),
            (ui.SublenderPTPropBase,),
            {
                "bl_label": displace_name,
                "bl_parent_id": bl_parent_id,
                "graph_url": graph_url,
                "group_info": cur_group,
            },
        )
        bpy.utils.register_class(p_clss)
        globalvar.sub_panel_clss_list.append(p_clss)


def graph_output_parse(
        outputs: list[parser.sbsarlite.SbsarGraphOutputData], exec_per=None
) -> GraphClassOutputInfoData:
    output_list_dict: dict[str, OutputInfoData] = {}
    output_list: typing.List[OutputInfoData] = []
    output_usage_dict: typing.Dict[str, typing.List[str]] = {}
    for output in outputs:
        if exec_per is not None:
            exec_per(output)
        usages = output.usages
        output_graph = OutputInfoData(
            name=output.identifier,
            usages=usages,
            label=output.label,
            uid=output.uid,
        )
        output_list_dict[output.identifier] = output_graph
        output_list.append(output_graph)
        for usage in usages:
            if output_usage_dict.get(usage) is None:
                output_usage_dict[usage] = []
            output_usage_dict[usage].append(output.identifier)
    return GraphClassOutputInfoData(
        list=output_list, dict=output_list_dict, usage=output_usage_dict
    )
