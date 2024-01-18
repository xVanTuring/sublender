import asyncio
import os
import typing

import bpy

from .. import utils
from .. import render
from ..render import command_line


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
        cmd_list: typing.List[str],
        output_id: str,
        output_dir: str,
        output_dict: dict,
        image_format: str,
    ):
        sbs_render_path = bpy.context.preferences.addons[
            "sublender"
        ].preferences.sbs_render
        process = await asyncio.create_subprocess_exec(
            sbs_render_path, *cmd_list, stdout=asyncio.subprocess.PIPE
        )
        self.process_list.append(process)
        await process.wait()
        texture_path = bpy.path.relpath(
            os.path.join(output_dir, "{0}.{1}".format(output_id, image_format))
        )
        output_info = output_dict.get(output_id)
        bl_img_name = utils.format.gen_image_name(self.material_name, output_info)
        texture_image = bpy.data.images.get(bl_img_name)
        if texture_image is not None:
            texture_image.filepath = texture_path
            texture_image.reload()
        else:
            texture_image = bpy.data.images.load(texture_path, check_existing=True)
            texture_image.name = bl_img_name
            texture_image.use_fake_user = True
        if (
            not output_info["usages"]
            or output_info["usages"][0] not in utils.consts.usage_color_dict
        ):
            texture_image.colorspace_settings.name = "Non-Color"
        if output_info["usages"] is not None:
            material_instance: bpy.types.Material = bpy.data.materials.get(
                self.material_name
            )
            if material_instance is not None:
                image_node: bpy.types.ShaderNodeTexImage = (
                    material_instance.node_tree.nodes.get(output_info["usages"][0])
                )
                if image_node is not None:
                    if (
                        image_node.image is None
                        or image_node.image.filepath != texture_image.filepath
                    ):
                        image_node.image = texture_image

    async def do_import_graph(self, preferences, importing_graph):
        if not importing_graph.enable:
            return
        material_name = importing_graph.material_name
        self.material_name = material_name
        material_inst: bpy.types.Material = bpy.data.materials.get(
            importing_graph.material_name
        )
        m_sublender = material_inst.sublender
        clss_name = utils.format.gen_clss_name(m_sublender.graph_url)
        clss_info = utils.globalvar.graph_clss.get(clss_name)
        graph_setting = getattr(material_inst, clss_name)
        param_list = command_line.generate_cmd_list(
            preferences,
            material_name,
            m_sublender,
            clss_info["input"],
            graph_setting,
        )
        target_dir = render.texture_output_dir(material_name)
        build_list = []
        output_info_list = clss_info["output_info"]["list"]
        for output in output_info_list:
            if getattr(graph_setting, utils.format.sb_output_to_prop(output["name"])):
                build_list.append(output["name"])
        worker_list = []
        for output in build_list:
            per_output_cmd = param_list[:]
            per_output_cmd.append("--input-graph-output")
            per_output_cmd.append(output)
            dep_name = utils.format.sb_output_dep_to_prop(output)
            bit_depth = getattr(graph_setting, dep_name, "0")
            if bit_depth != "0":
                per_output_cmd.append("--output-bit-depth"),
                per_output_cmd.append(bit_depth)
            format_name = utils.format.sb_output_format_to_prop(output)
            output_format = getattr(graph_setting, format_name, "png")
            per_output_cmd.append("--output-format"),
            per_output_cmd.append(output_format)
            worker_list.append(
                self.render_map(
                    per_output_cmd,
                    output,
                    target_dir,
                    clss_info["output_info"]["dict"],
                    output_format,
                )
            )
        await asyncio.gather(*worker_list)

    async def do_update_texture(self, preferences, texture_name, input_id):
        material_inst: bpy.types.Material = bpy.data.materials.get(self.material_name)
        m_sublender = material_inst.sublender
        clss_name = utils.format.gen_clss_name(m_sublender.graph_url)
        clss_info = utils.globalvar.graph_clss.get(clss_name)
        graph_setting = getattr(material_inst, clss_name)
        param_list = command_line.generate_cmd_list(
            preferences,
            self.material_name,
            m_sublender,
            clss_info["input"],
            graph_setting,
        )
        target_dir = render.texture_output_dir(self.material_name)
        use_altered_nodes = preferences.rerender_affected_texture
        alter_outputs = None
        if texture_name == "":
            if use_altered_nodes:
                all_inputs = clss_info["input"]
                for m_input in all_inputs:
                    if m_input["uid"] == input_id:
                        alter_outputs = m_input.get("alteroutputs")
                        if alter_outputs is not None:
                            print(alter_outputs)
                        break

            build_list = []
            output_info_list = clss_info["output_info"]["list"]
            for output in output_info_list:
                if alter_outputs is not None:
                    if output["uid"] not in alter_outputs:
                        continue
                if getattr(
                    graph_setting, utils.format.sb_output_to_prop(output["name"])
                ):
                    build_list.append(output["name"])
            worker_list = []
            for output in build_list:
                per_output_cmd = param_list[:]
                per_output_cmd.append("--input-graph-output")
                per_output_cmd.append(output)
                dep_name = utils.format.sb_output_dep_to_prop(output)
                bit_depth = getattr(graph_setting, dep_name, "0")
                if bit_depth != "0":
                    per_output_cmd.append("--output-bit-depth"),
                    per_output_cmd.append(bit_depth)
                format_name = utils.format.sb_output_format_to_prop(output)
                output_format = getattr(graph_setting, format_name, "png")
                per_output_cmd.append("--output-format"),
                per_output_cmd.append(output_format)
                worker_list.append(
                    self.render_map(
                        per_output_cmd,
                        output,
                        target_dir,
                        clss_info["output_info"]["dict"],
                        output_format,
                    )
                )
            await asyncio.gather(*worker_list)
        else:
            param_list.append("--input-graph-output")
            param_list.append(texture_name)
            dep_name = utils.format.sb_output_dep_to_prop(texture_name)
            bit_depth = getattr(graph_setting, dep_name, "0")
            if bit_depth != "0":
                param_list.append("--output-bit-depth"),
                param_list.append(bit_depth)
            format_name = utils.format.sb_output_format_to_prop(texture_name)
            output_format = getattr(graph_setting, format_name, "png")
            param_list.append("--output-format"),
            param_list.append(output_format)
            await self.render_map(
                param_list,
                texture_name,
                target_dir,
                clss_info["output_info"]["dict"],
                output_format,
            )
