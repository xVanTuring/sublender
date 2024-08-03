import pathlib
import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper


class SublenderOTSelectSbsarToLibrary(bpy.types.Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar_to_library"
    bl_label = "Import Sbsar to Library"
    bl_description = "Import Sbsar to Library"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(default="*.sbsar", options={"HIDDEN"}, maxlen=255)
    # https://gist.github.com/batFINGER/2c0604be3620def01c4eeaff6ceb22f4
    files: CollectionProperty(
        name="Sbsar files", type=bpy.types.OperatorFileListElement
    )
    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context):
        return len(context.scene.sublender_library.importing_graphs) == 0

    def execute(self, context):
        files_str = ""
        importing_graphs = context.scene.sublender_library.importing_graphs
        importing_graphs.clear()
        for file in self.files:
            if pathlib.Path(file.name).suffix != ".sbsar":
                self.report({"WARNING"}, "File extension doesn't match")
                continue
            files_str += "%s|" % str(pathlib.Path(self.directory, file.name))
        bpy.ops.sublender.parse_selected_sbsars_to_library(files_list=files_str)
        return {"FINISHED"}
