from .. import utils


class SublenderBaseOperator(object):
    @classmethod
    def poll(cls, context):
        return utils.find_active_material(context) is not None
