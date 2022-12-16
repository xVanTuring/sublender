import asyncio
import os
import pathlib
import tempfile
import typing

import bpy
import mathutils
from bpy.props import (BoolProperty, EnumProperty)
from bpy.utils import register_class

from . import globalvar, consts, settings, parser, ui, sbsarlite
from .parser import parse_sbsar_group


def sbsar_input_updated(_, context):
    if context.scene.sublender_settings.live_update:
        bpy.ops.sublender.render_texture_async()


def sbsar_output_updated_name(sbs_id: str):
    def sbsar_output_updated(self, _):
        prop_name = sb_output_to_prop(sbs_id)
        if getattr(self, consts.SBS_CONFIGURED) and getattr(self, prop_name):
            bpy.ops.sublender.render_texture_async(texture_name=sbs_id)

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
        sbs_graph = globalvar.graph_clss.get(self.clss_name).get('sbs_graph')

        graph_setting = getattr(bpy.data.materials.get(self.material_name), self.clss_name)
        if identifier == "$outputsize":
            if getattr(graph_setting, consts.output_size_lock):
                return VectorWrapper([int(getattr(graph_setting, consts.output_size_x)),
                                      int(getattr(graph_setting, consts.output_size_x))])
            else:
                return VectorWrapper([int(getattr(graph_setting, consts.output_size_x)),
                                      int(getattr(graph_setting, consts.output_size_y))])
        prop_name = None

        for i in sbs_graph['inputs']:
            if i['identifier'] == identifier:
                prop_name = parser.uid_prop(i['uid'])
        if prop_name is None:
            return False
        value = getattr(graph_setting, prop_name, None)
        # TODO(???): FIX drop_down enum type
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
        p_clss = type(sub_panel_name(group_key, graph_url),
                      (ui.Sublender_Prop_BasePanel,), {
                          'bl_label': displace_name,
                          'bl_parent_id': bl_parent_id,
                          'graph_url': graph_url,
                          'group_info': cur_group
                      })
        register_class(p_clss)
        globalvar.sub_panel_clss_list.append(p_clss)


def dynamic_gen_clss_graph(sbs_graph, graph_url: str):
    clss_name = gen_clss_name(graph_url)
    if globalvar.graph_clss.get(clss_name) is None:
        all_inputs = sbs_graph['inputs']
        all_outputs = sbs_graph['outputs']
        _anno_obj = {}

        def assign(obj_from, obj_to, m_prop_name: str):
            if obj_from.get(m_prop_name) is not None:
                obj_to[m_prop_name] = obj_from.get(m_prop_name)

        for input_info in all_inputs:
            (prop_type,
             prop_size) = consts.sbsar_type_to_property[input_info['type']]
            _anno_item = {
            }
            if prop_size is not None:
                _anno_item['size'] = prop_size
            assign(input_info, _anno_item, 'default')
            assign(input_info, _anno_item, 'min')
            assign(input_info, _anno_item, 'max')
            assign(input_info, _anno_item, 'step')
            if input_info['type'] == sbsarlite.SBSARTypeEnum.INTEGER1:
                if input_info.get('widget') == 'togglebutton':
                    prop_type = BoolProperty
                if input_info.get('widget') == 'combobox' and input_info.get('combo_items') is not None:
                    prop_type = EnumProperty
                    _anno_item['items'] = input_info.get('combo_items')
            if input_info['type'] == sbsarlite.SBSARTypeEnum.IMAGE:
                _anno_item['subtype'] = 'FILE_PATH'
            if input_info['type'] in [sbsarlite.SBSARTypeEnum.FLOAT3, sbsarlite.SBSARTypeEnum.FLOAT4]:
                if input_info.get('widget') == 'color':
                    _anno_item['min'] = 0
                    _anno_item['max'] = 1
                    _anno_item['subtype'] = 'COLOR'

            _anno_item['update'] = sbsar_input_updated
            if input_info['identifier'] == '$outputsize':
                preferences = bpy.context.preferences
                addon_prefs = preferences.addons[__package__].preferences
                _anno_obj[consts.output_size_x] = (EnumProperty, {
                    'items': consts.output_size_one_enum,
                    'default': addon_prefs.output_size_x,
                    'update': output_size_x_updated,
                })
                _anno_obj[consts.output_size_y] = (EnumProperty, {
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

        output_list = []
        output_list_dict = {}
        output_usage_dict: typing.Dict[str, typing.List[str]] = {}
        for output in all_outputs:
            _anno_obj[sb_output_to_prop(output['identifier'])] = (BoolProperty, {
                'name': output['label'],
                'default': False,
                'update': sbsar_output_updated_name(output['identifier'])
            })
            _anno_obj[sb_output_format_to_prop(output['identifier'])] = (EnumProperty, {
                'name': 'Format',
                'items': consts.format_list,
                'default': 'png'
            })
            _anno_obj[sb_output_dep_to_prop(output['identifier'])] = (EnumProperty, {
                'name': 'Bit Depth',
                'items': consts.output_bit_depth,
                'default': '0'
            })
            usages = output['usages']
            output_graph = {
                'name': output['identifier'],
                'usages': usages,
                'label': output['label'],
                'uid': output['uid']
            }
            output_list_dict[output['identifier']] = output_graph
            output_list.append(output_graph)
            for usage in usages:
                if output_usage_dict.get(usage) is None:
                    output_usage_dict[usage] = []
                output_usage_dict[usage].append(output['identifier'])

        group_tree, group_map = parse_sbsar_group(sbs_graph)
        generate_sub_panel(group_map, graph_url)
        _anno_obj[consts.SBS_CONFIGURED] = (BoolProperty, {
            'name': "SBS Configured",
            'default': False,
        })
        clss = type(clss_name, (bpy.types.PropertyGroup,), {
            '__annotations__': _anno_obj
        })
        register_class(clss)

        globalvar.graph_clss[clss_name] = {
            'clss': clss,
            'input': all_inputs,
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
        setattr(bpy.types.Material, clss_name,
                bpy.props.PointerProperty(type=clss))

    return clss_name, globalvar.graph_clss.get(clss_name)


async def load_sbsar_gen(loop, preferences, material, force=False, report=None):
    m_sublender = material.sublender
    sbs_package = None
    if not force:
        sbs_package = globalvar.sbsar_dict.get(m_sublender.package_path)
    if sbs_package is None:
        sbs_package = await loop.run_in_executor(None, load_sbsar_package, m_sublender.package_path)
        globalvar.sbsar_dict[m_sublender.package_path] = sbs_package

    if sbs_package is not None:
        sbs_graph = None
        for graph in sbs_package['graphs']:
            if graph['pkgUrl'] == m_sublender.graph_url:
                sbs_graph = graph
        # TODO force to unregister loaded clss
        clss_name, clss_info = dynamic_gen_clss_graph(sbs_graph, m_sublender.graph_url)
        m_sublender.package_missing = False
        if preferences.enable_visible_if:
            globalvar.eval_delegate_map[material.name] = EvalDelegate(
                material.name,
                clss_name
            )
        graph_setting = getattr(material, clss_name)
        setattr(graph_setting, consts.SBS_CONFIGURED, True)
        if report is not None:
            report({'INFO'}, "Package {0} is loaded".format(m_sublender.package_path))
    else:
        m_sublender.package_missing = True
        if report is not None:
            report({'WARNING'}, "Package is missing or corrupted: {0}".format(m_sublender.package_path))


def load_sbsar_package(filepath: str):
    if not os.path.exists(filepath):
        return None
    sbs_pkg = sbsarlite.parse_doc(filepath)
    return sbs_pkg


async def load_and_assign(filepath: str, report=None):
    if report is not None:
        report({'INFO'}, "Parsing sbsar {0}".format(filepath))
    loop = asyncio.get_event_loop()
    sbs_package = await loop.run_in_executor(None, load_sbsar_package, filepath)
    globalvar.sbsar_dict[filepath] = sbs_package
    if report is not None:
        report({'INFO'}, "Package {0} is parsed".format(filepath))


async def load_sbsars_async(report=None):
    loop = asyncio.get_event_loop()
    preferences = bpy.context.preferences.addons[__package__].preferences
    sb_materials = []
    sbs_package_set = set()
    for material in bpy.data.materials:
        # filter material
        m_sublender: settings.Sublender_Material_MT_Setting = material.sublender
        if (m_sublender is not None) and (m_sublender.graph_url != "") \
                and (m_sublender.package_path != ""):
            m_sublender.package_loaded = False
            sb_materials.append(material)
            sbs_package_set.add(m_sublender.package_path)
    load_queue = []
    for fp in sbs_package_set:
        load_queue.append(load_and_assign(fp, report))
    await asyncio.gather(*load_queue)
    for material in sb_materials:
        m_sublender: settings.Sublender_Material_MT_Setting = material.sublender
        await load_sbsar_gen(loop, preferences, material, False, report)
        m_sublender.package_loaded = True


def texture_output_dir(material_name: str):
    if bpy.data.filepath != "":
        current_file = pathlib.Path(bpy.data.filepath)
        parent_dir = current_file.parent
        file_name = bpy.path.clean_name(current_file.name)
        return str(parent_dir.joinpath(file_name, "mat_{0}".format(bpy.path.clean_name(material_name))))
    temp_dir = tempfile.gettempdir()
    return os.path.join(
        temp_dir, "sublender", globalvar.current_uuid, "mat_{0}".format(bpy.path.clean_name(material_name)))


def find_active_mat(context):
    scene_sb_settings: settings.SublenderSetting = context.scene.sublender_settings
    if scene_sb_settings.follow_selection:
        if bpy.context.view_layer.objects.active is None or len(
                bpy.context.view_layer.objects.active.material_slots) == 0:
            return None
        active_mat = bpy.context.view_layer.objects.active.active_material
        if active_mat is not None:
            mat_setting: settings.Sublender_Material_MT_Setting = active_mat.sublender
            if mat_setting.package_path != '' and mat_setting.graph_url != '':
                return active_mat
        return None

    mats = bpy.data.materials
    target_mat = mats.get(scene_sb_settings.active_instance)
    return target_mat


def find_active_graph(context):
    scene_sb_settings: settings.SublenderSetting = context.scene.sublender_settings
    if scene_sb_settings.follow_selection:
        if bpy.context.view_layer.objects.active is None or len(
                bpy.context.view_layer.objects.active.material_slots) == 0:
            return None, None
        active_mat = bpy.context.view_layer.objects.active.active_material
        if active_mat is not None:
            mat_setting: settings.Sublender_Material_MT_Setting = active_mat.sublender
            if mat_setting.package_path != '' and mat_setting.graph_url != '':
                return active_mat, active_mat.sublender.graph_url
        return None, None

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
