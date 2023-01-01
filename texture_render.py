import asyncio
import datetime
import os
import pathlib
from typing import List

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator

from . import globalvar, settings, utils, consts, async_loop


def generate_cmd_list(context, target_material_name: str, m_sublender, clss_info, graph_setting):
    input_list = clss_info['input']
    param_list = ["render", "--input", m_sublender.package_path, "--input-graph", m_sublender.graph_url]
    for input_info in input_list:
        if input_info['identifier'] == '$outputsize':
            locked = getattr(graph_setting, consts.output_size_lock, True)
            param_list.append("--set-value")
            width = getattr(graph_setting, consts.output_size_x)
            if locked:
                param_list.append("{0}@{1},{1}".format(input_info['identifier'], width))
            else:
                height = getattr(graph_setting, consts.output_size_x)
                param_list.append("{0}@{1},{2}".format(input_info['identifier'], width, height))
        else:
            is_image = input_info['type'] == consts.SBSARTypeEnum.IMAGE
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
                if input_info.get('widget') == 'combobox':
                    value = getattr(graph_setting, input_info['prop']).replace("$NUM:", "")
                param_list.append("{0}@{1}".format(input_info['identifier'], value))
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
    memory_budget = context.preferences.addons[__package__].preferences.memory_budget
    param_list.append("--memory-budget")
    param_list.append("{0}".format(memory_budget))
    return param_list


class SUBLENDER_OT_Render_Texture_Async(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.render_texture_async"
    bl_label = "Render Texture"
    bl_description = "Render Texture"

    importing_graph: BoolProperty(default=False)
    package_path: StringProperty()

    texture_name: StringProperty(default="")

    process_list = list()
    material_name = ""
    single_task = True

    def clean(self, context):
        while self.process_list:
            process: asyncio.subprocess.Process = self.process_list.pop()
            if process.returncode is None:
                print("{} Cancel Task!!!!!!!!".format(self.task_id))
                process.terminate()

    def invoke(self, context, event):
        if self.importing_graph:
            self.task_id = self.package_path
        else:
            material_inst = utils.find_active_mat(context)
            if material_inst is None:
                self.report({"WARNING"}, "No material is selected or given")
                return {"CANCELLED"}
            self.material_name = material_inst.name
            self.task_id = self.material_name
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str], output_id: str, output_dir: str, output_dict: dict,
                         format: str):
        sbs_render_path = bpy.context.preferences.addons[__package__].preferences.sbs_render
        process = await asyncio.create_subprocess_exec(sbs_render_path,
                                                       *cmd_list,
                                                       stdout=asyncio.subprocess.PIPE)
        self.process_list.append(process)
        await process.wait()
        print("Texture {0} Render done!".format(output_id))
        self.report({"INFO"}, "Texture {0} Render done!".format(output_id))
        texture_path = bpy.path.relpath(os.path.join(output_dir, "{0}.{1}".format(output_id, format)))
        output_info = output_dict.get(output_id)
        bl_img_name = utils.gen_image_name(self.material_name, output_info)
        texture_image = bpy.data.images.get(bl_img_name)
        if texture_image is not None:
            texture_image.filepath = texture_path
            texture_image.reload()
        else:
            texture_image = bpy.data.images.load(texture_path, check_existing=True)
            texture_image.name = bl_img_name
            texture_image.use_fake_user = True
        if not output_info['usages'] or output_info['usages'][0] not in consts.usage_color_dict:
            texture_image.colorspace_settings.name = 'Non-Color'
        if output_info['usages'] is not None:
            material_instance: bpy.types.Material = bpy.data.materials.get(self.material_name)
            if material_instance is not None:
                image_node: bpy.types.ShaderNodeTexImage = material_instance.node_tree.nodes.get(
                    output_info['usages'][0])
                if image_node is not None:
                    if image_node.image is None or image_node.image.filepath != texture_image.filepath:
                        image_node.image = texture_image

    async def async_execute(self, context):
        if self.importing_graph:
            start = datetime.datetime.now()
            importing_graph_items = context.scene.sublender_settings.importing_graphs
            for importing_graph in importing_graph_items:
                if not importing_graph.enable:
                    continue
                material_name = importing_graph.material_name
                self.material_name = material_name
                material_inst: bpy.types.Material = bpy.data.materials.get(importing_graph.material_name)
                m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
                clss_name = utils.gen_clss_name(m_sublender.graph_url)
                clss_info = globalvar.graph_clss.get(clss_name)
                graph_setting = getattr(material_inst, clss_name)
                param_list = generate_cmd_list(context, material_name, m_sublender, clss_info, graph_setting)
                target_dir = utils.texture_output_dir(material_name)
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
                    dep_name = utils.sb_output_dep_to_prop(output)
                    bit_depth = getattr(graph_setting, dep_name, "0")
                    if bit_depth != "0":
                        per_output_cmd.append("--output-bit-depth"),
                        per_output_cmd.append(bit_depth)
                    format_name = utils.sb_output_format_to_prop(output)
                    output_format = getattr(graph_setting, format_name, "png")
                    per_output_cmd.append("--output-format"),
                    per_output_cmd.append(output_format)
                    worker_list.append(
                        self.render_map(per_output_cmd, output, target_dir, clss_info['output_info']['dict'],
                                        output_format))
                await asyncio.gather(*worker_list)
                end = datetime.datetime.now()
                self.report({"INFO"}, "Render Done! Time spent: {0}s.".format((end - start).total_seconds()))
        else:
            if self.texture_name == "":
                await asyncio.sleep(0.2)
            start = datetime.datetime.now()
            material_inst: bpy.types.Material = bpy.data.materials.get(self.material_name)
            m_sublender: settings.Sublender_Material_MT_Setting = material_inst.sublender
            clss_name = utils.gen_clss_name(m_sublender.graph_url)
            clss_info = globalvar.graph_clss.get(clss_name)
            graph_setting = getattr(material_inst, clss_name)

            param_list = generate_cmd_list(context, self.material_name, m_sublender, clss_info, graph_setting)
            target_dir = utils.texture_output_dir(self.material_name)
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
                    dep_name = utils.sb_output_dep_to_prop(output)
                    bit_depth = getattr(graph_setting, dep_name, "0")
                    if bit_depth != "0":
                        per_output_cmd.append("--output-bit-depth"),
                        per_output_cmd.append(bit_depth)
                    format_name = utils.sb_output_format_to_prop(output)
                    output_format = getattr(graph_setting, format_name, "png")
                    per_output_cmd.append("--output-format"),
                    per_output_cmd.append(output_format)
                    worker_list.append(
                        self.render_map(per_output_cmd, output, target_dir, clss_info['output_info']['dict'],
                                        output_format))
                await asyncio.gather(*worker_list)
            else:
                param_list.append("--input-graph-output")
                param_list.append(self.texture_name)
                dep_name = utils.sb_output_dep_to_prop(self.texture_name)
                bit_depth = getattr(graph_setting, dep_name, "0")
                if bit_depth != "0":
                    param_list.append("--output-bit-depth"),
                    param_list.append(bit_depth)
                format_name = utils.sb_output_format_to_prop(self.texture_name)
                output_format = getattr(graph_setting, format_name, "png")
                param_list.append("--output-format"),
                param_list.append(output_format)
                await self.render_map(param_list, self.texture_name, target_dir,
                                      clss_info['output_info']['dict'], output_format)
            end = datetime.datetime.now()
            self.report({"INFO"}, "Render Done! Time spent: {0}s.".format((end - start).total_seconds()))


def register():
    bpy.utils.register_class(SUBLENDER_OT_Render_Texture_Async)


def unregister():
    bpy.utils.unregister_class(SUBLENDER_OT_Render_Texture_Async)
