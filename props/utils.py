import bpy


def get_idx(enum_items, name: str):
    def get_x(self):
        if callable(enum_items):
            len_of_x = len(enum_items(self, bpy.context))
        else:
            len_of_x = len(enum_items)
        if name in self:
            if len_of_x <= self[name]:
                if len_of_x > 0:
                    return 0
                return 0
            return self[name]
        elif len_of_x > 0:
            return 0
        return 0

    return get_x


def set_idx(name):
    def setter(self, value):
        self[name] = value

    return setter
