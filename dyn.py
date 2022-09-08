import bpy
from bpy.utils import register_class
from bpy.props import PointerProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty
from bpy.types import Panel, Operator, Menu
from rna_prop_ui import rna_idprop_quote_path, rna_idprop_ui_get, rna_idprop_context_value, rna_idprop_value_item_type, rna_idprop_ui_prop_update
from bpy.utils import escape_identifier



class Sublender_Material_MT_Setting(bpy.types.PropertyGroup):
    graph_url: bpy.props.StringProperty(name="Graph URL")


class Sublender_PT_Main(Panel):
    bl_label = "Sublender"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'

    def draw(self, context):
        # props = self.layout.operator("sub.mt_add", text="Add")
        mat = bpy.data.materials['Material']
        if mat.sublender_graph != "":
            print("1")
        self.layout.prop(mat.pkg_abc, 'Color')
        self.layout.prop(mat.pkg_abc, 'Output_Size')
        self.layout.prop(mat.pkg_abc, 'Normal_Map_Type')


def auto_gen():
    clss = type('pkg_abc', (bpy.types.PropertyGroup,), {
        '__annotations__': {
            'Color': (FloatVectorProperty, {
                'default': [.0, .1, .1],
                'subtype': 'COLOR',
                'max': 1.0,
                'min': 0.0}),
            'Output_Size': (IntVectorProperty, {
                'default': [0, 0],
                'size': 2,
                'max': 4096,
                'min': 1
            }),
            'Normal_Map_Type': (EnumProperty, {
                'default': 'DirectX',
                'items': [('DirectX', 'DirectX', 'DirectX'), ('OpenGL', 'OpenGL', 'OpenGL')],
            })
        }
    })
    bpy.utils.register_class(clss)
    bpy.types.Material.pkg_abc = bpy.props.PointerProperty(
        type=clss)


bpy.utils.register_class(Sublender_PT_Main)
bpy.utils.register_class(Sublender_Material_MT_Setting)
bpy.types.Material.sublender_graph = StringProperty(name="Sublender Graph")
auto_gen()
