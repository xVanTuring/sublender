import json
import pathlib
import shutil
from typing import List

import asyncio
import bpy
import os
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy.utils import previews

from .. import async_loop, utils, parser

default_usage_list = ["baseColor", "metallic", "roughness", "normal"]


def generate_cmd_list(context, target_dir: str, package_path, graph_url, preset_params=None):
    param_list = ["render", "--input", package_path, "--input-graph", graph_url]
    if preset_params is None:
        param_list.append("--set-value")
        param_list.append("$outputsize@9,9")
    else:
        for p in preset_params:
            is_image = p['type'] == parser.sbsarlite.SBSARTypeEnum.IMAGE
            if is_image:
                param_list.append("--set-entry")
            else:
                param_list.append("--set-value")
            param_list.append("{}@{}".format(p["identifier"], p["value"]))

    param_list.append("--output-path")
    pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)
    param_list.append(target_dir)

    engine_value = context.preferences.addons["sublender"].preferences.engine_enum
    if engine_value != "$default$":
        if engine_value != utils.consts.CUSTOM:
            param_list.append('--engine')
            param_list.append(engine_value)
            print("Render engine is {0}".format(engine_value))
        else:
            custom_value = context.preferences.addons["sublender"].preferences.custom_engine
            if custom_value != "":
                param_list.append('--engine')
                param_list.append(custom_value)
                print("Render engine is {0}".format(custom_value))
    else:
        print("Use Default Engine")

    memory_budget = context.preferences.addons["sublender"].preferences.memory_budget
    param_list.append("--memory-budget")
    param_list.append("{0}".format(memory_budget))
    return param_list


class SublenderOTRenderPreviewAsync(async_loop.AsyncModalOperatorMixin, Operator):
    bl_idname = "sublender.render_preview_async"
    bl_label = "Render Preview"
    bl_description = "Render Preview"
    preset_name: StringProperty(default="")
    library_uid: StringProperty(default="")
    engine: StringProperty(default="eevee")
    invert_normal: BoolProperty(default=False)
    cloth_template: BoolProperty(default=False)

    process_list = list()
    task_id = "SublenderOTRenderPreviewAsync"

    def clean(self, _):
        while self.process_list:
            process: asyncio.subprocess.Process = self.process_list.pop()
            if process.returncode is None:
                process.terminate()

    def invoke(self, context, event):

        return async_loop.AsyncModalOperatorMixin.invoke(self, context, event)

    async def render_map(self, cmd_list: List[str]):
        sbs_render_path = bpy.context.preferences.addons["sublender"].preferences.sbs_render
        await self.run_async(sbs_render_path, cmd_list)

    async def render_graph(self, package_path, param_list, pkg_url, is_preset=False, category=""):
        package_info = utils.globalvar.sbsar_dict.get(package_path)
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
        label = ""
        if not is_preset:
            label = current_graph['label']
            if label == "":
                label = bpy.utils.escape_identifier(pkg_url).replace("://", "")
            uu_key = "{}_{}".format(label, package_info["asmuid"])
            existed_material = utils.globalvar.library["materials"].get(uu_key)
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
            blender_file = get_sublender_library_render_dir(utils.consts.sublender_cloth_template_file)
        else:
            blender_file = get_sublender_library_render_dir(utils.consts.sublender_default_template_file)
        if self.invert_normal:
            if self.cloth_template:
                blender_file = get_sublender_library_render_dir(utils.consts.sublender_cloth_template_invert_file)
            else:
                blender_file = get_sublender_library_render_dir(utils.consts.sublender_template_invert_file)

        preview_cmd = ["-b", blender_file, "-o", get_sublender_library_render_dir("out#.png"), "-E"]
        if self.engine == "cycles":
            preview_cmd.append("CYCLES")
        else:
            preview_cmd.append("BLENDER_EEVEE")
        preview_cmd.append("-f")
        preview_cmd.append("1")
        await self.run_async(bpy.app.binary_path, preview_cmd)
        sublender_preview_img_file = get_sublender_library_render_dir("out1.png")
        if not is_preset:
            preview_folder = os.path.join(get_sublender_library_dir(), uu_key, "default")
            pathlib.Path(preview_folder).mkdir(parents=True, exist_ok=True)
            copied_img = shutil.copy(sublender_preview_img_file, os.path.join(preview_folder, "preview.png"))
            copied_sbsar = shutil.copy(package_path, pathlib.Path(preview_folder, "../").resolve())
            utils.globalvar.library["materials"][uu_key] = {
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
            preview_folder = os.path.join(get_sublender_library_dir(), uu_key, self.preset_name)
            pathlib.Path(preview_folder).mkdir(parents=True, exist_ok=True)
            copied_img = shutil.copy(sublender_preview_img_file, os.path.join(preview_folder, "preview.png"))
            if utils.globalvar.preview_collections.get(copied_img) is not None:
                del utils.globalvar.preview_collections[copied_img]
            utils.globalvar.library["materials"].get(
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
        # start = datetime.datetime.now()
        target_dir = get_sublender_library_render_dir()
        if self.preset_name != "":
            material_info = utils.globalvar.library["materials"].get(self.library_uid)
            package_path = material_info["sbsar_path"]
            preset_info = material_info["presets"][self.preset_name]
            preset_parameters = preset_info["values"]
            param_list = generate_cmd_list(context,
                                           target_dir,
                                           package_path,
                                           material_info["pkg_url"],
                                           preset_params=preset_parameters)
            await self.render_graph(package_path, param_list, material_info["pkg_url"], is_preset=True)
        else:
            if utils.globalvar.consumer_started:
                return
            utils.globalvar.consumer_started = True
            while True:
                if utils.globalvar.queue.empty():
                    utils.globalvar.consumer_started = False
                    break
                importing_graph_list = await utils.globalvar.queue.get()
                for importing_graph in importing_graph_list:
                    package_path = importing_graph["package_path"]
                    param_list = generate_cmd_list(context, target_dir, package_path, importing_graph["graph_url"])
                    category = importing_graph["category"]
                    graph_url = importing_graph["graph_url"]
                    uu_key, current_graph = await self.render_graph(package_path,
                                                                    param_list,
                                                                    graph_url,
                                                                    category=category)
                    if uu_key is None or current_graph is None:
                        return

                    for preset_name in importing_graph["presets"]:
                        self.preset_name = preset_name
                        self.library_uid = uu_key
                        preset_params = current_graph['presets'].get(preset_name)['inputs']
                        utils.globalvar.library["materials"].get(uu_key)["presets"][preset_name] = {
                            "name": preset_name,
                            "values": preset_params,
                            "preview": ""
                        }
                        param_list = generate_cmd_list(context,
                                                       target_dir,
                                                       package_path,
                                                       graph_url,
                                                       preset_params=preset_params)
                        self.report({'INFO'}, "Importing Preset {}".format(preset_name))
                        await self.render_graph(package_path, param_list, graph_url, is_preset=True)
                # end = datetime.datetime.now()
                # https://blender.stackexchange.com/a/30613
                for region in context.area.regions:
                    if region.type == "UI":
                        region.tag_redraw()
                        break
                # self.report({"INFO"}, "Render Done! Time spent: {0}s.".format((end - start).total_seconds()))


class SublenderOTRemoveMaterial(Operator):
    # TODO error after removing
    bl_idname = "sublender.remove_material"
    bl_label = "Remove"
    bl_description = "Remove selected material"

    def execute(self, context):
        library_preference = context.scene.sublender_library
        prev_category = library_preference.categories
        active_material = library_preference.active_material
        del utils.globalvar.library["materials"][active_material]
        sync_library()
        generate_preview()
        if prev_category != library_preference.categories:
            # Last material in that material had been removed, reset to All
            library_preference.categories = "$ALL$"
        # Check Material index existence, reset to first
        current_mat_list = utils.globalvar.library_category_material_map.get(library_preference.categories, [])
        library_len = len(current_mat_list)
        if 0 < library_len <= context.scene['sublender_library']['active_material']:
            context.scene.sublender_library.active_material = current_mat_list[0][0]
        shutil.rmtree(os.path.join(get_sublender_library_dir(), active_material))
        return {'FINISHED'}


class SublenderOTSaveAsPreset(Operator):
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
        graph_source = utils.globalvar.library["materials"].get(self.library_uid)

        temp_name = "Preset"
        self.preset_name = safe_name(temp_name, graph_source["presets"].keys())
        return wm.invoke_props_dialog(self)

    def draw(self, _):
        self.layout.prop(self, "preset_name")

    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        self.library_uid = mat.sublender.library_uid
        utils.globalvar.library["materials"].get(self.library_uid)["presets"][self.preset_name] = generate_preset(
            self.preset_name, self.material_name)
        bpy.ops.sublender.render_preview_async(library_uid=self.library_uid, preset_name=self.preset_name)
        return {'FINISHED'}


class SublenderOTApplyPreset(Operator):
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
        if len(utils.globalvar.library_material_preset_map.get(active_material)) > 0:
            active_preset_name = library_properties.material_preset
        utils.globalvar.applying_preset = True
        utils.reset_material(current_material)
        if active_preset_name != "$DEFAULT$":
            utils.apply_preset(current_material, active_preset_name)
        utils.globalvar.applying_preset = False
        # Manually update
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name='')
        return {'FINISHED'}


class SublenderOTSaveToPreset(Operator):
    bl_idname = "sublender.save_to_preset"
    bl_label = "Save to Preset"
    bl_description = "Save current parameters to Preset"

    def execute(self, context):
        current_material = utils.find_active_mat(context)
        library_properties = context.scene.sublender_library
        active_material = library_properties.active_material
        if len(utils.globalvar.library_material_preset_map.get(active_material)) == 0:
            return
        active_preset_name = library_properties.material_preset
        bpy.ops.sublender.save_as_preset(material_name=current_material.name, preset_name=active_preset_name)
        return {'FINISHED'}


class SublenderOTReleaseLibraryTemplate(Operator):
    bl_idname = "sublender.release_lib_template"
    bl_label = "Release Library Template"
    bl_description = "Release Library Template"

    def execute(self, context):
        old_version = bpy.context.preferences.addons["sublender"].preferences.old_version_of_template
        ensure_template_render_env(old=old_version, force=True)
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

    clss_info = utils.globalvar.graph_clss.get(clss_name)
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


def ensure_template_render_env(old=False, force=False):
    sublender_library_dir = bpy.context.preferences.addons["sublender"].preferences.library_path
    sublender_library_render_dir = os.path.join(sublender_library_dir, "template")
    pathlib.Path(sublender_library_render_dir).mkdir(parents=True, exist_ok=True)

    sublender_library_render_template_file = os.path.join(sublender_library_render_dir, "preview_template.blend")
    sublender_library_render_template_invert_file = os.path.join(sublender_library_render_dir,
                                                                 "preview_template_invert.blend")

    sublender_library_render_cloth_template_file = os.path.join(sublender_library_render_dir,
                                                                "preview_cloth_template.blend")
    sublender_library_render_cloth_template_invert_file = os.path.join(sublender_library_render_dir,
                                                                       "preview_cloth_template_invert.blend")
    if force or not os.path.exists(sublender_library_render_template_file):
        shutil.copy(utils.consts.get_template("shader_ball", False, old), sublender_library_render_template_file)
    if force or not os.path.exists(sublender_library_render_template_invert_file):
        shutil.copy(utils.consts.get_template("shader_ball", True, old), sublender_library_render_template_invert_file)
    if force or not os.path.exists(sublender_library_render_cloth_template_file):
        shutil.copy(utils.consts.get_template("cloth", False, old), sublender_library_render_cloth_template_file)
    if force or not os.path.exists(sublender_library_render_cloth_template_invert_file):
        shutil.copy(utils.consts.get_template("cloth", True, old), sublender_library_render_cloth_template_invert_file)


def ensure_library_config():
    if not os.path.exists(get_sublender_library_config_file()):
        sync_library()


def ensure_library():
    ensure_template_render_env()
    ensure_library_config()


def load_library():
    with open(get_sublender_library_config_file(), 'r') as f:
        data = json.load(f)
        utils.globalvar.library = data
        generate_preview()


def get_sublender_library_config_file():
    return os.path.join(get_sublender_library_dir(), "config.json")


def get_sublender_library_dir():
    return bpy.context.preferences.addons["sublender"].preferences.library_path


def get_sublender_library_render_dir(append=None):
    if append is None:
        return os.path.join(get_sublender_library_dir(), "template")
    else:
        return os.path.join(get_sublender_library_dir(), "template", append)


def generate_preview():
    if utils.globalvar.preview_collections is None:
        utils.globalvar.preview_collections = previews.new()
    utils.globalvar.library_category_enum.clear()
    for key in utils.globalvar.library_category_material_map:
        utils.globalvar.library_category_material_map[key].clear()
    category_set = set()
    for i, uu_key in enumerate(sorted(utils.globalvar.library["materials"].keys())):
        material = utils.globalvar.library["materials"][uu_key]
        img = material['preview']
        label = material['label']
        if not utils.globalvar.preview_collections.get(img):
            thumb = utils.globalvar.preview_collections.load(img, img, "IMAGE")
        else:
            thumb = utils.globalvar.preview_collections[img]
        utils.globalvar.library_category_material_map["$ALL$"].append((uu_key, label, label, thumb.icon_id, i))
        utils.globalvar.library_material_preset_map[uu_key] = []
        if len(material.get("presets", {})) > 0:
            utils.globalvar.library_material_preset_map[uu_key].append(
                ("$DEFAULT$", "Default", "Default", thumb.icon_id, 0))
            p_i = 1
            for p_key in material.get("presets", {}):
                preset = material["presets"][p_key]
                preset_img = preset["preview"]
                if not utils.globalvar.preview_collections.get(preset_img):
                    preset_thumb = utils.globalvar.preview_collections.load(preset_img, preset_img, "IMAGE")
                else:
                    preset_thumb = utils.globalvar.preview_collections[preset_img]
                utils.globalvar.library_material_preset_map[uu_key].append(
                    (p_key, p_key, p_key, preset_thumb.icon_id, p_i))
                p_i += 1

        if material.get("category") is not None and material.get("category") != "":
            category_set.add(material.get("category"))
            if utils.globalvar.library_category_material_map.get(material.get("category")) is None:
                utils.globalvar.library_category_material_map[material.get("category")] = []
            material_tuple: utils.globalvar.MaterialTuple = (uu_key, label, label, thumb.icon_id, i)
            utils.globalvar.library_category_material_map[material.get("category")].append(material_tuple)
        else:
            utils.globalvar.library_category_material_map["$OTHER$"].append((uu_key, label, label, thumb.icon_id, i))

    utils.globalvar.library_category_enum.append(
        ("$ALL$", "All - {}".format(len(utils.globalvar.library_category_material_map["$ALL$"])), "All"))
    for cat in sorted(category_set):
        utils.globalvar.library_category_enum.append(
            (cat, "{} - {}".format(cat, len(utils.globalvar.library_category_material_map[cat])), cat))
    utils.globalvar.library_category_enum.append(
        ("$OTHER$", "Other - {}".format(len(utils.globalvar.library_category_material_map["$OTHER$"])), "Other"))


def sync_library():
    with open(get_sublender_library_config_file(), 'w') as f:
        json.dump(utils.globalvar.library, f, indent=2)


cls_list = [
    SublenderOTRenderPreviewAsync, SublenderOTRemoveMaterial, SublenderOTSaveAsPreset, SublenderOTApplyPreset,
    SublenderOTSaveToPreset, SublenderOTReleaseLibraryTemplate
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    if utils.globalvar.preview_collections:
        previews.remove(utils.globalvar.preview_collections)
    utils.globalvar.preview_collections = None
    for cls in cls_list:
        bpy.utils.unregister_class(cls)
