from typing import List

from pysbs.sbsarchive import SBSARGuiComboBox
from pysbs.sbsarchive.sbsargraph import SBSARInput, SBSARInputGui

from .consts import sbsar_name_to_label, UNGROUPED, sbsar_name_prop


def parse_sbsar_input(graph_inputs: List[SBSARInput]):
    input_list = []
    for sbsar_graph_input in graph_inputs:
        group = sbsar_graph_input.getGroup()
        gui: SBSARInputGui = sbsar_graph_input.getInputGui()
        label = sbsar_name_to_label.get(
            sbsar_graph_input.mIdentifier, sbsar_graph_input.mIdentifier)
        if gui is not None:
            label = gui.mLabel
        if group is None:
            group = UNGROUPED
        input_info = {
            'group': group,
            'mIdentifier': sbsar_graph_input.mIdentifier,
            'mType': sbsar_graph_input.mType,
            'default': sbsar_graph_input.getDefaultValue(),
            'label': label,
            'prop': sbsar_name_prop.get(
                sbsar_graph_input.mIdentifier, sbsar_graph_input.mIdentifier)
        }
        if gui is not None:
            if gui.mWidget in ['togglebutton', 'combobox', 'color']:
                input_info['mWidget'] = gui.mWidget
            if gui.mWidget == 'combobox':
                combobox_box: SBSARGuiComboBox = gui.mGuiComboBox
                drop_down_list = combobox_box.getDropDownList()
                if drop_down_list is not None:
                    drop_down_keys = list(drop_down_list.keys())
                    drop_down_keys.sort()
                    enum_items = []
                    for key in drop_down_keys:
                        print(type(key))
                        enum_items.append(
                            (str(key), drop_down_list[key], drop_down_list[key]))
                    input_info['enum_items'] = enum_items
                    input_info['drop_down_list'] = enum_items
                    # assign default value to string here
                    if input_info.get('default') is not None:
                        input_info['default'] = str(input_info['default'])  # drop_down_list[input_info['default']]

        if sbsar_graph_input.getMaxValue() is not None:
            input_info['max'] = sbsar_graph_input.getMaxValue()
        if sbsar_graph_input.getMinValue() is not None:
            input_info['min'] = sbsar_graph_input.getMinValue()
        if sbsar_graph_input.getStep() is not None:
            input_info['step'] = int(sbsar_graph_input.getStep() * 100)
        input_list.append(input_info)
    return input_list
