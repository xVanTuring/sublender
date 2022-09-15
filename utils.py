import bpy
from bpy.props import (BoolProperty, EnumProperty)
from bpy.utils import register_class
from pysbs import sbsarchive
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
import os
from . import globalvar, consts, settings
from .parser import parse_sbsar_input


def sbsar_input_updated(self, context):
    if globalvar.active_material_name is not None:
        bpy.ops.sublender.render_texture_async(material_name=globalvar.active_material_name)


# def real_task():


def new_material_name(material_name: str) -> str:
    """Make Sure No Name Comflict"""
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
    if self.output_size_lock and self.output_size_y != self.output_size_x:
        self.output_size_y = self.output_size_x


def substance_group_to_toggle_name(name: str) -> str:
    return "sb_{0}_gptl".format(bpy.path.clean_name(name))


def gen_clss_name(graph_url: str):
    return "sb" + graph_url.replace("pkg://", "_")


def dynamic_gen_clss(package_path: str, graph_url: str, ):
    if globalvar.sbsar_dict.get(package_path) is None:
        sbsar_pkg = sbsarchive.SBSArchive(
            globalvar.aContext, package_path)
        sbsar_pkg.parseDoc()
        globalvar.sbsar_dict[package_path] = sbsar_pkg
    clss_name = gen_clss_name(graph_url)
    if globalvar.graph_clss.get(clss_name) is None:
        sbs_graph = globalvar.sbsar_dict[package_path].getSBSGraphFromPkgUrl(
            graph_url)
        all_inputs = sbs_graph.getAllInputs()
        all_outputs = sbs_graph.getGraphOutputs()
        input_list = parse_sbsar_input(all_inputs)
        _anno_obj = {}

        def assign(obj_from, obj_to, m_prop_name: str):
            if obj_from.get(m_prop_name) is not None:
                obj_to[m_prop_name] = obj_from.get(m_prop_name)

        input_info_dict = {}
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
                    _anno_item['subtype'] = 'COLOR'
            _anno_item['update'] = sbsar_input_updated

            if input_info['mIdentifier'] == '$outputsize':
                # make it to be two enum
                # TODO update event to sync x,y
                _anno_obj["output_size_x"] = (EnumProperty, {
                    'items': consts.output_size_one_enum,
                    'default': '8',
                    'update': output_size_x_updated,
                })
                _anno_obj["output_size_y"] = (EnumProperty, {
                    'items': consts.output_size_one_enum,
                    'default': '8'
                })
                _anno_obj["output_size_lock"] = (BoolProperty, {
                    'default': True,
                    'update': output_size_x_updated
                })
                pass
            else:
                _anno_obj[input_info['prop']] = (prop_type, _anno_item)

            if input_info_dict.get(input_info['group']) is None:
                input_info_dict[input_info['group']] = []
            input_info_dict[input_info['group']].append(input_info)
        for group_key in input_info_dict.keys():
            if group_key != consts.UNGROUPED:
                group_toggle_prop_name = substance_group_to_toggle_name(group_key)
                _anno_obj[group_toggle_prop_name] = (BoolProperty, {
                    'default': False,
                    'name': "Show {0}".format(group_key)
                })
        clss = type(clss_name, (bpy.types.PropertyGroup,), {
            '__annotations__': _anno_obj
        })
        register_class(clss)
        output_info_list = []
        for output in all_outputs:
            output_info_list.append(output.mIdentifier)
        globalvar.graph_clss[clss_name] = {
            'clss': clss,
            'input': input_info_dict,
            'output': output_info_list
        }
        setattr(bpy.types.Material, clss_name,
                bpy.props.PointerProperty(type=clss))
    return clss_name, globalvar.graph_clss.get(clss_name)


def load_sbsar():
    mats = bpy.data.materials.items()
    for _, mat in mats:
        m_sublender: settings.Sublender_Material_MT_Setting = mat.sublender
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)


def texture_output_dir(clss_name: str, material_name: str):
    return os.path.join(
        consts.SUBLENDER_DIR, globalvar.current_uuid, clss_name, bpy.path.clean_name(material_name))
