import json
import os

import bpy

from . import globalvar, consts


def isType(val, type_str: str):
    return isinstance(val, getattr(bpy.types, type_str))


def ensure_nodes(mat: bpy.types.Material, template, clear_nodes: bool):
    node_list = mat.node_tree.nodes
    if clear_nodes:
        node_list.clear()
    for node_info in template['nodes']:
        node_inst = node_list.get(node_info['name'])
        if (node_inst is not None) and (isType(node_inst, node_info['type'])):
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


def ensure_link(mat, template):
    node_list = mat.node_tree.nodes
    node_links = mat.node_tree.links
    for link in template['links']:
        from_node = node_list.get(link['fromNode'])
        to_node = node_list.get(link['toNode'])
        node_links.new(
            from_node.outputs[link['fromSocket']], to_node.inputs[link['toSocket']])


def ensure_options(mat, template):
    if template.get('options') is not None:
        for option in template.get('options'):
            if option == "withHeight":
                # works for both cycles and prorender
                if getattr(mat, 'cycles', None) is not None:
                    mat.cycles.displacement_method = 'DISPLACEMENT'


# TODO to name
def ensure_assets(context, material_name: str, template, resource):
    material = bpy.data.materials.get(material_name)
    preferences = context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    compatible_undo = addon_prefs.compatible_mode
    node_list = material.node_tree.nodes
    for texture_info in template['texture']:
        texture_path_list = resource.get(texture_info['type'])
        if texture_path_list is not None and len(texture_path_list) > 0:
            texture_path = texture_path_list[0]
            target_node = node_list.get(texture_info['node'])
            target_img_name = "{0}_{1}".format(
                material.name, texture_info['type'])
            if compatible_undo:
                texture_img = bpy.data.images.load(
                    texture_path, check_existing=False)
                texture_img.name = target_img_name
            else:
                texture_img = bpy.data.images.get(target_img_name)
                if texture_img is not None:
                    texture_img.filepath = texture_path
                    texture_img.reload()
                else:
                    texture_img = bpy.data.images.load(
                        texture_path, check_existing=True)
                    texture_img.name = target_img_name
            if texture_info.get('colorspace') is not None:
                texture_img.colorspace_settings.name = texture_info.get(
                    'colorspace')
            if target_node is not None:
                target_node.image = texture_img
            else:
                print("Missing image node with name:{0}".format(
                    texture_info['node']))
        else:
            print("Missing Texture:{0}".format(texture_info['type']))


def inflate_template(mat, template_name: str, clear_nodes=False):
    template = globalvar.material_templates.get(template_name)
    if template is None:
        raise Exception("Empty workflow")
    ensure_nodes(mat, template, clear_nodes)
    ensure_link(mat, template)
    ensure_options(mat, template)


def load_material_templates():
    template_path = consts.TEMPLATE_PATH
    files = os.listdir(template_path)

    globalvar.material_template_enum.clear()
    globalvar.material_templates.clear()

    for file_name_full in files:
        full_file_path = os.path.join(template_path, file_name_full)
        if os.path.isfile(full_file_path):
            file_name, file_ext = os.path.splitext(file_name_full)
            if file_ext == ".json":
                with open(full_file_path, 'r') as f:
                    material_temp = json.load(f)
                    globalvar.material_templates[file_name_full] = material_temp
                    globalvar.material_template_enum.append((
                        file_name_full,
                        material_temp.get('name', file_name),
                        material_temp.get('description', file_name_full),
                    ))
    globalvar.material_template_enum.append((
        consts.CUSTOM, "Custom", "Custom Workflow, empty material will be generated."
    ))
