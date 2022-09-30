import asyncio
import datetime
import json
import os
import pathlib
from typing import List

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from pysbs import context as sbsContext
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum

from . import globalvar, settings, utils, consts, async_loop


def generate_cmd_list(context, target_material_name: str,
                      m_sublender, clss_info, graph_setting):
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
            is_image = input_info['mType'] == SBSARTypeEnum.IMAGE
            value = graph_setting.get(input_info['prop'])
            if value is not None:
                if input_info.get('enum_items') is not None:
                    value = input_info.get('enum_items')[value][0]
                if is_image:
                    if value == "":
                        continue
                    else:
                        if not os.path.exists(value):
                            print("Image is missing")
                        param_list.append("--set-entry")
                else:
                    param_list.append("--set-value")
                to_list = getattr(value, 'to_list', None)
                if to_list is not None:
                    if isinstance(value[0], float):
                        value = ','.join(map(lambda x: ("%0.3f" % x), to_list()))
                    else:
                        value = ','.join(map(str, to_list()))
                if isinstance(value, float):
                    value = ("%.3f" % value)
                if isinstance(value, str) and value.startswith("$NUM:"):
                    value = value.replace("$NUM:", "")
                param_list.append("{0}@{1}".format(
                    input_info['mIdentifier'], value))
    param_list.append("--output-path")
    target_dir = utils.texture_output_dir(target_material_name)
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    param_list.append(target_dir)
    param_list.append("--output-name")
    param_list.append("{outputNodeName}")
    engine_value = context.preferences.addons[__package__].preferences.engine_enum
    if engine_value != "$default$":
        if engine_value != consts.CUSTOM:
            param_list.append('--engine')
            param_list.append(engine_value)
            print("Render engine is {0}".format(engine_value))
        else:
            custom_value = context.preferences.addons[__package__].preferences.custom_engine
            if custom_value != "":
                param_list.append('--engine')
                param_list.append(custom_value)
                print("Render engine is {0}".format(custom_value))
    else:
        print("Use Default Engine")
    return param_list


class Sublender_Render_Texture_Async(async_loop.AsyncModalOperatorMixin,
                                     Operator):
    bl_idname = "sublender.render_texture_async"
    bl_label = "Render Texture"
    bl_description = "Render Texture"
    assign_material: bpy.props.BoolProperty()
    material_name: StringProperty(name="Target Material Name, Optional", default="")
    texture_name: StringProperty(default="")
    process_list = list()

    def clean(self, context):
        while self.process_list:
            process: asyncio.subprocess.Process = self.process_list.pop()
            if process.returncode is None:
                process.terminate()

    def invoke(self, context, event):
        if self.material_name != "":
            material_inst = bpy.data.materials.get(self.material_name)
        else:
            material_inst = utils.find_active_mat(context)
        if material_inst is None:
            self.report({"WARNING"}, "No material is selected or given")
            return {"CANCELLED"}
        self.material_name = material_inst.name
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str], output_id: str):
        process = await asyncio.create_subprocess_exec(
            sbsContext.Context.getBatchToolExePath(5),
            *cmd_list,
            stdout=asyncio.subprocess.PIPE)
        self.process_list.append(process)
        await process.wait()
        self.report({"INFO"}, "Texture {0} Render done!".format(output_id))
        output_result = await process.stdout.read()
        img_output_info = json.loads(str(output_result, encoding="ascii"))
        usages = img_output_info[0]['outputs'][0]['usages']
        texture_path = bpy.path.relpath(img_output_info[0]['outputs'][0]['value'])
        one_usage = None
        if len(usages) > 0:
            one_usage = usages[0]
            image_name = '{0}_{1}'.format(self.material_name, usages[0])
        else:
            graph_identifier = img_output_info[0]['outputs'][0]['identifier']
            image_name = '{0}_{1}'.format(self.material_name, graph_identifier)
        texture_image = bpy.data.images.get(image_name)
        if texture_image is not None:
            texture_image.filepath = texture_path
            texture_image.reload()
        else:
            texture_image = bpy.data.images.load(
                texture_path, check_existing=True)
            texture_image.name = image_name
            texture_image.use_fake_user = True
        if one_usage is None or one_usage not in consts.usage_color_dict:
            texture_image.colorspace_settings.name = 'Non-Color'
        if self.assign_material and one_usage is not None:
            material_instance: bpy.types.Material = bpy.data.materials.get(self.material_name)
            if material_instance is not None:
                image_node: bpy.types.ShaderNodeTexImage = material_instance.node_tree.nodes.get(one_usage)
                if image_node is not None:
                    image_node.image = texture_image

        return output_result

    async def async_execute(self, context):
        if self.material_name != "":
            if self.texture_name == "":
                await asyncio.sleep(0.3)
            start = datetime.datetime.now()
            material_inst: bpy.types.Material = bpy.data.materials.get(self.material_name)
            m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
            clss_name = utils.gen_clss_name(m_sublender.graph_url)
            clss_info = globalvar.graph_clss.get(clss_name)
            graph_setting = getattr(material_inst, clss_name)

            param_list = generate_cmd_list(context, self.material_name,
                                           m_sublender, clss_info, graph_setting)
            if self.texture_name == "":
                build_list = []
                output_info_list = clss_info['output_info']['list']
                for output in output_info_list:
                    if getattr(graph_setting, utils.sb_output_to_prop(output['name'])):
                        build_list.append(output['name'])
                worker_list = []
                for output in build_list:
                    per_output_cmd = param_list[:]
                    per_output_cmd.append("--input-graph-output")
                    per_output_cmd.append(output)
                    worker_list.append(
                        self.render_map(per_output_cmd, output))
                await asyncio.gather(*worker_list)
            else:
                param_list.append("--input-graph-output")
                param_list.append(self.texture_name)
                await self.render_map(param_list, self.texture_name)
            end = datetime.datetime.now()
            self.report({"INFO"}, "Render Done! Time spent: {0}s.".format(
                (end - start).total_seconds()))


def register():
    bpy.utils.register_class(Sublender_Render_Texture_Async)


def unregister():
    bpy.utils.unregister_class(Sublender_Render_Texture_Async)
