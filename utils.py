import bpy
from bpy.props import (BoolProperty, EnumProperty)
from bpy.utils import register_class
from pysbs import sbsarchive
import typing

from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
import os
from . import globalvar, consts, settings, parser
from .parser import parse_sbsar_input, parse_sbsar_group
from pysbs.sbsarchive.sbsarchive import SBSARGraph
import mathutils


def sbsar_input_updated(self, context):
    if context.scene.sublender_settings.live_update:
        bpy.ops.sublender.render_texture_async()


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
    graph = None

    def __init__(self, graph, graph_setting):
        self.graph = graph
        self.graph_setting = graph_setting

    def __getitem__(self, identifier: str):
        if identifier == "$outputsize":
            if getattr(self.graph_setting, consts.output_size_lock):
                return VectorWrapper([int(getattr(self.graph_setting, consts.output_size_x)),
                                      int(getattr(self.graph_setting, consts.output_size_x))])
            else:
                return VectorWrapper([int(getattr(self.graph_setting, consts.output_size_x)),
                                      int(getattr(self.graph_setting, consts.output_size_y))])
        prop_name = parser.uid_prop(self.graph.getInput(identifier).mUID)
        value = getattr(self.graph_setting, prop_name, None)
        if isinstance(value, mathutils.Color) or isinstance(value, bpy.types.bpy_prop_array):
            return VectorWrapper(value)
        return value


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


def calc_prop_visibility(eval_delegate, input_info: dict):
    if input_info.get('mVisibleIf') is None:
        return True
    eval_str: str = input_info.get('mVisibleIf').replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    if eval_delegate is None:
        return False
    eval_result = eval(eval_str, {
        'input': eval_delegate,
        'true': True,
        'false': False
    })
    if eval_result:
        return True
    return False


def calc_group_visibility(eval_delegate, group_info: dict):
    for input_info in group_info['inputs']:
        input_visibility = calc_prop_visibility(eval_delegate, input_info)
        if input_visibility:
            return True

    for group_info in group_info['sub_group']:
        if calc_group_visibility(eval_delegate, group_info):
            return True
    return False


class Sublender_Prop_BasePanel(object):
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_options = {'DEFAULT_CLOSED'}
    graph_url = ""
    group_info = None

    @classmethod
    def poll(cls, context):
        active_mat, active_graph = find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        if globalvar.eval_delegate_map.get(active_mat.name) is None:
            clss_name = gen_clss_name(cls.graph_url)
            globalvar.eval_delegate_map[active_mat.name] = EvalDelegate(
                globalvar.graph_clss.get(clss_name)['sbs_graph'],
                getattr(active_mat, clss_name)
            )
        return active_graph == cls.graph_url and not active_mat.sublender.package_missing and calc_group_visibility(
            globalvar.eval_delegate_map.get(active_mat.name),
            cls.group_info)

    def draw(self, context):
        layout = self.layout
        target_mat = find_active_mat(context)
        sublender_setting = target_mat.sublender
        clss_name = gen_clss_name(sublender_setting.graph_url)
        graph_setting = getattr(target_mat, clss_name)
        for prop_info in self.group_info['inputs']:
            toggle = -1
            if prop_info.get('togglebutton', False):
                toggle = 1
            layout.prop(graph_setting, prop_info['prop'], text=prop_info['label'], toggle=toggle)


def generate_sub_panel(group_map, graph_url):
    for group_key in group_map.keys():
        if group_key == consts.UNGROUPED:
            continue
        displace_name = group_key.split('/')[-1]
        parent_name = '/'.join(group_key.split('/')[:-1])
        bl_parent_id = ''
        if parent_name != '':
            bl_parent_id = "Sbs_PT_{0}".format(hash(parent_name + graph_url))
        p_clss = type("Sbs_PT_{0}".format(hash(group_key + graph_url)),
                      (Sublender_Prop_BasePanel, bpy.types.Panel,), {
                          'bl_label': displace_name,
                          'bl_parent_id': bl_parent_id,
                          'graph_url': graph_url,
                          'group_info': group_map.get(group_key)
                      })
        register_class(p_clss)


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

        group_tree, group_map = parse_sbsar_group(sbs_graph)
        generate_sub_panel(group_map, graph_url)
        clss = type(clss_name, (bpy.types.PropertyGroup,), {
            '__annotations__': _anno_obj
        })
        register_class(clss)

        output_list = []
        output_usage_dict: typing.Dict[str, typing.List[str]] = {}
        for output in all_outputs:
            output_list.append(output.mIdentifier)
            for usage in output.getUsages():
                if output_usage_dict.get(usage.mName) is None:
                    output_usage_dict[usage.mName] = []
                output_usage_dict[usage.mName].append(output.mIdentifier)
        globalvar.graph_clss[clss_name] = {
            'clss': clss,
            'input': input_list,
            'group_info': {
                'tree': group_tree,
                'map': group_map
            },
            'output_info': {
                'list': output_list,
                'usage': output_usage_dict
            },
            'sbs_graph': sbs_graph,

            # 'group_map': group_map,
            # 'group_tree': group_tree,
            # 'output': output_list,
            # 'output_usage_dict': output_usage_dict,
            # 'graph': sbs_graph,
        }
        setattr(bpy.types.Material, clss_name,
                bpy.props.PointerProperty(type=clss))

    return clss_name, globalvar.graph_clss.get(clss_name)


def load_sbsars():
    mats = bpy.data.materials.items()
    for _, mat in mats:
        m_sublender: settings.Sublender_Material_MT_Setting = mat.sublender
        # TODO fix material name override
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            try:
                clss_name, clss_info = dynamic_gen_clss(
                    m_sublender.package_path, m_sublender.graph_url)
                m_sublender.package_missing = False
                globalvar.eval_delegate_map[mat.name] = EvalDelegate(
                    clss_info['sbs_graph'],
                    getattr(mat, clss_name)
                )
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
    return target_mat, target_mat.sublender.graph_url
