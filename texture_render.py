import asyncio
import datetime
import json
import pathlib
from typing import List

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator
from pysbs.context import Context
from pysbs.sbsarchive.sbsarchive import SBSARGraph
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

    def invoke(self, context, event):
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str], output_id: str):
        proc = await asyncio.create_subprocess_exec(
            Context.getBatchToolExePath(5),
            *cmd_list,
            stdout=asyncio.subprocess.PIPE)
        await proc.wait()
        self.report({"INFO"}, "Texture {0} Render: Done".format(output_id))
        return await proc.stdout.read()

    async def async_execute(self, context):
        material_inst = bpy.data.materials.get(self.material_name)
        if material_inst is not None:
            await asyncio.sleep(0.3)
            start = datetime.datetime.now()
            m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
            clss_name, clss_info = utils.dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)
            graph_setting = getattr(material_inst, clss_name)
            input_list = clss_info['input']
            param_list = ["render", "--input", m_sublender.package_path, "--input-graph", m_sublender.graph_url]
            for input_info in input_list:
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
                    value = graph_setting.get(input_info['prop'])
                    if value is not None:
                        if input_info.get('enum_items') is not None:
                            value = input_info.get('enum_items')[value][0]
                        param_list.append("--set-value")
                        to_list = getattr(value, 'to_list', None)
                        if to_list is not None:
                            if isinstance(value[0], float):
                                value = ','.join(map(lambda x: ("%0.3f" % x), to_list()))
                            else:
                                value = ','.join(map(str, to_list()))
                        if isinstance(value, float):
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
            worker_list = []
            # read material setting
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            m_workflow = globalvar.material_templates.get(
                m_sublender.material_template)
            output_list = clss_info['output']
            if addon_prefs.default_render_policy == "workflow":
                if m_sublender.material_template != consts.CUSTOM:
                    output_usage_dict = clss_info['output_usage_dict']
                    output_list = []
                    for item in m_workflow['texture']:
                        if output_usage_dict.get(item['type']) is not None:
                            output_list.append(output_usage_dict.get(item['type'])[0])
                        else:
                            print("Missing texture with Usage: {0}".format(item['type']))
            # elif addon_prefs.default_render_policy == "channels":
            #     sbsar_graph: SBSARGraph = clss_info['graph']
            #     channels_options = sbsar_graph.getAllInputsInGroup("Channels")
            #     if len(channels_options) != 0:
            #         # do have this group
            #         pass
            print(output_list)
            for output in output_list:
                per_output = param_list[:]
                per_output.append("--input-graph-output")
                per_output.append(output)
                worker_list.append(self.render_map(per_output, output))
            result = await asyncio.gather(*worker_list)
            end = datetime.datetime.now()
            resource_dict = build_resource_dict(result)
            template.ensure_assets(context, material_inst, m_workflow, resource_dict)
            self.report({"INFO"}, "Time spent: {0}s".format(
                (end - start).total_seconds()))


def register():
    bpy.utils.register_class(Sublender_Render_Texture_Async)


def unregister():
    bpy.utils.unregister_class(Sublender_Render_Texture_Async)
