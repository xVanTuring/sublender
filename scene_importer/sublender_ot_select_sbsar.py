import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper


class SublenderOTSelectSbsar(bpy.types.Operator, ImportHelper):
    bl_idname = "sublender.select_sbsar"
    bl_label = "Import Sbsar"
    bl_description = "Import Sbsar"
    filename_ext = ".sbsar"
    filter_glob: StringProperty(default="*.sbsar", options={"HIDDEN"}, maxlen=255)
    directory: StringProperty(subtype='DIR_PATH')
    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    @classmethod
    def poll(cls, _):
        return not bpy.data.filepath == ""

    def execute(self, _):
        import os
        if self.files:
            file_paths = list(map(lambda x: os.path.join(self.directory, x.name), self.files))
            bpy.ops.sublender.import_sbsar(sbsar_paths="|".join(file_paths))
            return {"FINISHED"}
        else:
            bpy.ops.sublender.import_sbsar(sbsar_paths=self.filepath)
            return {"FINISHED"}
