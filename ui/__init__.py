from bpy.types import Panel
from . import library, mainpanel, output, prop
from .. import utils


class SublenderPTPropBase(Panel):
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Sublender'
    bl_options = {'DEFAULT_CLOSED'}
    graph_url = ""
    group_info = None

    @classmethod
    def poll(cls, context):
        if not utils.sublender_inited(context) or len(utils.globalvar.graph_enum) == 0:
            return False
        preferences = context.preferences.addons["sublender"].preferences
        if preferences.hide_channels and cls.bl_label == "Channels":
            return False
        active_mat, active_graph = utils.find_active_graph(context)
        if active_mat is None or active_graph is None:
            return False
        if active_graph == cls.graph_url and not active_mat.sublender.package_missing:
            if preferences.enable_visible_if:
                clss_name = utils.gen_clss_name(cls.graph_url)
                if utils.globalvar.eval_delegate_map.get(active_mat.name) is None:
                    utils.globalvar.eval_delegate_map[active_mat.name] = utils.EvalDelegate(active_mat.name, clss_name)
                else:
                    # assign again, undo/redo will change the memory address
                    utils.globalvar.eval_delegate_map[active_mat.name].graph_setting = getattr(active_mat, clss_name)
                visible = calc_group_visibility(utils.globalvar.eval_delegate_map.get(active_mat.name), cls.group_info)
                return visible
            return True
        return False

    def draw(self, context):
        layout = self.layout
        target_mat = utils.find_active_mat(context)
        sublender_setting = target_mat.sublender
        clss_name = utils.gen_clss_name(sublender_setting.graph_url)
        graph_setting = getattr(target_mat, clss_name)
        preferences = context.preferences.addons["sublender"].preferences
        eval_dele = utils.globalvar.eval_delegate_map.get(target_mat.name)
        for prop_info in self.group_info['inputs']:
            if prop_info.get('identifier') == '$outputsize':
                row = layout.row()
                row.prop(graph_setting, utils.consts.output_size_x, text='Size')
                row.prop(graph_setting, utils.consts.output_size_lock, toggle=1, icon_only=True, icon="LINKED")
                if getattr(graph_setting, utils.consts.output_size_lock):
                    row.prop(graph_setting, utils.consts.output_size_x, text='')
                else:
                    row.prop(graph_setting, utils.consts.output_size_y, text='')
                if context.scene.sublender_settings.live_update:
                    row.prop(graph_setting,
                             utils.consts.update_when_sizing,
                             toggle=1,
                             icon_only=True,
                             icon="UV_SYNC_SELECT")
            elif prop_info.get('identifier') == "$randomseed":
                row = layout.row()
                row.prop(graph_setting, prop_info['prop'], text=prop_info['label'])
                row.operator('sublender.randomseed', icon="LIGHT_DATA", text="")
            else:
                if preferences.enable_visible_if:
                    visible = calc_prop_visibility(eval_dele, prop_info)
                    if not visible:
                        continue
                toggle = -1
                if prop_info.get('togglebutton', False):
                    toggle = 1
                layout.prop(graph_setting, prop_info['prop'], text=prop_info['label'], toggle=toggle)


mod_list = [library, mainpanel, output, prop]


def register():
    for mod in mod_list:
        mod.register()


def unregister():
    for mod in mod_list:
        mod.unregister()