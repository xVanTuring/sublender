import datetime
import json
import pathlib
import shutil
from typing import List

import asyncio
import bpy
import os
import sys
from bpy.props import StringProperty
from bpy.types import Operator
from bpy.utils import previews

from . import consts, async_loop, utils, globalvar

default_usage_list = ["baseColor",
                      "metallic",
                      "roughness",
                      "normal", ]


def generate_cmd_list(context, target_dir: str,
                      package_path, graph_url):
    param_list = ["render", "--input", package_path, "--input-graph", graph_url, "--set-value", "$outputsize@9,9",
                  "--output-path"]
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    param_list.append(target_dir)

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


class SUBLENDER_OT_Render_Preview_Async(async_loop.AsyncModalOperatorMixin,
                                        Operator):
    bl_idname = "sublender.render_preview_async"
    bl_label = "Render Preview"
    bl_description = "Render Preview"
    package_path: StringProperty(default="")
    process_list = list()

    def clean(self, context):
        while self.process_list:
            process: asyncio.subprocess.Process = self.process_list.pop()
            if process.returncode is None:
                process.terminate()

    def invoke(self, context, event):
        if self.package_path == "":
            self.report({"WARNING"}, "No Graph is selected or given")
            return {"CANCELLED"}
        self.task_id = self.package_path
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str]):
        sbs_render_path = bpy.context.preferences.addons[__package__].preferences.sbs_render
        await self.run_async(sbs_render_path, cmd_list)

    async def run_async(self, exec_path: str, cmd_list: List[str], ):
        process = await asyncio.create_subprocess_exec(
            exec_path,
            *cmd_list,
            stdout=asyncio.subprocess.PIPE)
        self.process_list.append(process)
        await process.wait()

    async def async_execute(self, context):
        ensure_library()
        start = datetime.datetime.now()
        target_dir = consts.sublender_library_render_dir
        for importing_graph in context.scene.sublender_library.importing_graphs:
            if not importing_graph.enable:
                continue

            param_list = generate_cmd_list(context, target_dir,
                                           self.package_path, importing_graph.graph_url)
            package_info = globalvar.sbsar_dict.get(self.package_path)
            current_graph = None
            build_list = []
            for graph in package_info['graphs']:
                if graph['pkgUrl'] == importing_graph.graph_url:
                    current_graph = graph
                    _, _, output_usage_dict = utils.graph_output_parse(graph['outputs'])
                    for usage in output_usage_dict:
                        if usage in default_usage_list:
                            build_list.append((output_usage_dict[usage][0], usage))
                    break
            label = current_graph['label']
            if label == "":
                label = bpy.utils.escape_identifier(importing_graph.graph_url).replace("://", "")
            uu_key = "{}_{}".format(label, package_info["asmuid"])
            existed_material = globalvar.library["materials"].get(uu_key)
            if existed_material is not None:
                self.report({"WARNING"}, "Package has already been imported!")
                return

            worker_list = []
            for output in build_list:
                per_output_cmd = param_list[:]
                per_output_cmd.append("--input-graph-output")
                per_output_cmd.append(output[0])
                per_output_cmd.append("--output-name")
                per_output_cmd.append(output[1])
                worker_list.append(
                    self.render_map(per_output_cmd))

            await asyncio.gather(*worker_list)
            preview_cmd = ["-b",
                           consts.sublender_library_render_template_file,
                           "-o",
                           consts.sublender_preview_img_template_file,
                           "-f",
                           "1"]
            await self.run_async(sys.executable, preview_cmd)

            preview_folder = os.path.join(consts.sublender_library_dir, uu_key, "default")
            pathlib.Path(preview_folder).mkdir(parents=True, exist_ok=True)
            copied_img = shutil.copy(consts.sublender_preview_img_file, os.path.join(preview_folder, "preview.png"))
            copied_sbsar = shutil.copy(self.package_path, pathlib.Path(preview_folder, "../").resolve())

            globalvar.library["materials"][uu_key] = {
                "label": label,
                "sbsar_path": copied_sbsar,
                "preview": copied_img,
                "pkg_url": current_graph['pkgUrl'],
                "ar_uid": package_info["asmuid"],
                "category": current_graph["category"],
                "description": current_graph["description"]
            }
            sync_library()
            generate_preview()
        end = datetime.datetime.now()
        # https://blender.stackexchange.com/questions/30488/require-blender-to-update-n-or-t-panel
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
                break
        self.report({"INFO"}, "Render Done! Time spent: {0}s.".format(
            (end - start).total_seconds()))


class SUBLENDER_OT_REMOVE_MATERIAL(Operator):
    bl_idname = "sublender.remove_material"
    bl_label = "Remove"
    bl_description = "Remove selected material"

    def execute(self, context):
        selected_uid = context.scene.sublender_library.library_preview
        del globalvar.library["materials"][selected_uid]
        sync_library()
        generate_preview()
        if context.scene['sublender_library']['library_preview'] >= len(globalvar.library_preview_enum) and len(
                globalvar.library_preview_enum) > 0:
            context.scene['sublender_library']['library_preview'] = len(globalvar.library_preview_enum) - 1
        shutil.rmtree(os.path.join(consts.sublender_library_dir, selected_uid))
        return {'FINISHED'}


# blender -b ./template.blend -o ~/Desktop/out_cycles# -E BLENDER_EEVEE -f 1
# CYCLES
def ensure_template_render_env():
    pathlib.Path(consts.sublender_library_render_dir).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(consts.sublender_library_render_template_file):
        shutil.copy(consts.packed_sublender_template_file,
                    consts.sublender_library_render_template_file)


def ensure_library_config():
    if not os.path.exists(consts.sublender_library_config_file):
        sync_library()


def ensure_library():
    ensure_template_render_env()
    ensure_library_config()


def load_library():
    with open(consts.sublender_library_config_file, 'r') as f:
        data = json.load(f)
        globalvar.library = data
        generate_preview()


def generate_preview():
    if globalvar.preview_collections is None:
        globalvar.preview_collections = previews.new()
    globalvar.library_preview_enum.clear()
    globalvar.library_category_enum.clear()
    for key in globalvar.library_category_material_map:
        globalvar.library_category_material_map[key].clear()
    category_set = set()
    for i, uu_key in enumerate(globalvar.library["materials"]):
        material = globalvar.library["materials"][uu_key]
        img = material['preview']
        label = material['label']
        if not globalvar.preview_collections.get(img):
            thumb = globalvar.preview_collections.load(img, img, "IMAGE")
        else:
            thumb = globalvar.preview_collections[img]
        globalvar.library_preview_enum.append((uu_key, label, label, thumb.icon_id, i))
        if material.get("category") is not None:
            category_set.add(material.get("category"))
            if globalvar.library_category_material_map.get(material.get("category")) is None:
                globalvar.library_category_material_map[material.get("category")] = []
            globalvar.library_category_material_map[material.get("category")].append(
                (uu_key, label, label, thumb.icon_id, i))
        else:
            globalvar.library_category_material_map["$OTHER$"].append((uu_key, label, label, thumb.icon_id, i))

    globalvar.library_category_enum.append(("$ALL$", "All", "All"))
    for cat in category_set:
        globalvar.library_category_enum.append((cat, cat, cat))
    globalvar.library_category_enum.append(("$OTHER$", "Other", "Other"))


def sync_library():
    with open(consts.sublender_library_config_file, 'w') as f:
        json.dump(globalvar.library, f, indent=2)


def register():
    bpy.utils.register_class(SUBLENDER_OT_Render_Preview_Async)
    bpy.utils.register_class(SUBLENDER_OT_REMOVE_MATERIAL)


def unregister():
    previews.remove(globalvar.preview_collections)
    globalvar.preview_collections = None
    bpy.utils.unregister_class(SUBLENDER_OT_Render_Preview_Async)
    bpy.utils.unregister_class(SUBLENDER_OT_REMOVE_MATERIAL)