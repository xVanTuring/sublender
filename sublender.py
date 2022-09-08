import pprint
import subprocess
from pysbs.sbsarchive.sbsargraph import SBSARInput
from pysbs.sbsarchive.sbsarchive import SBSARGraph
from pysbs.sbsarchive.sbsarenum import SBSARTypeEnum
from pysbs import sbsarchive, context
import pysbs
from pysbs.sbsarchive import SBSARInputGui
from pysbs.sbsarchive import SBSARGuiComboBox
from typing import List
from bpy_extras.io_utils import ImportHelper
from bpy.utils import previews, register_class
from bpy.types import Panel, Operator, Menu, PropertyGroupItem
import pathlib
import json
import bpy
import os
from pysbs.batchtools import batchtools
from bpy.props import PointerProperty, StringProperty, BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty
from pathlib import Path
# from shutil import copy
HOME = str(Path.home())
SUBLENDER_DIR = os.path.join(HOME, ".sublender")
bl_info = {
    "name": "Sublender",
    "author": "xVanTuring(@outlook.com)",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (0, 0, 1),
    "location": "View3D > Properties > Sublender",
    "description": "A addon for sbsar",
    "category": "Material"
}
type_dict = ['FLOAT1',
             'FLOAT2',
             'FLOAT3',
             'FLOAT4',
             'INTEGER1',
             'IMAGE',
             'STRING',
             'FONT',
             'INTEGER2',
             'INTEGER3',
             'INTEGER4', ]


def new_material_name(material_name: str) -> str:
    """Make Sure No Name Comflict"""
    for mat in bpy.data.materials:
        name: str = mat.name
        if (name == material_name):
            try:
                base, suffix = name.rsplit('.', 1)

                # trigger the exception
                num = int(suffix, 10)
                material_name = base + "." + '%03d' % (num + 1)
            except ValueError:
                material_name = material_name + ".001"

    return material_name


aContext = pysbs.context.Context()

instance_map = {
}
sbsar_dict = {}
"""key->{clss,input}"""
graph_clss = {}

UNGROUPED = '$UNGROUPED$'

sbsar_name_prop = {
    '$outputsize': 'output_size',
    '$randomseed': 'random_seed'
}
sbsar_name_to_label = {
    '$outputsize': 'Output Size',
    '$randomseed': 'Random Seed'
}
sbsar_type_to_property = [
    (FloatProperty, None,),
    (FloatVectorProperty, 2,),
    (FloatVectorProperty, 3,),
    (FloatVectorProperty, 4,),
    (IntProperty, None),
    (None, None),
    (StringProperty, None),
    (None, None),
    (IntVectorProperty, 2),
    (IntVectorProperty, 3),
    (IntVectorProperty, 4),
]

material_templates = {}
material_template_enum = []


def generate_material_nodes():
    pass


def parseSbsarInput(graph_inputs: List[SBSARInput]):
    input_list = []
    for sbsa_graph_input in graph_inputs:
        group = sbsa_graph_input.getGroup()
        gui: SBSARInputGui = sbsa_graph_input.getInputGui()
        label = sbsar_name_to_label.get(
            sbsa_graph_input.mIdentifier, sbsa_graph_input.mIdentifier)
        if gui is not None:
            label = gui.mLabel
        if group is None:
            group = UNGROUPED
        input_info = {
            'group': group,
            'mIdentifier': sbsa_graph_input.mIdentifier,
            'mType': sbsa_graph_input.mType,
            'mTypeStr': type_dict[sbsa_graph_input.mType],
            'default': sbsa_graph_input.getDefaultValue(),
            'label': label
        }
        if gui is not None:
            if gui.mWidget in ['togglebutton', 'combobox', 'color']:
                input_info['mWidget'] = gui.mWidget
            if gui.mWidget == 'combobox':
                comboxBox: SBSARGuiComboBox = gui.mGuiComboBox
                drop_down = comboxBox.getDropDownList()
                if drop_down is not None:
                    drop_down_keys = list(drop_down.keys())
                    drop_down_keys.sort()
                    drop_down_list = []
                    for key in drop_down_keys:
                        drop_down_list.append(
                            (drop_down[key], drop_down[key], drop_down[key]))
                    input_info['drop_down'] = drop_down_list
        if sbsa_graph_input.getMaxValue() is not None:
            input_info['max'] = sbsa_graph_input.getMaxValue()
        if sbsa_graph_input.getMinValue() is not None:
            input_info['min'] = sbsa_graph_input.getMinValue()
        if sbsa_graph_input.getStep() is not None:
            input_info['step'] = int(sbsa_graph_input.getStep()*100)
        input_list.append(input_info)
    return input_list


def dynamic_gen_clss(package_path: str, graph_url: str,):
    if sbsar_dict.get(package_path) is None:
        sbsar_pkg = sbsarchive.SBSArchive(
            aContext, package_path)
        sbsar_pkg.parseDoc()
        sbsar_dict[package_path] = sbsar_pkg
    # input_info_list = []
    clss_name = "sublender_"+graph_url.replace("://", "_")
    if graph_clss.get(clss_name) is None:
        all_inputs = sbsar_dict[package_path].getSBSGraphFromPkgUrl(
            graph_url).getAllInputs()
        input_list = parseSbsarInput(all_inputs)
        _anno_obj = {}

        def assign(obj_from, obj_to, prop_name: str):
            if obj_from.get(prop_name) is not None:
                obj_to[prop_name] = obj_from.get(prop_name)
        input_info_dict = {}
        for input_info in input_list:
            prop_name = sbsar_name_prop.get(
                input_info['mIdentifier'], input_info['mIdentifier'])
            (prop_type,
             prop_size) = sbsar_type_to_property[input_info['mType']]
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
                if input_info.get('mWidget') == 'combobox' and input_info.get('drop_down') is not None:
                    # todo ENUM_FLAG???
                    prop_type = EnumProperty
                    _anno_item['items'] = input_info.get('drop_down')
                    if _anno_item.get('default') is not None:
                        # set to string
                        old_index = _anno_item['default']
                        _anno_item['default'] = input_info['drop_down'][old_index][0]
            if input_info['mType'] in [SBSARTypeEnum.FLOAT3, SBSARTypeEnum.FLOAT4]:
                if input_info.get('mWidget') == 'color':
                    _anno_item['subtype'] = 'COLOR'

            _anno_obj[prop_name] = (prop_type, _anno_item)

            if input_info_dict.get(input_info['group']) is None:
                input_info_dict[input_info['group']] = []
            input_info_dict[input_info['group']].append({
                'prop': prop_name,
                'mIdentifier': input_info['mIdentifier'],
                'label': input_info['label'],
                'mWidget': input_info.get('mWidget')
            })
        clss = type(clss_name, (bpy.types.PropertyGroup,), {
            '__annotations__': _anno_obj
        })
        register_class(clss)

        graph_clss[clss_name] = {
            'clss': clss,
            'input': input_info_dict
        }
        setattr(bpy.types.Material, clss_name,
                bpy.props.PointerProperty(type=clss))
    return (clss_name, graph_clss.get(clss_name))


def graph_list(self, context):
    mats = bpy.data.materials.items()
    instance_map.clear()
    for mat_name, mat in mats:
        m_sublender: Sublender_Material_MT_Setting = mat.sublender
        if m_sublender is not None and (not m_sublender.graph_url == ""):
            if not(m_sublender.graph_url in instance_map):
                instance_map[m_sublender.graph_url] = []
            instance_map[m_sublender.graph_url].append((
                mat_name, mat_name, mat_name,))
    # [(identifier, name, description, icon, number), ...]
    return list(map(lambda x: (x, x, ""), instance_map.keys()))


def active_graph_updated(self, context):
    if len(instance_map.get(context.scene.sublender_settings.active_graph, [])) > 0:
        active_instance = instance_map.get(
            context.scene.sublender_settings.active_graph, [])[0][0]
        context.scene.sublender_settings.active_instance = active_instance


def instance_list(self, context):
    # [(identifier, name, description, icon, number), ...]
    return instance_map.get(context.scene.sublender_settings.active_graph, [])


class SublenderSetting(bpy.types.PropertyGroup):
    show_preview: BoolProperty(name="Show Preview")
    active_graph: EnumProperty(
        items=graph_list, name="Graph", update=active_graph_updated)
    active_instance: EnumProperty(
        items=instance_list, name="Instance")
    uuid: StringProperty(name="UUID of this blender file", default="")


def isType(val, type_str: str):
    return isinstance(val, getattr(bpy.types, type_str))


def ensure_nodes(mat, template):
    # todo: force override position options
    node_list = mat.node_tree.nodes
    for node_info in template['nodes']:
        node_inst = node_list.get(node_info['name'])
        if (node_inst is not None) and (isType(node_inst, node_info['type'])):
            continue
        node_inst = node_list.new(type=node_info['type'])
        node_inst.name = node_info['name']
        if node_info.get('label', None) is not None:
            node_inst.label = node_info['label']
        if node_info.get('location', None) is not None:
            node_inst.location = node_info['location']
        if node_info.get('hide') == True:
            node_inst.hide = True


def ensure_link(mat, template):
    node_list = mat.node_tree.nodes
    node_links = mat.node_tree.links
    for link in template['links']:
        from_node = node_list.get(link['fromNode'])
        to_node = node_list.get(link['toNode'])
        node_links.new(
            from_node.outputs[link['fromSocket']], to_node.inputs[link['toSocket']])


def ensure_assets(mat, template, resource):
    node_list = mat.node_tree.nodes
    for texture_info in template['texture']:
        texture_path = resource.get(texture_info['type'])
        if texture_path is not None:
            image_name = bpy.path.basename(texture_path)
            bpy.ops.image.open(filepath=texture_path)
            target_Node = node_list.get(texture_info['node'])
            texture_img = bpy.data.images.get(image_name)
            if texture_info.get('colorspace') is not None:
                texture_img.colorspace_settings.name = texture_info.get(
                    'colorspace')
            if target_Node is not None:
                target_Node.image = texture_img
            else:
                print("Missing Node:{0}".format(texture_info['node']))
        else:
            print("Missing Texture:{0}".format(texture_info['type']))


def inflate_template(mat, template_name: str):
    # get template_name from material setting
    template = material_templates.get(template_name)
    ensure_nodes(mat, template)
    ensure_link(mat, template)


class Sublender_Import_Graph(Operator):
    bl_idname = "sublender.import_graph"
    bl_label = "Import Graph"
    graph_url: StringProperty(
        name='Current Graph')
    package_path: StringProperty(
        name='Current Graph')
    material_name: StringProperty(
        name='Material Name')
    use_fake_user: BoolProperty(
        name="Fake User",
        default=True
    )
    assign_to_selection: BoolProperty(
        name='Assign to Selected',
        default=False
    )
    material_template: EnumProperty(
        items=material_template_enum,
        name='Material Template'
    )

    def execute(self, context):
        material_name = new_material_name(self.material_name)
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
        material.use_fake_user = self.use_fake_user

        m_sublender: Sublender_Material_MT_Setting = material.sublender
        m_sublender.graph_url = self.graph_url
        m_sublender.package_path = self.package_path
        m_sublender.material_template = self.material_template

        bpy.context.scene.sublender_settings.active_graph = self.graph_url
        clss_name, clss = dynamic_gen_clss(
            self.package_path, self.graph_url)
        inflate_template(material, self.material_template)
        # generate material and texture
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Import "+self.graph_url, icon="IMPORT")
        col = layout.column()
        col.alignment = 'CENTER'
        col.prop(self, "material_name")
        col.prop(self, "use_fake_user", icon='FAKE_USER_ON')
        col.prop(self, "assign_to_selection")
        col.prop(self, "material_template")


class Sublender_Import_Sbsar(Operator, ImportHelper):
    bl_idname = "sublender.import_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(
        default="*.sbsar",
        options={'HIDDEN'},
        maxlen=255
    )

    def execute(self, context):
        file_extension = pathlib.Path(self.filepath).suffix
        if not file_extension == ".sbsar":
            self.report({'WARNING'}, "File extension doesn't match")
            return {'CANCELLED'}
        else:
            importing_package = sbsarchive.SBSArchive(aContext, self.filepath)
            importing_package.parseDoc()

            sbs_graph_list: List[SBSARGraph] = importing_package.getSBSGraphList(
            )
            sbsar_dict[self.filepath] = importing_package
            for graph in sbs_graph_list:
                # INVOKE_DEFAULT
                bpy.ops.sublender.import_graph(
                    'INVOKE_DEFAULT', package_path=self.filepath, graph_url=graph.mPkgUrl, material_name=graph.mLabel)
        return {'FINISHED'}


class Sublender_Render_TEXTURE(Operator):
    bl_idname = "sublender.render_texture"
    bl_label = "Render Texture"
    bl_description = "Render Texture"

    def execute(self, context):
        # read all params
        mats = bpy.data.materials
        sublender_settings: SublenderSetting = context.scene.sublender_settings
        target_mat = mats.get(sublender_settings.active_instance)
        if target_mat is not None:
            m_sublender: Sublender_Material_MT_Setting = target_mat.sublender
            clss_name, clss_info = dynamic_gen_clss(
                m_sublender.package_path, m_sublender.graph_url)
            graph_setting = getattr(target_mat, clss_name)
            input_dict = clss_info['input']
            param_list = []
            param_list.append("--input")
            param_list.append(m_sublender.package_path)
            param_list.append("--input-graph")
            param_list.append(m_sublender.graph_url)
            for group_key in input_dict:
                input_group = input_dict[group_key]
                for input_info in input_group:
                    value = graph_setting.get(input_info['prop'])
                    if value is not None:
                        param_list.append("--set-value")
                        to_list = getattr(value, 'to_list', None)
                        if to_list is not None:
                            value = ','.join(map(str, to_list()))
                        param_list.append("{0}@{1}".format(
                            input_info['mIdentifier'], value))
            param_list.append("--output-path")
            target_dir = os.path.join(
                SUBLENDER_DIR, sublender_settings.uuid, clss_name)
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            param_list.append(target_dir)
            out = batchtools.sbsrender_render(
                *param_list, output_handler=True)
            print(param_list)
        return {'FINISHED'}


class Sublender_New_Instance(Operator):
    bl_idname = "sublender.new_instance"
    bl_label = "New Instance"
    bl_description = "New Instance"

    def execute(self, context):
        return {'FINISHED'}


class Sublender_Material_MT_Setting(bpy.types.PropertyGroup):
    package_path: bpy.props.StringProperty(name="Package Path")
    graph_url: bpy.props.StringProperty(name="Graph URL")
    show_setting: bpy.props.BoolProperty(name="Show Params")
    material_template: EnumProperty(
        name="Material Template", items=material_template_enum)


class Sublender_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES', 'BLENDER_EEVEE'}

    def draw(self, context):
        self.show_preview = True
        mats = bpy.data.materials
        sublender_settings: SublenderSetting = context.scene.sublender_settings
        target_mat = mats.get(sublender_settings.active_instance)
        if sublender_settings.active_instance != "" and target_mat is not None:
            self.layout.prop(sublender_settings,
                             'show_preview', icon='MATERIAL')
            if sublender_settings['show_preview']:
                self.layout.template_preview(
                    target_mat)
                self.layout.separator()
        self.layout.operator("sublender.import_sbsar", icon='IMPORT')
        if sublender_settings.active_graph != "":
            self.layout.prop(sublender_settings,
                             'active_graph')
        if sublender_settings.active_instance != "":
            self.layout.prop(sublender_settings,
                             'active_instance')
        if target_mat is not None:
            self.layout.prop(target_mat, 'use_fake_user')
            m_sublender: Sublender_Material_MT_Setting = target_mat.sublender

            # can't really generate here it's readonly when drawing

            self.layout.prop(m_sublender,
                             'material_template', text='Material Template')

            self.layout.operator("sublender.new_instance", icon='PRESET_NEW')
            self.layout.operator("sublender.render_texture", icon='TEXTURE')

            self.layout.prop(m_sublender, 'show_setting')
            if m_sublender.show_setting:
                clss_name, clss_info = dynamic_gen_clss(
                    m_sublender.package_path, m_sublender.graph_url)
                graph_setting = getattr(target_mat, clss_name)
                input_dict = clss_info['input']
                for group_key in input_dict:
                    if group_key != UNGROUPED:
                        self.layout.label(text=group_key)
                    input_group = input_dict[group_key]
                    for input_info in input_group:
                        toggle = -1
                        if input_info['mWidget'] == 'togglebutton':
                            toggle = 1
                        self.layout.prop(graph_setting,
                                         input_info['prop'], text=input_info['label'], toggle=toggle)


classes = (Sublender_PT_Main, SublenderSetting,
           Sublender_Import_Sbsar, Sublender_Render_TEXTURE, Sublender_New_Instance,
           Sublender_Import_Graph, Sublender_Material_MT_Setting,)


def load_sbsar():
    mats = bpy.data.materials.items()
    for mat_name, mat in mats:
        m_sublender: Sublender_Material_MT_Setting = mat.sublender
        if (m_sublender is not None) and (m_sublender.graph_url is not "") and (m_sublender.package_path is not ""):
            dynamic_gen_clss(m_sublender.package_path, m_sublender.graph_url)


def load_material_templates():
    template_path = os.path.join(SUBLENDER_DIR, 'templates')
    files = os.listdir(template_path)
    for file_name_full in files:
        full_file_path = os.path.join(template_path, file_name_full)
        if os.path.isfile(full_file_path):
            file_name, file_ext = os.path.splitext(file_name_full)
            if file_ext == ".json":
                with open(full_file_path, 'r') as f:
                    material_temp = json.load(f)
                    material_templates[file_name_full] = material_temp
                    material_template_enum.append((
                        file_name_full,
                        file_name,
                        file_name_full
                    ))


def init_system():
    sublender_settings: SublenderSetting = bpy.context.scene.sublender_settings
    if sublender_settings.uuid == "":
        import uuid
        sublender_settings.uuid = str(uuid.uuid4())
    Path(SUBLENDER_DIR).mkdir(parents=True, exist_ok=True)


def register():
    load_material_templates()
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.sublender_settings = bpy.props.PointerProperty(
        type=SublenderSetting, name="Sublender")
    bpy.types.Material.sublender = bpy.props.PointerProperty(
        type=Sublender_Material_MT_Setting)
    init_system()
    load_sbsar()


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    print("Goodbye World")


if __name__ == "__main__":
    # unregister()
    register()
