
import bpy
from . import globals
import os
def isType(val, type_str: str):
    return isinstance(val, getattr(bpy.types, type_str))
import json

def ensure_nodes(mat, template):
    # todo: force override position options
    node_list = mat.node_tree.nodes
    for node_info in template['nodes']:
        node_inst = node_list.get(node_info['name'])
        if (node_inst is not None) and (isType(node_inst, node_info['type'])):
            continue
        node_inst = node_list.new(type=node_info['type'])
        node_inst.name = node_info['name']
        if node_info.get('label', None) is not None:
            node_inst.label = node_info['label']
        if node_info.get('location', None) is not None:
            node_inst.location = node_info['location']
        if node_info.get('hide') == True:
            node_inst.hide = True


def ensure_link(mat, template):
    node_list = mat.node_tree.nodes
    node_links = mat.node_tree.links
    for link in template['links']:
        from_node = node_list.get(link['fromNode'])
        to_node = node_list.get(link['toNode'])
        node_links.new(
            from_node.outputs[link['fromSocket']], to_node.inputs[link['toSocket']])


def ensure_assets(mat, template, resource):
    node_list = mat.node_tree.nodes
    for texture_info in template['texture']:
        texture_path = resource.get(texture_info['type'])
        if texture_path is not None:
            image_name = bpy.path.basename(texture_path)
            bpy.ops.image.open(filepath=texture_path)
            target_Node = node_list.get(texture_info['node'])
            texture_img = bpy.data.images.get(image_name)
            if texture_info.get('colorspace') is not None:
                texture_img.colorspace_settings.name = texture_info.get(
                    'colorspace')
            if target_Node is not None:
                target_Node.image = texture_img
            else:
                print("Missing Node:{0}".format(texture_info['node']))
        else:
            print("Missing Texture:{0}".format(texture_info['type']))


def inflate_template(mat, template_name: str):
    # get template_name from material setting
    template = globals.material_templates.get(template_name)
    ensure_nodes(mat, template)
    ensure_link(mat, template)

def load_material_templates():
    template_path = os.path.join(globals.SUBLENDER_DIR, 'templates')
    files = os.listdir(template_path)
    for file_name_full in files:
        full_file_path = os.path.join(template_path, file_name_full)
        if os.path.isfile(full_file_path):
            file_name, file_ext = os.path.splitext(file_name_full)
            if file_ext == ".json":
                with open(full_file_path, 'r') as f:
                    material_temp = json.load(f)
                    globals.material_templates[file_name_full] = material_temp
                    globals.material_template_enum.append((
                        file_name_full,
                        file_name,
                        file_name_full
                    ))
