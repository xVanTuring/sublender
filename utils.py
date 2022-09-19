import bpy
from bpy.props import (BoolProperty, EnumProperty)
from bpy.utils import register_class
from pysbs import sbsarchive
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
import os
from . import globalvar, consts, settings
from .parser import parse_sbsar_input, parse_sbsar_group
from pysbs.sbsarchive.sbsarchive import SBSARGraph


def sbsar_input_updated(self, context):
    if context.scene.sublender_settings.live_update:
        bpy.ops.sublender.render_texture_async()


def new_material_name(material_name: str) -> str:
    """Make Sure No Name Conflict"""
    for mat in bpy.data.materials:
        name: str = mat.name
        if name == material_name:
            try:
                base, suffix = name.rsplit('.', 1)

                # trigger the exception
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
    sbsar_input_updated(self, context)


def substance_group_to_toggle_name(name: str) -> str:
    return "sb_{0}_gptl".format(bpy.path.clean_name(str(hash(name))))


def gen_clss_name(graph_url: str):
    return "sb" + graph_url.replace("pkg://", "_")


def dynamic_gen_clss(package_path: str, graph_url: str):
    if globalvar.sbsar_dict.get(package_path) is None:
        if not os.path.exists(package_path):
            raise FileNotFoundError("File {0} does not exist".format(package_path))
        sbsar_pkg = sbsarchive.SBSArchive(
            globalvar.aContext, package_path)
        sbsar_pkg.parseDoc()
        globalvar.sbsar_dict[package_path] = sbsar_pkg
    clss_name = gen_clss_name(graph_url)
    if globalvar.graph_clss.get(clss_name) is None:
        sbs_graph: SBSARGraph = globalvar.sbsar_dict[package_path].getSBSGraphFromPkgUrl(
            graph_url)
        all_inputs = sbs_graph.getAllInputs()
        all_outputs = sbs_graph.getGraphOutputs()
        input_list = parse_sbsar_input(all_inputs)
        _anno_obj = {}

        def assign(obj_from, obj_to, m_prop_name: str):
            if obj_from.get(m_prop_name) is not None:
                obj_to[m_prop_name] = obj_from.get(m_prop_name)

        for input_info in input_list:
            (prop_type,
             prop_size) = consts.sbsar_type_to_property[input_info['mType']]
            _anno_item = {
            }
            if prop_size is not None:
                _anno_item['size'] = prop_size
            assign(input_info, _anno_item, 'default')
            assign(input_info, _anno_item, 'min')
            assign(input_info, _anno_item, 'max')
            assign(input_info, _anno_item, 'step')
            if input_info['mType'] == SBSARTypeEnum.INTEGER1:
                if input_info.get('mWidget') == 'togglebutton':
                    prop_type = BoolProperty
                if input_info.get('mWidget') == 'combobox' and input_info.get('enum_items') is not None:
                    prop_type = EnumProperty
                    _anno_item['items'] = input_info.get('enum_items')
            if input_info['mType'] in [SBSARTypeEnum.FLOAT3, SBSARTypeEnum.FLOAT4]:
                if input_info.get('mWidget') == 'color':
                    _anno_item['min'] = 0
                    _anno_item['max'] = 1
                    _anno_item['subtype'] = 'COLOR'

            _anno_item['update'] = sbsar_input_updated
            if input_info['mIdentifier'] == '$outputsize':
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
                    'update': output_size_x_updated,
                })
                _anno_obj[consts.output_size_lock] = (BoolProperty, {
                    'default': addon_prefs.output_size_lock,
                    'update': output_size_x_updated
                })
            else:
                _anno_obj[input_info['prop']] = (prop_type, _anno_item)

        graph_tree, group_keys = parse_sbsar_group(sbs_graph)
        for group_key in group_keys:
            displace_name = group_key.split('/')[-1]
            group_toggle_prop_name = substance_group_to_toggle_name(group_key)
            _anno_obj[group_toggle_prop_name] = (BoolProperty, {
                'default': False,
                'name': displace_name,
                'description': "Toggle Display group"
            })
        clss = type(clss_name, (bpy.types.PropertyGroup,), {
            '__annotations__': _anno_obj
        })
        register_class(clss)

        output_info_list = []
        output_usage_dict = {}
        for output in all_outputs:
            output_info_list.append(output.mIdentifier)
            for usage in output.getUsages():
                if output_usage_dict.get(usage.mName) is None:
                    output_usage_dict[usage.mName] = []
                output_usage_dict[usage.mName].append(output.mIdentifier)
        globalvar.graph_clss[clss_name] = {
            'clss': clss,
            'input': input_list,
            'group_tree': graph_tree,
            'output': output_info_list,
            'output_usage_dict': output_usage_dict,
            'graph': sbs_graph
        }
        setattr(bpy.types.Material, clss_name,
                bpy.props.PointerProperty(type=clss))

    return clss_name, globalvar.graph_clss.get(clss_name)


def load_sbsars():
    mats = bpy.data.materials.items()
    for _, mat in mats:
        m_sublender: settings.Sublender_Material_MT_Setting = mat.sublender
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            try:
                dynamic_gen_clss(
                    m_sublender.package_path, m_sublender.graph_url)
                m_sublender.package_missing = False
            except FileNotFoundError as e:
                print(e)
                print("Set Sbsar missing")
                m_sublender.package_missing = True


def texture_output_dir(clss_name: str, material_name: str):
    return os.path.join(
        globalvar.SUBLENDER_DIR, globalvar.current_uuid, clss_name, bpy.path.clean_name(material_name))


def find_active_mat(context):
    scene_sb_settings: settings.SublenderSetting = context.scene.sublender_settings
    if scene_sb_settings.follow_selection:
        if bpy.context.view_layer.objects.active is None or len(
                bpy.context.view_layer.objects.active.material_slots) == 0:
            return None
        # mt_index = bpy.context.object.active_material_index
        active_mat = bpy.context.view_layer.objects.active.active_material
        # bpy.context.view_layer.objects.active.material_slots[
        # mt_index].material
        if active_mat is not None:
            mat_setting: settings.Sublender_Material_MT_Setting = active_mat.sublender
            if mat_setting.package_path != '' and mat_setting.graph_url != '':
                return active_mat
        return None

    mats = bpy.data.materials
    target_mat = mats.get(scene_sb_settings.active_instance)
    return target_mat
