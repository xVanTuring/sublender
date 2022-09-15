import subprocess
import json
from pysbs.batchtools import batchtools
import threading
import asyncio
from typing import List
import bpy
from . import globalvar, settings, utils, consts, async_loop, template
from pysbs.context import Context
import os
import pathlib
from bpy.types import Operator

from bpy.props import BoolProperty, StringProperty
import datetime


def build_resource_dict(result):
    resource_dict = {}
    for output in result:
        img_output = json.loads(str(output, encoding="ascii"))
        for usage in img_output[0]['outputs'][0]['usages']:
            if resource_dict.get(usage) is None:
                resource_dict[usage] = []
            resource_dict[usage].append(img_output[0]['outputs'][0]['value'])
    return resource_dict


class Sublender_Render_Texture_Async(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.render_texture_async"
    bl_label = "Render Texture"
    bl_description = "Render Texture"
    assign_texture: BoolProperty(name="Assign Texture",
                                 default=False)
    material_name: StringProperty(name="Target Material Name")

    def invoke(self, context, event):
        # TODO check parameters in invoke
        print("Sublender_Render_Texture_Async ... invoke")
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str], output_id: str):
        proc = await asyncio.create_subprocess_exec(
            Context.getBatchToolExePath(5),
            *cmd_list,
            stdout=asyncio.subprocess.PIPE)
        await proc.wait()
        self.report({"INFO"}, "Texture Render Done: {0}".format(output_id))
        return await proc.stdout.read()

    async def async_execute(self, context):
        # read all params
        sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        target_mat = bpy.data.materials.get(self.material_name)
        if target_mat is not None:
            start = datetime.datetime.now()
            m_sublender: settings.Sublender_Material_MT_Setting = target_mat.sublender
            clss_name, clss_info = utils.dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)
            graph_setting = getattr(target_mat, clss_name)
            input_dict = clss_info['input']
            param_list = []
            param_list.append("render")
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
            param_list.append("{outputNodeName}")
            param_list.append('--engine')
            param_list.append('d3d11pc')
            worker_list = []
            for output in clss_info['output']:
                per_output = param_list[:]
                per_output.append("--input-graph-output")
                per_output.append(output)
                worker_list.append(self.render_map(per_output, output))
            result = await asyncio.gather(*worker_list)
            end = datetime.datetime.now()

            resource_dict = build_resource_dict(result)
            m_template = globalvar.material_templates.get(
                m_sublender.material_template)
            template.ensure_assets(target_mat, m_template, resource_dict)

            self.report({"INFO"}, "Time spent: {0}s".format(
                (end - start).total_seconds()))


def register():
    bpy.utils.register_class(Sublender_Render_Texture_Async)


def unregister():
    bpy.utils.unregister_class(Sublender_Render_Texture_Async)
