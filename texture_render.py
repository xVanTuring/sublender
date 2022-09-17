import asyncio
import datetime
import json
import os
import pathlib
from typing import List

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator
from pysbs.context import Context

from . import globalvar, settings, utils, consts, async_loop, template


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
    task_id = -1

    def invoke(self, context, event):
        # TODO check parameters in invoke
        # print("Sublender_Render_Texture_Async ... invoke")
        self.task_id = globalvar.get_id()
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
        # sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
        material_inst = bpy.data.materials.get(self.material_name)
        if material_inst is not None:
            await asyncio.sleep(0.5)
            print("Rendering Texture!")
            start = datetime.datetime.now()
            m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
            clss_name, clss_info = utils.dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)
            graph_setting = getattr(material_inst, clss_name)
            input_dict = clss_info['input']
            param_list = ["render", "--input", m_sublender.package_path, "--input-graph", m_sublender.graph_url]
            for input_info in input_dict:
                if input_info['mIdentifier'] == '$outputsize':
                    locked = getattr(
                        graph_setting, consts.output_size_lock, True)
                    param_list.append("--set-value")
                    width = getattr(graph_setting, consts.output_size_x)
                    if locked:
                        param_list.append("{0}@{1},{1}".format(
                            input_info['mIdentifier'], width))
                    else:
                        height = getattr(graph_setting, consts.output_size_x)
                        param_list.append("{0}@{1},{2}".format(
                            input_info['mIdentifier'], width, height))
                else:
                    # print("Current identifier: {0}, current prop: {1}".format(input_info['mIdentifier'],
                    #                                                           input_info['prop']))
                    value = graph_setting.get(input_info['prop'])
                    if value is not None:
                        if input_info.get('enum_items') is not None:
                            print(input_info.get('enum_items'))
                            value = input_info.get('enum_items')[value][0]
                        param_list.append("--set-value")
                        to_list = getattr(value, 'to_list', None)
                        if to_list is not None:
                            if isinstance(value[0], float):
                                # print("This is float vector, from: {0}".format(to_list()))
                                value = ','.join(map(lambda x: ("%0.3f" % x), to_list()))
                                # print("This is float vector, to: {0}".format(value))
                            else:
                                value = ','.join(map(str, to_list()))
                        if isinstance(value, float):
                            # print("Format float value from {0} to {1} ".format(value, ("%.3f" % value)))
                            value = ("%.3f" % value)
                        param_list.append("{0}@{1}".format(
                            input_info['mIdentifier'], value))
            param_list.append("--output-path")
            target_dir = utils.texture_output_dir(clss_name, material_inst.name)
            pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
            param_list.append(target_dir)
            param_list.append("--output-name")
            param_list.append("{outputNodeName}")
            param_list.append('--engine')
            param_list.append('d3d11pc')
            # print(param_list)
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
            template.ensure_assets(material_inst, m_template, resource_dict)

            self.report({"INFO"}, "Time spent: {0}s".format(
                (end - start).total_seconds()))


def register():
    bpy.utils.register_class(Sublender_Render_Texture_Async)


def unregister():
    bpy.utils.unregister_class(Sublender_Render_Texture_Async)
