import asyncio
import logging
import os
import typing

import bpy

from .. import render, consts, globalvar, formatting
from ..datatypes import OutputInfoData
from ..preference import get_preferences, SublenderPreferences
from ..props import get_material_sublender, ImportingGraphItem
from ..render import command_line

log = logging.getLogger(__name__)


def make_output_cmd(output_cmd: list[str], graph_setting, output_id: str):
    output_cmd.append("--input-graph-output")
    output_cmd.append(output_id)
    dep_name = formatting.sb_output_dep_to_prop(output_id)
    bit_depth = getattr(graph_setting, dep_name, "0")
    if bit_depth != "0":
        output_cmd.append("--output-bit-depth"),
        output_cmd.append(bit_depth)
    format_name = formatting.sb_output_format_to_prop(output_id)
    output_format = getattr(graph_setting, format_name, "png")
    output_cmd.append("--output-format"),
    output_cmd.append(output_format)
    return output_format


class RenderTextureBase:
    process_list: typing.List[asyncio.subprocess.Process] = list()
    material_name = ""

    def do_clean(self):
        while self.process_list:
            process = self.process_list.pop()
            if process.returncode is None:
                process.kill()

    async def render_map(
            self,
            cmd_list: list[str],
            output_id: str,
            output_dir: str,
            output_dict: dict[str, OutputInfoData],
            image_format: str,
    ):
        sbs_render_path = get_preferences().sbs_render
        process = await asyncio.create_subprocess_exec(
            sbs_render_path, *cmd_list, stdout=asyncio.subprocess.PIPE
        )
        self.process_list.append(process)
        await process.wait()
        texture_path = bpy.path.relpath(
            os.path.join(output_dir, "{0}.{1}".format(output_id, image_format))
        )
        output_info = output_dict.get(output_id)
        bl_img_name = formatting.gen_image_name(self.material_name, output_info)
        texture_image = bpy.data.images.get(bl_img_name)
        if texture_image is not None:
            texture_image.filepath = texture_path
            texture_image.reload()
        else:
            texture_image = bpy.data.images.load(texture_path, check_existing=True)
            texture_image.name = bl_img_name
            texture_image.use_fake_user = True
        if (
                not output_info.usages
                or output_info.usages[0] not in consts.usage_color_dict
        ):
            texture_image.colorspace_settings.name = "Non-Color"
        if output_info.usages is not None:
            material_instance: bpy.types.Material = bpy.data.materials.get(
                self.material_name
            )
            if material_instance is not None:
                image_node: bpy.types.ShaderNodeTexImage = (
                    material_instance.node_tree.nodes.get(output_info.usages[0])
                )
                if image_node is not None:
                    if (
                            image_node.image is None
                            or image_node.image.filepath != texture_image.filepath
                    ):
                        image_node.image = texture_image

    def make_batch_render_worker(
            self,
            param_list: list[str],
            graph_setting,
            target_dir: str,
            output_dict: typing.Dict[str, OutputInfoData],
            build_list: list[str],
    ):
        worker_list = []
        for output in build_list:
            per_output_cmd = param_list[:]
            output_format = make_output_cmd(per_output_cmd, graph_setting, output)
            worker_list.append(
                self.render_map(
                    per_output_cmd,
                    output,
                    target_dir,
                    output_dict,
                    output_format,
                )
            )
        return worker_list

    async def do_import_graph(self, preferences: SublenderPreferences, importing_graph: ImportingGraphItem):
        if not importing_graph.enable:
            return
        material_name: str = importing_graph.material_name
        self.material_name = material_name

        material_inst = bpy.data.materials.get(
            importing_graph.material_name
        )
        m_sublender = get_material_sublender(material_inst)
        clss_name = formatting.gen_clss_name(m_sublender.graph_url)
        clss_info = globalvar.graph_clss.get(clss_name)
        graph_setting = getattr(material_inst, clss_name)
        param_list = command_line.generate_render_params(
            preferences,
            material_name,
            m_sublender,
            clss_info.input,
            graph_setting,
        )
        target_dir = render.texture_output_dir(material_name)
        build_list = []
        output_info_list = clss_info.output_info.list
        for output in output_info_list:
            if getattr(graph_setting, formatting.sb_output_to_prop(output.name)):
                build_list.append(output.name)
        worker_list = self.make_batch_render_worker(
            param_list,
            graph_setting,
            target_dir,
            clss_info.output_info.dict,
            build_list,
        )
        await asyncio.gather(*worker_list)
        material_inst.asset_generate_preview()

    async def do_update_texture(self, preferences: SublenderPreferences, texture_name: str, input_id: str):
        material_inst: bpy.types.Material = bpy.data.materials.get(self.material_name)
        m_sublender = get_material_sublender(material_inst)
        clss_name = formatting.gen_clss_name(m_sublender.graph_url)
        clss_info = globalvar.graph_clss.get(clss_name)
        graph_setting = getattr(material_inst, clss_name)
        param_list = command_line.generate_render_params(
            preferences,
            self.material_name,
            m_sublender,
            clss_info.input,
            graph_setting,
        )
        target_dir = render.texture_output_dir(self.material_name)
        use_altered_nodes = preferences.rerender_affected_texture
        alter_outputs = None

        if texture_name == "":
            if use_altered_nodes:
                all_inputs = clss_info.input
                for m_input in all_inputs:
                    if m_input.uid == input_id:
                        alter_outputs = m_input.alteroutputs
                        if alter_outputs is not None:
                            log.debug("alter_outputs: %s", alter_outputs)
                        break

            build_list: list[str] = []
            output_info_list = clss_info.output_info.list
            for output in output_info_list:
                if alter_outputs is not None:
                    if output.uid not in alter_outputs:
                        continue
                if getattr(graph_setting, formatting.sb_output_to_prop(output.name)):
                    build_list.append(output.name)

            worker_list = self.make_batch_render_worker(
                param_list,
                graph_setting,
                target_dir,
                clss_info.output_info.dict,
                build_list,
            )
            await asyncio.gather(*worker_list)
        else:
            await self.render_specify_texture(
                clss_info, graph_setting, param_list, target_dir, texture_name
            )

    async def render_specify_texture(
            self, clss_info, graph_setting, param_list, target_dir, texture_name
    ):
        output_format = make_output_cmd(param_list, graph_setting, texture_name)
        await self.render_map(
            param_list,
            texture_name,
            target_dir,
            clss_info.output_info.dict,
            output_format,
        )
