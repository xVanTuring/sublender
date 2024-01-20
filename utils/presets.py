from .. import parser, globalvar, formatting
import logging

logger = logging.getLogger(__name__)


def apply_preset(material, preset_name: str):
    material_id = material.sublender.library_uid
    clss_name = formatting.gen_clss_name(material.sublender.graph_url)
    graph_setting = getattr(material, clss_name)
    clss_info = globalvar.graph_clss.get(clss_name)
    prop_input_map = clss_info.prop_input_map
    # Apply preset
    preset = globalvar.library["materials"].get(material_id)["presets"].get(preset_name)
    for p_value in preset["values"]:
        if (
                p_value["identifier"] != "$outputsize"
                and p_value["identifier"] != "$randomseed"
        ):
            parsed_value = p_value["value"]
            if isinstance(parsed_value, str):
                parsed_value = parser.sbsarlite.parse_str_value(
                    parsed_value, p_value["type"]
                )
            if p_value["type"] == parser.sbsarlite.SBSARTypeEnum.INTEGER1:
                input_info = prop_input_map[p_value["prop"]]
                if (
                        input_info.widget == "combobox"
                        and input_info.combo_items is not None
                ):
                    parsed_value = "$NUM:{0}".format(parsed_value)
                if input_info.widget == "togglebutton":
                    parsed_value = bool(parsed_value)
            try:
                setattr(graph_setting, p_value["prop"], parsed_value)
            except ValueError as err:
                logger.error("===============ERROR===============")
                logger.error(err)
                err.with_traceback(None)
                logger.error(
                    "identifier: {}, \nproperty {}, \nvalue {}\n".format(
                        p_value["identifier"], p_value["prop"], parsed_value
                    )
                )
                logger.error("attr: {}".format(type(getattr(graph_setting, p_value["prop"]))))
                logger.error("===================================")
                if type(parsed_value) is list:
                    target_size = (
                        type(graph_setting)
                        .__annotations__["sbp_2593441964"][1]
                        .get("size")
                    )
                    if target_size is not None:
                        if target_size < len(parsed_value):
                            print("Trying to shrink the preset input")
                            setattr(
                                graph_setting,
                                p_value["prop"],
                                parsed_value[:target_size],
                            )
