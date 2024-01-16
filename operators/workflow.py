import bpy

from .base import SublenderBaseOperator
from .. import utils, workflow


class SublenderOTApplyWorkflow(SublenderBaseOperator, bpy.types.Operator):
    bl_idname = "sublender.apply_workflow"
    bl_label = "Apply Workflow"
    bl_description = "Apply Workflow, this will remove all existing nodes"

    def execute(self, context):
        material_inst = utils.find_active_mat(context)
        mat_setting = material_inst.sublender
        workflow_name: str = mat_setting.material_template
        self.report({"INFO"}, "Inflating material {0}".format(material_inst.name))

        material_template = utils.globalvar.material_templates.get(mat_setting.material_template)
        clss_name = utils.format.gen_clss_name(mat_setting.graph_url)
        clss_info = utils.globalvar.graph_clss.get(clss_name)
        output_info_usage: dict = clss_info['output_info']['usage']
        graph_setting = getattr(material_inst, clss_name)

        setattr(graph_setting, utils.consts.SBS_CONFIGURED, False)
        if workflow_name != utils.consts.CUSTOM:
            for template_texture in material_template['texture']:
                if output_info_usage.get(template_texture) is not None:
                    name = output_info_usage.get(template_texture)[0]
                    setattr(graph_setting, utils.format.sb_output_to_prop(name), True)
            setattr(graph_setting, utils.consts.SBS_CONFIGURED, True)
            workflow.inflate_template(material_inst, workflow_name, True)
        else:
            for output_info in clss_info['output_info']['list']:
                setattr(graph_setting, utils.format.sb_output_to_prop(output_info['name']), True)
        setattr(graph_setting, utils.consts.SBS_CONFIGURED, True)
        bpy.ops.sublender.render_texture_async(importing_graph=False, texture_name='')
        return {'FINISHED'}


cls_list = [SublenderOTApplyWorkflow]


def register():
    for cls in cls_list:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(cls_list):
        bpy.utils.unregister_class(cls)
