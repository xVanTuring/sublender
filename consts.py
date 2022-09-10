from bpy.props import (PointerProperty, StringProperty, BoolProperty, CollectionProperty,
                       EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)
import pathlib
import os
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
CUSTOM = "$CUSTOM$"
output_size_enum = [
    ("1", "1x1", "1x1"),
    ("2", "2x2", "2x2"),
    ("4", "4x4", "4x4"),
    ("8", "8x8", "8x8"),
    ("16", "16x16", "16x16"),
    ("32", "32x32", "32x32"),
    ("64", "64x64", "64x64"),
    ("128", "128x128", "128x128"),
    ("256", "256x256", "256x256"),
    ("512", "512x512", "512x512"),
    ("1024", "1024x1024", "1024x1024"),
    ("2048", "2048x2048", "2048x2048"),
    ("4096", "4096x4096", "4096x4096"),
    ("8192", "8192x8192", "8192x8192"),
    (CUSTOM, "Custom", "Custom"),
]

HOME = str(pathlib.Path.home())
SUBLENDER_DIR = os.path.join(HOME, ".sublender")
ADDON_DIR = os.path.dirname(__file__)

TEMPLATE_PATH = os.path.join(ADDON_DIR, 'workflows')
