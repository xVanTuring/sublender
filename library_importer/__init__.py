import bpy
from .sublender_ot_select_sbsar_to_library import SublenderOTSelectSbsarToLibrary
from .sublender_ot_import_graphs_to_library import SublenderOTImportGraphsToLibrary
from .sublender_ot_parse_selected_sbsars_to_library import SublenderOTParseSelectedSbsarsToLibrary

cls_list = [
    SublenderOTImportGraphsToLibrary,
    SublenderOTParseSelectedSbsarsToLibrary,
    SublenderOTSelectSbsarToLibrary,
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
