import bpy
mat = bpy.data.materials['Cedar White Wood']
material_config = {
    "nodes": [
        {
            "type": "ShaderNodeOutputMaterial",
            "name": "Material Output",
            "label": "Material Output",
            "location": [
                448,
                0
            ]
        },
        {
            "type": "ShaderNodeBsdfPrincipled",
            "name": "Principled BSDF",
            "label": "Principled BSDF",
            "location": [
                28,
                0
            ]
        },
        {
            "type": "ShaderNodeTexImage",
            "name": "baseColor",
            "label": "Base Color",
            "location": [
                -371,
                -106
            ],
            "hide": True
        },
        {
            "type": "ShaderNodeTexImage",
            "name": "metallic",
            "label": "Metallic",
            "location": [
                -371,
                -192
            ],
            "hide": True
        },
        {
            "type": "ShaderNodeTexImage",
            "name": "roughness",
            "label": "Roughness",
            "location": [
                -371,
                -259
            ],
            "hide": True
        },
        {
            "type": "ShaderNodeNormalMap",
            "name": "Normal Map",
            "label": "Normal Map",
            "hide": True,
            "location": [-195, -506]
        },
        {
            "type": "ShaderNodeTexImage",
            "name": "normal",
            "label": "Normal",
            "hide": True,
            "location": [-483, -506]
        }
    ],
    "links": [
        {
            "fromNode": "Principled BSDF",
            "toNode": "Material Output",
            "fromSocket": "BSDF",
            "toSocket": "Surface"
        },
        {
            "fromNode": "baseColor",
            "toNode": "Principled BSDF",
            "fromSocket": "Color",
            "toSocket": "Base Color"
        },
        {
            "fromNode": "metallic",
            "fromSocket": "Color",
            "toNode": "Principled BSDF",
            "toSocket": "Metallic"
        },
        {
            "fromNode": "roughness",
            "fromSocket": "Color",
            "toNode": "Principled BSDF",
            "toSocket": "Roughness"
        },
        {
            "fromNode": "normal",
            "fromSocket": "Color",
            "toNode": "Normal Map",
            "toSocket": "Color"
        },
        {
            "fromNode": "Normal Map",
            "fromSocket": "Normal",
            "toNode": "Principled BSDF",
            "toSocket": "Normal"
        }
    ],
    "texture": [
        {
            "type": "baseColor",
            "node": "baseColor"
        },
        {
            "type": "metallic",
            "node": "metallic",
            "colorspace": "Non-Color"
        },
        {
            "type": "roughness",
            "node": "roughness",
            "colorspace": "Non-Color"
        },
        {
            "type": "normal",
            "node": "normal",
            "colorspace": "Non-Color"
        }
    ]
}


def isType(val, type_str):
    return isinstance(val, getattr(bpy.types, type_str))


node_list = mat.node_tree.nodes
node_links = mat.node_tree.links


def ensureNodes():
    for node_info in material_config['nodes']:
        node_inst = node_list.get(node_info['name'])
        if (node_inst is not None) and (isType(node_inst, node_info['type'])):
            continue
        node_inst = node_list.new(type=node_info['type'])
        node_inst.name = node_info['name']
        if node_info.get('label', None) is not None:
            node_inst.label = node_info['label']
        if node_info.get('location', None) is not None:
            node_inst.location = node_info['location']
        if node_info.get('hide') == True:
            node_inst.hide = True


ensureNodes()


def make_link():
    for link in material_config['links']:
        from_node = node_list.get(link['fromNode'])
        to_node = node_list.get(link['toNode'])
        node_links.new(
            from_node.outputs[link['fromSocket']], to_node.inputs[link['toSocket']])


make_link()

resource_dict = {
    'baseColor': r"C:\Users\xVan\.sublender\484837db-4840-4b09-b470-6671c9fec292\sublender_pkg_wood_planks_aged\sa_aged_wood_planks_wood_planks_aged_basecolor.png",
    'metallic': r"C:\Users\xVan\.sublender\484837db-4840-4b09-b470-6671c9fec292\sublender_pkg_wood_planks_aged\sa_aged_wood_planks_wood_planks_aged_metallic.png",
    'roughness': r"C:\Users\xVan\.sublender\484837db-4840-4b09-b470-6671c9fec292\sublender_pkg_wood_planks_aged\sa_aged_wood_planks_wood_planks_aged_roughness.png",
    'normal': r"C:\Users\xVan\.sublender\484837db-4840-4b09-b470-6671c9fec292\sublender_pkg_wood_planks_aged\sa_aged_wood_planks_wood_planks_aged_normal.png"
}


def assign_texture():
    for texture_info in material_config['texture']:
        texture_path = resource_dict.get(texture_info['type'])
        if texture_path is not None:
            image_name = bpy.path.basename(texture_path)
            bpy.ops.image.open(filepath=texture_path)
            target_Node = node_list.get(texture_info['node'])
            texture_img = bpy.data.images.get(image_name)
            if texture_info.get('colorspace') is not None:
                texture_img.colorspace_settings.name = texture_info.get(
                    'colorspace')
            if target_Node is not None:
                target_Node.image = texture_img
            else:
                print("Missing Node:{0}".format(texture_info['node']))
        else:
            print("Missing Texture:{0}".format(texture_info['type']))


assign_texture()


# bpy.ops.node.add_node(type="ShaderNodeGroup", use_transform=True, settings=[{"name":"node_tree", "value":"bpy.data.node_groups['DirectX To OpenGL']"}])
