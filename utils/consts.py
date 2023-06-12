import os

UNGROUPED = '$UNGROUPED$'
SBS_CONFIGURED = "$CONFIGURED"
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
    ("13", "8192", "8192"),
]

ADDON_DIR = os.path.join(os.path.dirname(__file__), "../")

WORKFLOW_PATH = os.path.join(ADDON_DIR, 'workflow')
RESOURCES_PATH = os.path.join(ADDON_DIR, 'resources')

output_size_x = "$sb_output_size_x"
output_size_y = "$sb_output_size_y"
output_size_lock = "$sb_output_size_lock"
update_when_sizing = "$update_when_sizing"
usage_color_dict = ['baseColor', 'ambientOcclusion']

sublender_default_template_file = "preview_template.blend"
sublender_template_invert_file = "preview_template_invert.blend"

sublender_cloth_template_file = "preview_cloth_template.blend"
sublender_cloth_template_invert_file = "preview_cloth_template_invert.blend"
old_sublender_template_path = "old"


def get_template(type, inverted_normal, old):
    file_folder = os.path.join(ADDON_DIR, 'resources', old_sublender_template_path if old else '')
    file_name = ''
    if type == "shader_ball":
        if inverted_normal:
            file_name = 'preview_template_invert'
        else:
            file_name = 'preview_template'
    elif type == "cloth":
        if inverted_normal:
            file_name = 'preview_cloth_template_invert'
        else:
            file_name = 'preview_cloth_template'
    file_name += ".blend"
    return os.path.join(file_folder, file_name)
