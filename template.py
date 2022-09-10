
import json
from pysbs.batchtools import batchtools
import threading
from typing import List
import bpy
from . import globals, settings, utils, consts
import os
import pathlib
from bpy.types import Operator

from bpy.props import BoolProperty


def isType(val, type_str: str):
    return isinstance(val, getattr(bpy.types, type_str))


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
        texture_path_list = resource.get(texture_info['type'])
        if texture_path_list is not None and len(texture_path_list) > 0:
            texture_path = texture_path_list[0]
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
    template_path = consts.TEMPLATE_PATH
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
                        material_temp.get('name', file_name),
                        material_temp.get('description', file_name_full),
                    ))


def build_resource_dict(outputs):
    resource_dict = {}
    for output in outputs:
        if output.type == "image":
            for usage in output.usages:
                if resource_dict.get(usage) is None:
                    resource_dict[usage] = []
                resource_dict[usage].append(output.value)
    return resource_dict


class RenderTextureThread(threading.Thread):
    param_list: List[str]
    assign_texture: bool

    def __init__(self, param_list: List[str], assign_texture: bool, material):
        threading.Thread.__init__(self)
        self.param_list = param_list
        self.assign_texture = assign_texture
        self.material = material

    def run(self):
        out = batchtools.sbsrender_render(
            *self.param_list, output_handler=True)
        resource_dict = None

        graph = out.get_results()[0]
        resource_dict = build_resource_dict(graph.outputs)

        m_sublender: settings.Sublender_Material_MT_Setting = self.material.sublender
        m_template = globals.material_templates.get(
            m_sublender.material_template)
        ensure_assets(self.material, m_template, resource_dict)


class Sublender_Render_TEXTURE(Operator):
    bl_idname = "sublender.render_texture"
    bl_label = "Render Texture"
    bl_description = "Render Texture"
    assign_texture: BoolProperty(name="Assign Texture",
                                 default=False)

    def execute(self, context):
        # read all params
        mats = bpy.data.materials
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        target_mat = mats.get(sublender_settings.active_instance)
        if target_mat is not None:
            m_sublender: settings.Sublender_Material_MT_Setting = target_mat.sublender
            clss_name, clss_info = utils.dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)
            graph_setting = getattr(target_mat, clss_name)
            input_dict = clss_info['input']
            param_list = []
            param_list.append("--input")
            param_list.append(m_sublender.package_path)
            param_list.append("--input-graph")
            param_list.append(m_sublender.graph_url)
            for group_key in input_dict:
                input_group = input_dict[group_key]
                for input_info in input_group:
                    value = graph_setting.get(input_info['prop'])
                    if value is not None:
                        param_list.append("--set-value")
                        to_list = getattr(value, 'to_list', None)
                        if to_list is not None:
                            value = ','.join(map(str, to_list()))
                        param_list.append("{0}@{1}".format(
                            input_info['mIdentifier'], value))
            param_list.append("--output-path")
            target_dir = os.path.join(
                globals.SUBLENDER_DIR, sublender_settings.uuid, clss_name)
            pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
            param_list.append(target_dir)
            param_list.append('--engine')
            param_list.append('d3d11pc')
            render_thread = RenderTextureThread(
                param_list, self.assign_texture, target_mat)
            render_thread.start()
        return {'FINISHED'}
