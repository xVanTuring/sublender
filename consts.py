import os

from bpy.props import (StringProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)

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
SBS_CONFIGURED = "$CONFIGURED"
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
    (StringProperty, None),
    (StringProperty, None),
    (None, None),
    (IntVectorProperty, 2),
    (IntVectorProperty, 3),
    (IntVectorProperty, 4),
]
CUSTOM = "$CUSTOM$"
output_size_one_enum = [
    ("0", "1", "1"),
    ("1", "2", "2"),
    ("2", "4", "4"),
    ("3", "8", "8"),
    ("4", "16", "16"),
    ("5", "32", "32"),
    ("6", "64", "64"),
    ("7", "128", "128"),
    ("8", "256", "256"),
    ("9", "512", "512"),
    ("10", "1024", "1024"),
    ("11", "2048", "2048"),
    ("12", "4096", "4096"),
    ("13", "8192", "8192")
]
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

ADDON_DIR = os.path.dirname(__file__)

TEMPLATE_PATH = os.path.join(ADDON_DIR, 'workflows')
RESOURCES_PATH = os.path.join(ADDON_DIR, 'resources')
output_size_x = "$sb_output_size_x"
output_size_y = "$sb_output_size_y"
output_size_lock = "$sb_output_size_lock"
update_when_sizing = "$update_when_sizing"
usage_color_dict = ['baseColor',
                    'ambientOcclusion']
usage_to_label = {
    'baseColor': 'Base Color',
    'metallic': 'Metallic',
    'roughness': 'Roughness',
    'normal': 'Normal',
    'ambientOcclusion': 'Ambient Occlusion',
    'height': 'Height'
}

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
sublender_library_dir = os.path.expanduser("~/Documents/Sublender")
sublender_library_config_file = os.path.join(sublender_library_dir, "config.json")
sublender_library_render_dir = os.path.join(sublender_library_dir, "template")
sublender_library_render_template_file = os.path.join(sublender_library_render_dir, "preview_template.blend")

sublender_preview_img_template_file = os.path.join(sublender_library_render_dir, "out#.png")
sublender_preview_img_file = os.path.join(sublender_library_render_dir, "out1.png")

packed_sublender_template_file = os.path.join(ADDON_DIR, 'resources', 'preview_template.blend')
