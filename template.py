
import subprocess
import json
from pysbs.batchtools import batchtools
import threading
from typing import List
import bpy
from . import globals, settings, utils, consts
import os
import pathlib
from bpy.types import Operator

from bpy.props import BoolProperty, StringProperty


def isType(val, type_str: str):
    return isinstance(val, getattr(bpy.types, type_str))


def ensure_nodes(mat, template):
    node_list = mat.node_tree.nodes
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


def ensure_options(mat, template):
    if template.get('options') is not None:
        for option in template.get('options'):
            if option == "withHeight":
                # works for both cycles and prorender
                if getattr(mat, 'cycles', None) is not None:
                    mat.cycles.displacement_method = 'DISPLACEMENT'


def ensure_assets(material, template, resource):
    node_list = material.node_tree.nodes
    for texture_info in template['texture']:
        texture_path_list = resource.get(texture_info['type'])
        if texture_path_list is not None and len(texture_path_list) > 0:
            texture_path = texture_path_list[0]
            # image_name = bpy.path.basename(texture_path)
            target_node = node_list.get(texture_info['node'])
            target_img_name = "{0}_{1}".format(
                material.name, texture_info['type'])
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


def inflate_template(mat, template_name: str):
    template = globals.material_templates.get(template_name)
    ensure_nodes(mat, template)
    ensure_link(mat, template)
    ensure_options(mat, template)


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
    globals.material_template_enum.append((
        consts.CUSTOM, "Custom", "Custom Workflow, empty material will be generated"
    ))


def build_resource_dict(outputs):
    resource_dict = {}
    for output in outputs:
        if output['type'] == "image":
            for usage in output['usages']:
                if resource_dict.get(usage) is None:
                    resource_dict[usage] = []
                resource_dict[usage].append(output['value'])
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
        P: subprocess.Popen = batchtools.sbsrender_render(
            *self.param_list, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, universal_newlines=True)
        # if self.assign_texture:
        stdout_str = str(P.stdout.read())
        outputs = json.loads(stdout_str)
        graph = outputs[0]
        resource_dict = build_resource_dict(graph['outputs'])
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
    material_name: StringProperty(name="Target Material Name")

    def execute(self, context):
        # read all params
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        target_mat = bpy.data.materials.get(self.material_name)
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
                    if input_info['mIdentifier'] == '$outputsize':
                        locked = getattr(
                            graph_setting, 'output_size_lock', True)
                        param_list.append("--set-value")
                        width = getattr(graph_setting, 'output_size_x')
                        if locked:
                            param_list.append("{0}@{1},{1}".format(
                                input_info['mIdentifier'], width))
                        else:
                            height = getattr(graph_setting, 'output_size_x')
                            param_list.append("{0}@{1},{2}".format(
                                input_info['mIdentifier'], width, height))
                    else:
                        # TODO use getattr
                        value = graph_setting.get(input_info['prop'])
                        if value is not None:
                            param_list.append("--set-value")
                            to_list = getattr(value, 'to_list', None)
                            if to_list is not None:
                                value = ','.join(map(str, to_list()))
                            param_list.append("{0}@{1}".format(
                                input_info['mIdentifier'], value))
            param_list.append("--output-path")
            instance_name = bpy.path.clean_name(target_mat.name)
            target_dir = os.path.join(
                consts.SUBLENDER_DIR, sublender_settings.uuid, clss_name, instance_name)
            pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
            param_list.append(target_dir)
            param_list.append("--output-name")
            # shorter name
            param_list.append("{outputNodeName}")
            # TODO Cross Platform
            param_list.append('--engine')
            param_list.append('d3d11pc')
            print(param_list)
            print(" ".join(param_list))
            render_thread = RenderTextureThread(
                param_list, self.assign_texture, target_mat)
            render_thread.start()
        return {'FINISHED'}
