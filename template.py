import json
import os

import bpy

from . import utils


def is_type(val, type_str: str):
    return isinstance(val, getattr(bpy.types, type_str))


def ensure_nodes(mat: bpy.types.Material, template, clear_nodes: bool):
    node_list = mat.node_tree.nodes
    if clear_nodes:
        node_list.clear()
    for node_info in template['nodes']:
        node_inst = node_list.get(node_info['name'])
        if (node_inst is not None) and (is_type(node_inst, node_info['type'])):
            # reset position here
            if node_info.get('location', None) is not None:
                node_inst.location = node_info['location']
            continue
        node_inst = node_list.new(type=node_info['type'])
        node_inst.name = node_info['name']
        if node_info.get('label', None) is not None:
            node_inst.label = node_info['label']
        if node_info.get('location', None) is not None:
            node_inst.location = node_info['location']
        if node_info.get('hide', False):
            node_inst.hide = True
        if node_info.get('prop') is not None:
            for prop_item in node_info.get('prop'):
                temp = node_inst
                path_list = prop_item['path'].split('.')
                for prop_name in path_list[:-1]:
                    temp = getattr(temp, prop_name)
                    if temp is None:
                        break
                setattr(temp, path_list[-1], prop_item['value'])
        if node_info.get('inputs') is not None:
            for input_item in node_info.get('inputs'):
                node_inst.inputs[input_item['name']].default_value = input_item['value']


def ensure_link(mat, template):
    node_list = mat.node_tree.nodes
    node_links = mat.node_tree.links
    for link in template['links']:
        from_info, to_info = link.split('/')
        from_name, from_socket = from_info.split('.')
        to_name, to_socket = to_info.split('.')
        from_node = node_list.get(from_name)
        to_node = node_list.get(to_name)
        node_links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])


def ensure_options(mat, template):
    if template.get('options') is not None:
        for option in template.get('options'):
            if option == "displacement":
                # works for both cycles and prorender
                if getattr(mat, 'cycles', None) is not None:
                    mat.cycles.displacement_method = 'DISPLACEMENT'


def load_default_texture(mat, template):
    default_color = os.path.join(utils.consts.RESOURCES_PATH, "default_color.png")
    default_normal = os.path.join(utils.consts.RESOURCES_PATH, "default_normal.png")
    default_color_node = bpy.data.images.load(default_color, check_existing=True)
    default_normal_node = bpy.data.images.load(default_normal, check_existing=True)
    for texture in template['texture']:
        texture_node: bpy.types.ShaderNodeTexImage = mat.node_tree.nodes.get(texture)
        if texture_node is not None:
            if texture == 'normal':
                texture_node.image = default_normal_node
            else:
                texture_node.image = default_color_node


def inflate_template(mat, template_name: str, clear_nodes=False):
    template = utils.globalvar.material_templates.get(template_name)
    if template is None:
        return
    ensure_nodes(mat, template, clear_nodes)
    ensure_link(mat, template)
    ensure_options(mat, template)
    load_default_texture(mat, template)


def load_material_templates():
    template_path = utils.consts.TEMPLATE_PATH
    files = os.listdir(template_path)
    files.sort()

    utils.globalvar.material_template_enum.clear()
    utils.globalvar.material_templates.clear()

    for file_name_full in files:
        full_file_path = os.path.join(template_path, file_name_full)
        if os.path.isfile(full_file_path):
            file_name, file_ext = os.path.splitext(file_name_full)
            if file_ext == ".json":
                with open(full_file_path, 'r') as f:
                    material_temp = json.load(f)
                    utils.globalvar.material_templates[file_name_full] = material_temp
                    utils.globalvar.material_template_enum.append((
                        file_name_full,
                        material_temp.get('name', file_name),
                        material_temp.get('description', file_name_full),
                    ))
    utils.globalvar.material_template_enum.append(
        (utils.consts.CUSTOM, "Custom", "Custom Workflow, empty material will be generated."))
