from . consts import sbsar_name_to_label, UNGROUPED, type_dict

from pysbs.sbsarchive.sbsargraph import SBSARInput
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
from pysbs import sbsarchive, context
from typing import List



def parseSbsarInput(graph_inputs: List[SBSARInput]):
    input_list = []
    for sbsa_graph_input in graph_inputs:
        group = sbsa_graph_input.getGroup()
        gui: SBSARInputGui = sbsa_graph_input.getInputGui()
        label = sbsar_name_to_label.get(
            sbsa_graph_input.mIdentifier, sbsa_graph_input.mIdentifier)
        if gui is not None:
            label = gui.mLabel
        if group is None:
            group = UNGROUPED
        input_info = {
            'group': group,
            'mIdentifier': sbsa_graph_input.mIdentifier,
            'mType': sbsa_graph_input.mType,
            'mTypeStr': type_dict[sbsa_graph_input.mType],
            'default': sbsa_graph_input.getDefaultValue(),
            'label': label
        }
        if gui is not None:
            if gui.mWidget in ['togglebutton', 'combobox', 'color']:
                input_info['mWidget'] = gui.mWidget
            if gui.mWidget == 'combobox':
                comboxBox: SBSARGuiComboBox = gui.mGuiComboBox
                drop_down = comboxBox.getDropDownList()
                if drop_down is not None:
                    drop_down_keys = list(drop_down.keys())
                    drop_down_keys.sort()
                    drop_down_list = []
                    for key in drop_down_keys:
                        drop_down_list.append(
                            (drop_down[key], drop_down[key], drop_down[key]))
                    input_info['drop_down'] = drop_down_list
        if sbsa_graph_input.getMaxValue() is not None:
            input_info['max'] = sbsa_graph_input.getMaxValue()
        if sbsa_graph_input.getMinValue() is not None:
            input_info['min'] = sbsa_graph_input.getMinValue()
        if sbsa_graph_input.getStep() is not None:
            input_info['step'] = int(sbsa_graph_input.getStep()*100)
        input_list.append(input_info)
    return input_list
