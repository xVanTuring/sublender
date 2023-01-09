import datetime
import json
import pathlib
import shutil
from typing import List

import asyncio
import bpy
import os
import sys
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy.utils import previews

from . import consts, async_loop, utils, globalvar

default_usage_list = ["baseColor", "metallic", "roughness", "normal"]


def generate_cmd_list(context, target_dir: str, package_path, graph_url, preset_params=None):
    param_list = ["render", "--input", package_path, "--input-graph", graph_url]
    if preset_params is None:
        param_list.append("--set-value")
        param_list.append("$outputsize@9,9")
    else:
        for p in preset_params:
            is_image = p['type'] == consts.SBSARTypeEnum.IMAGE
            if is_image:
                param_list.append("--set-entry")
            else:
                param_list.append("--set-value")
            param_list.append("{}@{}".format(p["identifier"], p["value"]))

    param_list.append("--output-path")
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


class SUBLENDER_OT_Render_Preview_Async(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.render_preview_async"
    bl_label = "Render Preview"
    bl_description = "Render Preview"
    package_path: StringProperty(default="")
    preset_name: StringProperty(default="")
    library_uid: StringProperty(default="")
    engine: StringProperty(default="eevee")
    invert_normal: BoolProperty(default=False)
    cloth_template: BoolProperty(default=False)

    process_list = list()

    def clean(self, _):
        while self.process_list:
            process: asyncio.subprocess.Process = self.process_list.pop()
            if process.returncode is None:
                process.terminate()

    def invoke(self, context, event):
        if self.package_path == "" and self.preset_name == "":
            self.report({"WARNING"}, "No Graph/Preset is selected or given")
            return {"CANCELLED"}
        self.task_id = self.package_path
        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str]):
        sbs_render_path = bpy.context.preferences.addons[__package__].preferences.sbs_render
        await self.run_async(sbs_render_path, cmd_list)

    async def render_graph(self, param_list, pkg_url, is_preset=False, category=""):
        package_info = globalvar.sbsar_dict.get(self.package_path)
        current_graph = None
        build_list = []
        for graph in package_info['graphs']:
            if graph['pkgUrl'] == pkg_url:
                current_graph = graph
                _, _, output_usage_dict = utils.graph_output_parse(graph['outputs'])
                for usage in output_usage_dict:
                    if usage in default_usage_list:
                        build_list.append((output_usage_dict[usage][0], usage))
                break
        if not is_preset:
            label = current_graph['label']
            if label == "":
                label = bpy.utils.escape_identifier(pkg_url).replace("://", "")
            uu_key = "{}_{}".format(label, package_info["asmuid"])
            existed_material = globalvar.library["materials"].get(uu_key)
            if existed_material is not None:
                self.report({"WARNING"}, "Package has already been imported!")
                return None, None
        else:
            uu_key = self.library_uid

        worker_list = []
        for output in build_list:
            per_output_cmd = param_list[:]
            per_output_cmd.append("--input-graph-output")
            per_output_cmd.append(output[0])
            per_output_cmd.append("--output-name")
            per_output_cmd.append(output[1])
            worker_list.append(self.render_map(per_output_cmd))

        await asyncio.gather(*worker_list)
        if self.cloth_template:
            blender_file = consts.sublender_library_render_cloth_template_file
        else:
            blender_file = consts.sublender_library_render_template_file
        if self.invert_normal:
            if self.cloth_template:
                blender_file = consts.sublender_library_render_cloth_template_invert_file
            else:
                blender_file = consts.sublender_library_render_template_invert_file

        preview_cmd = ["-b", blender_file, "-o", consts.sublender_preview_img_template_file, "-E"]
        if self.engine == "cycles":
            preview_cmd.append("CYCLES")
        else:
            preview_cmd.append("BLENDER_EEVEE")
        preview_cmd.append("-f")
        preview_cmd.append("1")
        await self.run_async(sys.executable, preview_cmd)
        if not is_preset:
            preview_folder = os.path.join(consts.sublender_library_dir, uu_key, "default")
            pathlib.Path(preview_folder).mkdir(parents=True, exist_ok=True)
            copied_img = shutil.copy(consts.sublender_preview_img_file,
                                     os.path.join(preview_folder, "preview.png"))
            copied_sbsar = shutil.copy(self.package_path, pathlib.Path(preview_folder, "../").resolve())
            globalvar.library["materials"][uu_key] = {
                "label": label,
                "sbsar_path": copied_sbsar,
                "preview": copied_img,
                "pkg_url": current_graph['pkgUrl'],
                "ar_uid": package_info["asmuid"],
                "category": category,
                "description": current_graph["description"],
                "presets": {}
            }
        else:
            preview_folder = os.path.join(consts.sublender_library_dir, uu_key, self.preset_name)
            pathlib.Path(preview_folder).mkdir(parents=True, exist_ok=True)
            copied_img = shutil.copy(consts.sublender_preview_img_file,
                                     os.path.join(preview_folder, "preview.png"))
            if globalvar.preview_collections.get(copied_img) is not None:
                del globalvar.preview_collections[copied_img]
            globalvar.library["materials"].get(
                self.library_uid)["presets"][self.preset_name]["preview"] = copied_img

        sync_library()
        generate_preview()
        return uu_key, current_graph

    async def run_async(self, exec_path: str, cmd_list: List[str]):
        process = await asyncio.create_subprocess_exec(exec_path, *cmd_list, stdout=asyncio.subprocess.PIPE)
        self.process_list.append(process)
        await process.wait()

    async def async_execute(self, context):
        ensure_library()
        start = datetime.datetime.now()
        target_dir = consts.sublender_library_render_dir
        if self.preset_name != "":
            material_info = globalvar.library["materials"].get(self.library_uid)
            self.package_path = material_info["sbsar_path"]
            preset_info = material_info["presets"][self.preset_name]
            preset_parameters = preset_info["values"]
            param_list = generate_cmd_list(context,
                                           target_dir,
                                           self.package_path,
                                           material_info["pkg_url"],
                                           preset_params=preset_parameters)
            await self.render_graph(param_list, material_info["pkg_url"], is_preset=True)
        else:
            for importing_graph in context.scene.sublender_library.importing_graphs:
                if not importing_graph.enable:
                    continue

                param_list = generate_cmd_list(context, target_dir, self.package_path,
                                               importing_graph.graph_url)
                uu_key, current_graph = await self.render_graph(param_list,
                                                                importing_graph.graph_url,
                                                                category=importing_graph.category)

                if uu_key is None or current_graph is None:
                    return

                for preset in importing_graph.importing_presets:
                    if not preset.enable:
                        continue
                    self.preset_name = preset.name
                    self.library_uid = uu_key
                    preset_params = current_graph['presets'].get(preset.name)['inputs']
                    globalvar.library["materials"].get(uu_key)["presets"][preset.name] = {
                        "name": preset.name,
                        "values": preset_params,
                        "preview": ""
                    }
                    param_list = generate_cmd_list(context,
                                                   target_dir,
                                                   self.package_path,
                                                   importing_graph.graph_url,
                                                   preset_params=preset_params)
                    self.report({'INFO'}, "Importing Preset {}".format(preset.name))
                    await self.render_graph(param_list, importing_graph.graph_url, is_preset=True)

        end = datetime.datetime.now()
        # https://blender.stackexchange.com/a/30613
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
                break
        self.report({"INFO"}, "Render Done! Time spent: {0}s.".format((end - start).total_seconds()))


# FIXME: error after removing material under external category
class SUBLENDER_OT_REMOVE_MATERIAL(Operator):
    bl_idname = "sublender.remove_material"
    bl_label = "Remove"
    bl_description = "Remove selected material"

    def execute(self, context):
        active_material = context.scene.sublender_library.active_material
        del globalvar.library["materials"][active_material]
        sync_library()
        generate_preview()
        library_len = len(globalvar.library_category_material_map["$ALL$"])
        if 0 < library_len <= context.scene['sublender_library']['active_material']:
            context.scene['sublender_library']['active_material'] = library_len - 1
        shutil.rmtree(os.path.join(consts.sublender_library_dir, active_material))
        return {'FINISHED'}


def safe_name(name: str, exists):
    for existed_name in exists:
        if existed_name == name:
            try:
                base, suffix = name.rsplit('.', 1)
                num = int(suffix, 10)
                name = base + "." + '%03d' % (num + 1)
            except ValueError:
                name = name + ".001"
    return name


def generate_preset(preset_name: str, material_name: str):
    material_inst = bpy.data.materials.get(material_name)
    m_sublender = material_inst.sublender
    clss_name = utils.gen_clss_name(m_sublender.graph_url)

    clss_info = globalvar.graph_clss.get(clss_name)
    input_list = clss_info['input']
    graph_setting = getattr(material_inst, clss_name)
    preset_parameters = []
    for input_info in input_list:
        if input_info['identifier'] != '$outputsize' and input_info['identifier'] != '$randomseed':
            is_image = input_info['type'] == 5
            value = graph_setting.get(input_info['prop'])
            if value is not None:
                if input_info.get('enum_items') is not None:
                    value = input_info.get('enum_items')[value][0]
                if is_image and value == "":
                    continue
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
                preset_parameters.append({
                    "identifier": input_info['identifier'],
                    "value": value,
                    "type": input_info['type'],
                    "prop": input_info['prop']
                })
    preset_config = {"name": preset_name, "values": preset_parameters, "preview": ""}
    return preset_config


class SUBLENDER_OT_SAVE_AS_PRESET(Operator):
    bl_idname = "sublender.save_as_preset"
    bl_label = "Save as Preset"
    bl_description = "Save current material as a preset"
    material_name: StringProperty()
    preset_name: StringProperty(default="Preset", name="Preset Name")
    library_uid = None

    def invoke(self, context, _):
        wm = context.window_manager
        mat = bpy.data.materials.get(self.material_name)
        self.library_uid = mat.sublender.library_uid
        graph_source = globalvar.library["materials"].get(self.library_uid)

        temp_name = "Preset"
        self.preset_name = safe_name(temp_name, graph_source["presets"].keys())
        return wm.invoke_props_dialog(self)

    def draw(self, _):
        self.layout.prop(self, "preset_name")

    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        self.library_uid = mat.sublender.library_uid
        globalvar.library["materials"].get(self.library_uid)["presets"][self.preset_name] \
            = generate_preset(self.preset_name, self.material_name)
        bpy.ops.sublender.render_preview_async(library_uid=self.library_uid, preset_name=self.preset_name)
        return {'FINISHED'}


class SUBLENDER_OT_APPLY_PRESET(Operator):
    bl_idname = "sublender.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply preset to selected instance"

    # @classmethod
    # def poll(cls, context):
    #     return False

    def execute(self, context):
        current_material = utils.find_active_mat(context)
        library_properties = context.scene.sublender_library
        active_material = library_properties.active_material
        active_preset_name = "$DEFAULT$"
        if len(globalvar.library_material_preset_map.get(active_material)) > 0:
            active_preset_name = library_properties.material_preset
        globalvar.applying_preset = True
        utils.reset_material(current_material)
        if active_preset_name != "$DEFAULT$":
            utils.apply_preset(current_material, active_preset_name)
        globalvar.applying_preset = False
        # Manually update
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name='')
        return {'FINISHED'}


class SUBLENDER_OT_SAVE_TO_PRESET(Operator):
    bl_idname = "sublender.save_to_preset"
    bl_label = "Save to Preset"
    bl_description = "Save current parameters to Preset"

    def execute(self, context):
        current_material = utils.find_active_mat(context)
        library_properties = context.scene.sublender_library
        active_material = library_properties.active_material
        if len(globalvar.library_material_preset_map.get(active_material)) == 0:
            return
        active_preset_name = library_properties.material_preset
        bpy.ops.sublender.save_as_preset(material_name=current_material.name, preset_name=active_preset_name)
        return {'FINISHED'}


def ensure_template_render_env():
    pathlib.Path(consts.sublender_library_render_dir).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(consts.sublender_library_render_template_file):
        shutil.copy(consts.packed_sublender_template_file, consts.sublender_library_render_template_file)
    if not os.path.exists(consts.sublender_library_render_template_invert_file):
        shutil.copy(consts.packed_sublender_template_invert_file,
                    consts.sublender_library_render_template_invert_file)
    if not os.path.exists(consts.sublender_library_render_cloth_template_file):
        shutil.copy(consts.packed_sublender_template_cloth_file,
                    consts.sublender_library_render_cloth_template_file)
    if not os.path.exists(consts.sublender_library_render_cloth_template_invert_file):
        shutil.copy(consts.packed_sublender_template_cloth_invert_file,
                    consts.sublender_library_render_cloth_template_invert_file)


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
        globalvar.library_category_material_map["$ALL$"].append((uu_key, label, label, thumb.icon_id, i))
        globalvar.library_material_preset_map[uu_key] = []
        if len(material.get("presets", {})) > 0:
            globalvar.library_material_preset_map[uu_key].append(
                ("$DEFAULT$", "Default", "Default", thumb.icon_id, 0))
            p_i = 1
            for p_key in material.get("presets", {}):
                preset = material["presets"][p_key]
                preset_img = preset["preview"]
                if not globalvar.preview_collections.get(preset_img):
                    preset_thumb = globalvar.preview_collections.load(preset_img, preset_img, "IMAGE")
                else:
                    preset_thumb = globalvar.preview_collections[preset_img]
                globalvar.library_material_preset_map[uu_key].append(
                    (p_key, p_key, p_key, preset_thumb.icon_id, p_i))
                p_i += 1

        if material.get("category") is not None and material.get("category") != "":
            category_set.add(material.get("category"))
            if globalvar.library_category_material_map.get(material.get("category")) is None:
                globalvar.library_category_material_map[material.get("category")] = []
            globalvar.library_category_material_map[material.get("category")].append(
                (uu_key, label, label, thumb.icon_id, i))
        else:
            globalvar.library_category_material_map["$OTHER$"].append(
                (uu_key, label, label, thumb.icon_id, i))

    for key in globalvar.library_category_material_map:
        globalvar.library_category_material_map[key].sort()

    globalvar.library_category_enum.append(
        ("$ALL$", "All - {}".format(len(globalvar.library_category_material_map["$ALL$"])), "All"))
    for cat in sorted(category_set):
        globalvar.library_category_enum.append(
            (cat, "{} - {}".format(cat, len(globalvar.library_category_material_map[cat])), cat))
    globalvar.library_category_enum.append(
        ("$OTHER$", "Other - {}".format(len(globalvar.library_category_material_map["$OTHER$"])), "Other"))


def sync_library():
    with open(consts.sublender_library_config_file, 'w') as f:
        json.dump(globalvar.library, f, indent=2)


def register():
    bpy.utils.register_class(SUBLENDER_OT_Render_Preview_Async)
    bpy.utils.register_class(SUBLENDER_OT_REMOVE_MATERIAL)
    bpy.utils.register_class(SUBLENDER_OT_SAVE_AS_PRESET)
    bpy.utils.register_class(SUBLENDER_OT_APPLY_PRESET)
    bpy.utils.register_class(SUBLENDER_OT_SAVE_TO_PRESET)


def unregister():
    previews.remove(globalvar.preview_collections)
    globalvar.preview_collections = None
    bpy.utils.unregister_class(SUBLENDER_OT_Render_Preview_Async)
    bpy.utils.unregister_class(SUBLENDER_OT_REMOVE_MATERIAL)
    bpy.utils.unregister_class(SUBLENDER_OT_SAVE_AS_PRESET)
    bpy.utils.unregister_class(SUBLENDER_OT_APPLY_PRESET)
    bpy.utils.unregister_class(SUBLENDER_OT_SAVE_TO_PRESET)
