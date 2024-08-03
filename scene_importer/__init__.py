import bpy

from .sublender_ot_select_sbsar import SublenderOTSelectSbsar
from .sublender_ot_import_sbsar import SublenderOTImportSbsar
from .sublender_ot_import_graph import SublenderOTImportGraph
from .sublender_ot_import_sbsar_from_library import SublenderOTImportSbsarFromLibrary

cls_list = [
    SublenderOTImportGraph,
    SublenderOTImportSbsar,
    SublenderOTSelectSbsar,
    SublenderOTImportSbsarFromLibrary
]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
