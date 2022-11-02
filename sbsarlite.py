import py7zr
import os
import xmltodict
from collections import OrderedDict

import tempfile

from . import (parser)


def parse_sbsar_raw(raw: OrderedDict):
    xml_graphs = raw['sbsdescription']['graphs']
    parsed_sbsar = {
        "graphs": []
    }
    graph_count = int(xml_graphs['@count'])
    if graph_count > 1:
        graph_list = xml_graphs['graph']
    else:
        graph_list = [xml_graphs['graph']]
    for i in range(graph_count):
        if graph_list[i].get('@hideInLibrary') == "on":
            continue
        parsed_sbsar['graphs'].append(parse_graph(graph_list[i]))
    return parsed_sbsar


def parse_graph(raw: OrderedDict):
    parsed_graph = {
        'pkgUrl': raw['@pkgurl'],
        'label': raw['@label'],
        'inputs': [],
        'outputs': []
    }
    xml_inputs = raw['inputs']
    input_count = int(xml_inputs['@count'])
    if input_count > 1:
        raw_input_list = xml_inputs['input']
    else:
        raw_input_list = [xml_inputs['input']]
    for i in range(input_count):
        parsed_graph['inputs'].append(parse_input(raw_input_list[i]))

    xml_outputs = raw['outputs']
    output_count = int(xml_outputs['@count'])
    if output_count > 1:
        raw_output_list = xml_outputs['output']
    else:
        raw_output_list = [xml_outputs['output']]
    for i in range(output_count):
        parsed_graph['outputs'].append(parse_output(raw_output_list[i]))
    return parsed_graph


def parse_output(raw: OrderedDict):
    parsed_output = {'identifier': raw['@identifier'],
                     'uid': raw['@uid'],
                     'label': raw['outputgui']['@label']}
    if raw['outputgui']['channels'] is not None:
        usages = []
        if isinstance(raw['outputgui']['channels']['channel'], list):
            channels = raw['outputgui']['channels']['channel']
        else:
            channels = [raw['outputgui']['channels']['channel']]
        for channel in channels:
            usages.append(channel['@names'])
        parsed_output['usages'] = usages

    return parsed_output


def parse_input(raw: OrderedDict):
    parsed_input = {
        'uid': raw['@uid'],
        'identifier': raw['@identifier'],
        'type': int(raw['@type']),
        'prop': parser.uid_prop(raw['@uid'])
    }
    if parsed_input['identifier'] == "$randomseed":
        parsed_input['prop'] = "$randomseed"
    if raw.get('@default') is not None:
        default_value = parse_str_value(
            raw['@default'], parsed_input['type'])
        parsed_input['default'] = default_value
    if raw.get('inputgui') is not None:
        parsed_input['gui'] = parse_gui(raw['inputgui'], parsed_input['type'])
    return parsed_input


def parse_gui(raw: OrderedDict, type_num):
    parsed_gui = {'widget': raw.get('@widget'),
                  'label': raw.get('@label'),
                  'visibleIf': raw.get('@visibleif'),
                  'group': raw.get('@group')}
    if parsed_gui['widget'] == 'slider':
        if raw.get('guislider') is not None:
            parsed_gui['min'] = parse_str_value(
                raw.get('guislider')['@min'], type_num)
            parsed_gui['max'] = parse_str_value(
                raw.get('guislider')['@max'], type_num)
            parsed_gui['step'] = parse_str_value(
                raw.get('guislider')['@step'], type_num)
            if raw.get('guislider').get('@clamp') == "on":
                parsed_gui['clamp'] = True
            else:
                parsed_gui['clamp'] = False
            parsed_gui['label0'] = raw.get('guislider').get('@label0')
            parsed_gui['label1'] = raw.get('guislider').get('@label1')
            parsed_gui['label2'] = raw.get('guislider').get('@label2')
            parsed_gui['label3'] = raw.get('guislider').get('@label3')
    elif parsed_gui['widget'] == 'togglebutton':
        if raw.get('guibutton') is not None:
            parsed_gui['label0'] = raw.get('guibutton').get('@label0')
            parsed_gui['label1'] = raw.get('guibutton').get('@label1')
    elif parsed_gui['widget'] == 'combobox':
        # TODO: parse based on parser
        if raw.get('guicombobox') is not None:
            combo_item_list = []
            for raw_combox_item in raw['guicombobox'].get('guicomboboxitem'):
                combo_item_list.append({
                    'value': int(raw_combox_item.get('@value')),
                    'text': raw_combox_item.get('@text')
                })
            parsed_gui['combo_items'] = combo_item_list
    return parsed_gui


def parse_str_value(raw_str: str, type_num):
    if type_num < 4:
        parsed = [float(value) for value in raw_str.split(',')]
        if len(parsed) == 1:
            return parsed[0]
        return parsed
    elif type_num == 4 or type_num > 7:
        parsed = [int(value) for value in raw_str.split(',')]
        if len(parsed) == 1:
            return parsed[0]
        return parsed

    return raw_str


def parse_doc(file_path: str):
    archive = py7zr.SevenZipFile(file_path, mode='r')
    allfiles = archive.getnames()
    sbsar_xml_path = None
    unzip_dir = os.path.join(tempfile.gettempdir(
    ), "sublender", os.path.basename(file_path))
    for file_name in allfiles:
        if file_name.endswith("xml"):
            sbsar_xml_path = os.path.join(unzip_dir, file_name)
            archive.extract(unzip_dir, targets=file_name)
    if sbsar_xml_path is not None:
        raw_xml_str = open(sbsar_xml_path, 'r').read()
        raw_sbs_xml = xmltodict.parse(raw_xml_str)
        return parse_sbsar_raw(raw_sbs_xml)
    return None


class SBSARTypeEnum:
    FLOAT1 = 0
    FLOAT2 = 1
    FLOAT3 = 2
    FLOAT4 = 3
    INTEGER1 = 4
    IMAGE = 5
    STRING = 6
    FONT = 7
    INTEGER2 = 8
    INTEGER3 = 9
    INTEGER4 = 10
