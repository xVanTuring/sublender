from . import consts
from . import install_lib
from . import globalvar
import asyncio
import os
import pathlib
import tempfile
import uuid

import bpy
import mathutils
from bpy.props import (BoolProperty, EnumProperty)
from bpy.utils import register_class
from bpy.props import (StringProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)
from .. import settings, parser, ui


def sbsar_input_updated(_, context):
    if context.scene.sublender_settings.live_update and not globalvar.applying_preset:
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name='')


def sbsar_output_updated_name(sbs_id: str):
    def sbsar_output_updated(self, _):
        prop_name = sb_output_to_prop(sbs_id)
        if getattr(self, consts.SBS_CONFIGURED) and getattr(self, prop_name):
            bpy.ops.sublender.render_texture_async(texture_name=sbs_id, importing_graph=False)

    return sbsar_output_updated


def gen_image_name(material_name, output_info):
    if len(output_info['usages']) > 0:
        return '{0}_{1}'.format(material_name, output_info['usages'][0])
    else:
        graph_identifier = output_info['name']
        return '{0}_{1}'.format(material_name, graph_identifier)


class VectorWrapper(object):
    def __init__(self, vec):
        self.vec = vec

    @property
    def x(self):
        return self.vec[0]

    @property
    def y(self):
        return self.vec[1]

    @property
    def z(self):
        return self.vec[2]

    @property
    def w(self):
        return self.vec[3]


class EvalDelegate(object):
    material_name = ""
    clss_name = ""

    def __init__(self, material_name, clss_name):
        self.material_name = material_name
        self.clss_name = clss_name

    def __getitem__(self, identifier: str):
        sbs_graph = globalvar.graph_clss.get(self.clss_name, {}).get('sbs_graph')

        graph_setting = getattr(bpy.data.materials.get(self.material_name), self.clss_name)
        if identifier == "$outputsize":
            if getattr(graph_setting, consts.output_size_lock):
                return VectorWrapper([
                    int(getattr(graph_setting, consts.output_size_x)),
                    int(getattr(graph_setting, consts.output_size_x))
                ])
            else:
                return VectorWrapper([
                    int(getattr(graph_setting, consts.output_size_x)),
                    int(getattr(graph_setting, consts.output_size_y))
                ])
        prop_name = None

        for i in sbs_graph['inputs']:
            if i['identifier'] == identifier:
                prop_name = parser.uid_prop(i['uid'])
        if prop_name is None:
            return False
        value = getattr(graph_setting, prop_name, None)
        if isinstance(value, mathutils.Color) or isinstance(value, bpy.types.bpy_prop_array):
            return VectorWrapper(value)
        if isinstance(value, str) and value.startswith("$NUM:"):
            value = int(value.replace("$NUM:", ""))
        return value


def new_material_name(material_name: str) -> str:
    """Make Sure No Name Conflict"""
    for mat in bpy.data.materials:
        name: str = mat.name
        if name == material_name:
            try:
                base, suffix = name.rsplit('.', 1)
                num = int(suffix, 10)
                material_name = base + "." + '%03d' % (num + 1)
            except ValueError:
                material_name = material_name + ".001"

    return material_name


def output_size_x_updated(self, context):
    if getattr(self, consts.output_size_lock) and \
            getattr(self, consts.output_size_y) != getattr(self,
                                                           consts.output_size_x):
        setattr(self, consts.output_size_y, getattr(self, consts.output_size_x))
        if getattr(self, consts.update_when_sizing):
            sbsar_input_updated(self, context)


def substance_group_to_toggle_name(name: str) -> str:
    return "sb_{0}_gptl".format(bpy.path.clean_name(str(hash(name))))


def sb_output_to_prop(uid: str):
    return "sbo_{0}".format(uid)


def sb_output_format_to_prop(uid: str):
    return "sbo_format_{0}".format(uid)


def sb_output_dep_to_prop(uid: str):
    return "sbo_dep_{0}".format(uid)


def gen_clss_name(graph_url: str):
    return "sb" + graph_url.replace("pkg://", "_")


def sub_panel_name(group_key: str, graph_url: str):
    return "SBS_PT_k{0}".format(str(hash(group_key + graph_url)).replace('-', '_'))


def generate_sub_panel(group_map, graph_url):
    for group_key in group_map.keys():
        cur_group = group_map.get(group_key)
        group_name_map = {'$UNGROUPED$': 'Parameters'}
        displace_name = group_name_map.get(cur_group['nameInShort'], cur_group['nameInShort'])
        parent_name = '/'.join(group_key.split('/')[:-1])
        bl_parent_id = ''
        if parent_name != '':
            bl_parent_id = sub_panel_name(parent_name, graph_url)
        p_clss = type(sub_panel_name(group_key, graph_url), (ui.Sublender_Prop_BasePanel, ), {
            'bl_label': displace_name,
            'bl_parent_id': bl_parent_id,
            'graph_url': graph_url,
            'group_info': cur_group
        })
        register_class(p_clss)
        globalvar.sub_panel_clss_list.append(p_clss)


sbsar_type_to_property = [
    (
        FloatProperty,
        None,
    ),
    (
        FloatVectorProperty,
        2,
    ),
    (
        FloatVectorProperty,
        3,
    ),
    (
        FloatVectorProperty,
        4,
    ),
    (IntProperty, None),
    (StringProperty, None),
    (StringProperty, None),
    (None, None),
    (IntVectorProperty, 2),
    (IntVectorProperty, 3),
    (IntVectorProperty, 4),
]

format_list = [
    ("png", "PNG", "PNG"),
    ("jpg", "JPG", "JPG"),
    ("tiff", "TIFF", "TIFF"),
    ("hdr", "HDR", "HDR"),
    ("exr", "EXR", "EXR"),
]
output_bit_depth = [
    ("0", "Default", "Default"),
    ("8", "Int 8", "Int 8"),
    ("16", "Int 16", "Int 16"),
    ("16f", "Float 16", "Float 16"),
    ("32f", "Float 32", "Float 32"),
]


def dynamic_gen_clss_graph(sbs_graph, graph_url: str):
    clss_name = gen_clss_name(graph_url)
    if globalvar.graph_clss.get(clss_name) is None:
        all_inputs = sbs_graph['inputs']
        all_outputs = sbs_graph['outputs']
        _anno_obj = {}
        prop_input_map = {}

        def assign(obj_from, obj_to, m_prop_name: str):
            if obj_from.get(m_prop_name) is not None:
                obj_to[m_prop_name] = obj_from.get(m_prop_name)

        for input_info in all_inputs:
            (prop_type, prop_size) = sbsar_type_to_property[input_info['type']]
            _anno_item = {}

            prop_input_map[input_info["prop"]] = input_info
            if prop_size is not None:
                _anno_item['size'] = prop_size
            assign(input_info, _anno_item, 'default')
            assign(input_info, _anno_item, 'min')
            assign(input_info, _anno_item, 'max')
            assign(input_info, _anno_item, 'step')
            if input_info['type'] == parser.sbsarlite.SBSARTypeEnum.INTEGER1:
                if input_info.get('widget') == 'togglebutton':
                    prop_type = BoolProperty
                if input_info.get('widget') == 'combobox' and input_info.get('combo_items') is not None:
                    prop_type = EnumProperty
                    _anno_item['items'] = input_info.get('combo_items')
            if input_info['type'] == parser.sbsarlite.SBSARTypeEnum.IMAGE:
                _anno_item['subtype'] = 'FILE_PATH'
            if input_info['type'] in [parser.sbsarlite.SBSARTypeEnum.FLOAT3, parser.sbsarlite.SBSARTypeEnum.FLOAT4]:
                if input_info.get('widget') == 'color':
                    _anno_item['min'] = 0
                    _anno_item['max'] = 1
                    _anno_item['subtype'] = 'COLOR'

            _anno_item['update'] = sbsar_input_updated
            if input_info['identifier'] == '$outputsize':
                preferences = bpy.context.preferences
                addon_prefs = preferences.addons["sublender"].preferences
                _anno_obj[consts.output_size_x] = (EnumProperty, {
                    'items': consts.output_size_one_enum,
                    'default': addon_prefs.output_size_x,
                    'update': output_size_x_updated,
                })
                _anno_obj[consts.output_size_y] = (
                    EnumProperty,
                    {
                        'items': consts.output_size_one_enum,
                        'default': addon_prefs.output_size_x,
                        # 'update': output_size_x_updated,
                    })
                _anno_obj[consts.output_size_lock] = (BoolProperty, {
                    'default': addon_prefs.output_size_lock,
                    'update': output_size_x_updated
                })
                _anno_obj[consts.update_when_sizing] = (BoolProperty, {
                    'name': "Update texture when change size",
                    'default': True
                })
            else:
                _anno_obj[input_info['prop']] = (prop_type, _anno_item)

        def parse_output(_output):
            _anno_obj[sb_output_to_prop(_output['identifier'])] = (BoolProperty, {
                'name':
                _output['label'],
                'default':
                False,
                'update':
                sbsar_output_updated_name(_output['identifier'])
            })
            _anno_obj[sb_output_format_to_prop(_output['identifier'])] = (EnumProperty, {
                'name': 'Format',
                'items': format_list,
                'default': 'png'
            })
            _anno_obj[sb_output_dep_to_prop(_output['identifier'])] = (EnumProperty, {
                'name': 'Bit Depth',
                'items': output_bit_depth,
                'default': '0'
            })

        output_list_dict, output_list, output_usage_dict = graph_output_parse(all_outputs, parse_output)

        group_tree, group_map = parser.parse_sbsar_group(sbs_graph)
        generate_sub_panel(group_map, graph_url)
        _anno_obj[consts.SBS_CONFIGURED] = (BoolProperty, {
            'name': "SBS Configured",
            'default': False,
        })
        clss = type(clss_name, (bpy.types.PropertyGroup, ), {'__annotations__': _anno_obj})
        register_class(clss)

        globalvar.graph_clss[clss_name] = {
            'clss': clss,
            'input': all_inputs,
            'prop_input_map': prop_input_map,
            'group_info': {
                'tree': group_tree,
                'map': group_map
            },
            'output_info': {
                'list': output_list,
                'dict': output_list_dict,
                'usage': output_usage_dict
            },
            'sbs_graph': sbs_graph,
        }
        setattr(bpy.types.Material, clss_name, bpy.props.PointerProperty(type=clss))

    return clss_name, globalvar.graph_clss.get(clss_name)


def graph_output_parse(outputs, exec_per=None):
    output_list_dict = {}
    output_list = []
    output_usage_dict = {}
    for output in outputs:
        if exec_per is not None:
            exec_per(output)
        usages = output['usages']
        output_graph = {
            'name': output['identifier'],
            'usages': usages,
            'label': output['label'],
            'uid': output['uid'],
        }
        output_list_dict[output['identifier']] = output_graph
        output_list.append(output_graph)
        for usage in usages:
            if output_usage_dict.get(usage) is None:
                output_usage_dict[usage] = []
            output_usage_dict[usage].append(output['identifier'])
    return output_list_dict, output_list, output_usage_dict


async def gen_clss_from_material_async(target_material, enable_visible_if, force_reload=False, report=None):
    m_sublender = target_material.sublender
    if force_reload:
        await load_sbsar_to_dict_async(m_sublender.package_path)
    sbs_package = globalvar.sbsar_dict.get(m_sublender.package_path)

    if sbs_package is not None:
        sbs_graph = None
        for graph in sbs_package['graphs']:
            if graph['pkgUrl'] == m_sublender.graph_url:
                sbs_graph = graph
        clss_name, _ = dynamic_gen_clss_graph(sbs_graph, m_sublender.graph_url)
        m_sublender.package_missing = False
        if enable_visible_if:
            globalvar.eval_delegate_map[target_material.name] = EvalDelegate(target_material.name, clss_name)
        graph_setting = getattr(target_material, clss_name)
        setattr(graph_setting, consts.SBS_CONFIGURED, True)
        if report is not None:
            report({'INFO'}, "Graph {0} is loaded".format(m_sublender.graph_url))
    else:
        m_sublender.package_missing = True
        if report is not None:
            report({'WARNING'}, "Package is missing or corrupted: {0}".format(m_sublender.package_path))


def parse_sbsar_package(filepath: str):
    if not os.path.exists(filepath):
        return None
    sbs_pkg = parser.sbsarlite.parse_doc(filepath)
    return sbs_pkg


async def load_sbsar_to_dict_async(filepath: str, report=None):
    if report is not None:
        print("Parsing sbsar {0}".format(filepath))
        report({'INFO'}, "Parsing sbsar {0}".format(filepath))
    loop = asyncio.get_event_loop()
    sbs_package = await loop.run_in_executor(None, parse_sbsar_package, filepath)
    globalvar.sbsar_dict[filepath] = sbs_package
    if report is not None:
        report({'INFO'}, "Package {0} is parsed".format(filepath))
        print("Package {0} is parsed".format(filepath))
    return sbs_package


async def load_sbsars_async(report=None):
    preferences = bpy.context.preferences.addons["sublender"].preferences
    sb_materials = []
    sbs_package_set = set()

    for material in bpy.data.materials:
        # filter material
        m_sublender = material.sublender
        if (m_sublender is not None) and (m_sublender.graph_url != "") \
                and (m_sublender.package_path != ""):
            m_sublender.package_loaded = False
            sb_materials.append(material)
            sbs_package_set.add(m_sublender.package_path)
    load_queue = []
    for fp in sbs_package_set:
        load_queue.append(load_sbsar_to_dict_async(fp, report))
    await asyncio.gather(*load_queue)
    for material in sb_materials:
        m_sublender = material.sublender
        await gen_clss_from_material_async(material, preferences.enable_visible_if, False, report)
        m_sublender.package_loaded = True


def find_active_mat(context):
    if not sublender_inited(context):
        return None
    scene_sb_settings = context.scene.sublender_settings
    if scene_sb_settings.follow_selection:
        if (context.view_layer.objects.active is None
                or len(bpy.context.view_layer.objects.active.material_slots) == 0):
            return None
        active_material_enum = settings.instance_list_of_object
        if len(active_material_enum) == 0:
            return None
        mat_name = context.scene.sublender_settings.object_active_instance
        return bpy.data.materials.get(mat_name, None)
    if len(globalvar.instance_of_graph) > 0:
        target_mat = bpy.data.materials.get(scene_sb_settings.active_instance)
        return target_mat
    return None


def find_active_graph(context):
    if not sublender_inited(context):
        return None
    scene_sb_settings: settings.SublenderSetting = context.scene.sublender_settings
    if scene_sb_settings.follow_selection:
        if (context.view_layer.objects.active is None
                or len(bpy.context.view_layer.objects.active.material_slots) == 0):
            return None, None
        if context.scene.sublender_settings.object_active_instance == "":
            settings.init_instance_list_of_object(context)
        active_material_enum = settings.instance_list_of_object
        if len(active_material_enum) == 0:
            return None, None
        mat_name = context.scene.sublender_settings.object_active_instance
        active_mat = bpy.data.materials.get(mat_name, None)
        return active_mat, active_mat.sublender.graph_url

    mats = bpy.data.materials
    target_mat = mats.get(scene_sb_settings.active_instance)
    if target_mat is not None:
        return target_mat, target_mat.sublender.graph_url
    return None, None


def refresh_panel(context):
    if context.area is not None:
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
                break
    else:
        print("Context.Area is None, Forcing updating all VIEW_3D-UI")
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == "UI":
                            region.tag_redraw()
                            break
                    break


async def init_sublender_async(self, context):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    await load_sbsars_async(self.report)
    settings.init_graph_items()
    settings.init_instance_of_graph(sublender_settings)
    bpy.app.handlers.undo_post.append(on_blender_undo)
    bpy.app.handlers.redo_post.append(on_blender_undo)
    if sublender_settings.uuid == "":
        sublender_settings.uuid = str(uuid.uuid4())
    globalvar.current_uuid = sublender_settings.uuid
    refresh_panel(context)


def apply_preset(material, preset_name):
    material_id = material.sublender.library_uid
    clss_name = gen_clss_name(material.sublender.graph_url)
    graph_setting = getattr(material, clss_name)
    clss_info = globalvar.graph_clss.get(clss_name)
    prop_input_map = clss_info['prop_input_map']
    # Apply preset
    preset = globalvar.library['materials'].get(material_id)['presets'].get(preset_name)
    for p_value in preset["values"]:
        if p_value['identifier'] != '$outputsize' and p_value['identifier'] != '$randomseed':
            parsed_value = p_value["value"]
            if isinstance(parsed_value, str):
                parsed_value = parser.sbsarlite.parse_str_value(parsed_value, p_value['type'])
            if p_value["type"] == parser.sbsarlite.SBSARTypeEnum.INTEGER1:
                input_info = prop_input_map[p_value['prop']]
                if input_info.get('widget') == 'combobox' and input_info.get('combo_items') is not None:
                    parsed_value = "$NUM:{0}".format(parsed_value)
                if input_info.get('widget') == 'togglebutton':
                    parsed_value = bool(parsed_value)
            setattr(graph_setting, p_value['prop'], parsed_value)


def reset_material(material):
    clss_name = gen_clss_name(material.sublender.graph_url)
    graph_setting = getattr(material, clss_name)
    clss_info = globalvar.graph_clss.get(clss_name)
    for p_input in clss_info["input"]:
        if p_input['identifier'] != "$outputsize" and p_input['identifier'] != "$randomseed":
            graph_setting.property_unset(p_input["prop"])


def sublender_inited(context):
    sublender_settings: settings.SublenderSetting = context.scene.sublender_settings
    return globalvar.current_uuid != "" and globalvar.current_uuid == sublender_settings.uuid


def get_addon_preferences(context):
    return context.preferences.addons["sublender"].preferences


def on_blender_undo(scene):
    sublender_settings = scene.sublender_settings
    if sublender_settings.live_update and sublender_settings.catch_undo:
        print("sublender_settings.catch_undo is On,re-render texture now")
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name='')


def unregister():
    if on_blender_undo in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.remove(on_blender_undo)
        bpy.app.handlers.redo_post.remove(on_blender_undo)