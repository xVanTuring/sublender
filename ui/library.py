import bpy
from .. import utils


class SUBLENDER_PT_Library(bpy.types.Panel):
    bl_label = "Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sublender"
    bl_order = 1

    def draw(self, context):
        self.layout.operator(
            "sublender.select_sbsar_to_library",
            icon="IMPORT",
            text="Import to Library",
        )
        if len(utils.globalvar.library_category_material_map["$ALL$"]) > 0:
            properties = context.scene.sublender_library
            self.layout.prop(properties, "categories", text="")
            if (
                len(
                    utils.globalvar.library_category_material_map.get(
                        properties.categories, []
                    )
                )
                == 0
            ):
                self.layout.box().label(text="No material is in this category")
                return
            active_material = properties.active_material
            row = self.layout.row()
            row.template_icon_view(properties, "active_material", show_labels=True)
            has_presets = (
                len(
                    utils.globalvar.library_material_preset_map.get(active_material, [])
                )
                > 0
            )
            if has_presets:
                row.template_icon_view(properties, "material_preset", show_labels=True)
            row = self.layout.row()
            import_sbsar_operator = row.operator("sublender.import_sbsar")
            import_sbsar_operator.from_library = True
            row.operator("sublender.remove_material", icon="PANEL_CLOSE")
            active_mat = utils.find_active_mat(context)
            if active_mat is not None:
                material_id = active_mat.sublender.library_uid
                if material_id != "" and material_id == active_material:
                    row = self.layout.row()
                    row.operator("sublender.apply_preset")
                    if has_presets and properties.material_preset != "$DEFAULT$":
                        row.operator("sublender.save_to_preset")


cls_list = [SUBLENDER_PT_Library]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
