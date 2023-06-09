from .. import utils


class SublenderBaseOperator(object):
    @classmethod
    def poll(cls, context):
        return utils.find_active_mat(context) is not None