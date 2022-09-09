from bpy.props import (PointerProperty, StringProperty, BoolProperty, CollectionProperty,
                       EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, IntVectorProperty)
type_dict = ['FLOAT1',
             'FLOAT2',
             'FLOAT3',
             'FLOAT4',
             'INTEGER1',
             'IMAGE',
             'STRING',
             'FONT',
             'INTEGER2',
             'INTEGER3',
             'INTEGER4', ]
UNGROUPED = '$UNGROUPED$'

sbsar_name_prop = {
    '$outputsize': 'output_size',
    '$randomseed': 'random_seed'
}
sbsar_name_to_label = {
    '$outputsize': 'Output Size',
    '$randomseed': 'Random Seed'
}
sbsar_type_to_property = [
    (FloatProperty, None,),
    (FloatVectorProperty, 2,),
    (FloatVectorProperty, 3,),
    (FloatVectorProperty, 4,),
    (IntProperty, None),
    (None, None),
    (StringProperty, None),
    (None, None),
    (IntVectorProperty, 2),
    (IntVectorProperty, 3),
    (IntVectorProperty, 4),
]
