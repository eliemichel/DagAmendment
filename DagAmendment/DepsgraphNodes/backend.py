# This file is part of DagAmendment, the reference implementation of:
#
#   Michel, Élie and Boubekeur, Tamy (2021).
#   DAG Amendment for Inverse Control of Parametric Shapes
#   ACM Transactions on Graphics (Proc. SIGGRAPH 2021), 173:1-173:14.
#
# Copyright (c) 2020-2021 -- Télécom Paris (Élie Michel <elie.michel@telecom-paris.fr>)
# 
# DagAmendment is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# DagAmendment is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with DagAmendment.  If not, see <https://www.gnu.org/licenses/>.

import bpy

# -------------------------------------------------------------------

def make_node(G, type, parent, variant=None, hide=False):
    ident = f"{type}@{parent}"
    full_parent = parent
    if variant is not None:
        ident += f"#{variant}"
        full_parent += f"#{variant}"

    node = G.nodes.get(ident)
    if node is not None:
        return node

    node = G.nodes.new(type=type)
    node.entity_name = full_parent
    node.name = ident
    node.hide = hide

    node.subtype = type
    node.objname = parent if parent is not None else ""
    node.variant = variant if variant is not None else ""
    return node

# -------------------------------------------------------------------

def make_transform_node(G, obj, prop):
    x = make_node(G, prop + 'X', obj.name, hide=True)
    y = make_node(G, prop + 'Y', obj.name, hide=True)
    z = make_node(G, prop + 'Z', obj.name, hide=True)
    prop = make_node(G, prop, obj.name, hide=True)
    G.links.new(x.outputs[0], prop.inputs["X"])
    G.links.new(y.outputs[0], prop.inputs["Y"])
    G.links.new(z.outputs[0], prop.inputs["Z"])
    return prop

# -------------------------------------------------------------------

def add_xform_nodes(G, context):
    for o in context.view_layer.objects:
        T = make_transform_node(G, o, 'PROP:T')
        R = make_transform_node(G, o, 'PROP:R')
        S = make_transform_node(G, o, 'PROP:S')
        xform = make_node(G, 'PROP:XFORM', o.name)  # evaluated TRS
        if o.parent is None:
            op_xform = make_node(G, 'OP:XFORM', o.name)
        else:
            op_xform = make_node(G, 'OP:XFORM', o.name)
            
        G.links.new(T.outputs[0], op_xform.inputs["T"])
        G.links.new(R.outputs[0], op_xform.inputs["R"])
        G.links.new(S.outputs[0], op_xform.inputs["S"])
        G.links.new(op_xform.outputs[0], xform.inputs[0])
        if o.parent is not None:
            parent_xform = make_node(G, 'PROP:XFORM', o.parent.name)
            G.links.new(parent_xform.outputs[0], op_xform.inputs["parent"])

# -------------------------------------------------------------------

def make_modifier_node(G, obj, modifier):
    unary_operators = {
        'SUBSURF',
        'MIRROR', # Account for center object (xform)
        'SOLIDIFY',
        'SCREW',
        'HOOK', # Account for hook object (xform)
        'ARRAY',  # Account for offset object (xform) and end caps (meshes)
        'DISPLACE',
        'BEVEL',
        'UV_WARP',
    }
    other_obj = None
    if modifier.type == 'BOOLEAN':
        mod = make_node(G, 'OP:MODIFIER_DUARY', obj.name, variant=modifier.name)
        other_obj = modifier.object
    else:
        if modifier.type not in unary_operators:
            print(f"Warning: Unknown modifier '{modifier.type}', treated as unary")
        mod = make_node(G, 'OP:MODIFIER_UNARY', obj.name, variant=modifier.name)
    return mod, other_obj

# -------------------------------------------------------------------

def add_mesh_nodes(G, context):
    view_layer_node = make_node(G, 'OTHER:VIEW_LAYER', context.view_layer.name)
    i = 0
    for o in context.view_layer.objects:
        if o.type != 'MESH':
            continue

        mesh = make_node(G, 'PROP:MESH', o.data.name)
        mod = mesh
        
        for m in o.modifiers:
            prev_mod = mod
            mod, other_obj = make_modifier_node(G, o, m)
            if other_obj is not None:
                other_out_mesh = make_node(G, 'PROP:OUT_MESH', other_obj.name)
                G.links.new(other_out_mesh.outputs[0], mod.inputs[1])
            G.links.new(prev_mod.outputs[0], mod.inputs[0])
        
        xform = make_node(G, 'PROP:XFORM', o.name)
        out_mesh = make_node(G, 'PROP:OUT_MESH', o.name)
        op_transform_mesh = make_node(G, 'OP:XFORM_MESH', o.name)

        G.links.new(mod.outputs[0], op_transform_mesh.inputs["mesh"])
        G.links.new(xform.outputs[0], op_transform_mesh.inputs["xform"])
        G.links.new(op_transform_mesh.outputs[0], out_mesh.inputs[0])

        view_layer_input = view_layer_node.inputs.new('MeshDependencySocket', f"mesh{i}")
        G.links.new(out_mesh.outputs[0], view_layer_input)
        i += 1

# -------------------------------------------------------------------

def add_driver_nodes(G, context):
    for o in context.scene.objects:
        if o.animation_data is None:
            continue
        for i, drv in enumerate(o.animation_data.drivers):
            drv.data_path # e.g. 'modifiers["Boolean"].double_threshold'
            tokens = sum([t.split(']') for t in drv.data_path.split('[')], [])
            if tokens[0] == "modifiers":
                m = o.modifiers[tokens[1].strip('"')]
                driven, other_obj = make_modifier_node(G, o, m)
            elif tokens[0] == "location":
                axis = ['X', 'Y', 'Z'][drv.array_index]
                driven = make_node(G, 'PROP:T'+axis, o.name)
            elif tokens[0] == "rotation_euler":
                axis = ['X', 'Y', 'Z'][drv.array_index]
                driven = make_node(G, 'PROP:R'+axis, o.name)
            elif tokens[0] == "scale":
                axis = ['X', 'Y', 'Z'][drv.array_index]
                driven = make_node(G, 'PROP:S'+axis, o.name)
            else:
                print(f"Unable to parse driven property '{drv.data_path}', skipping.")
                continue

            driver = make_node(G, 'OP:DRIVER', o.name, variant=str(i))
            driven.ensure_driver_input()
            G.links.new(driver.outputs[0], driven.inputs["driver"])

            variable_slots = []
            for var in drv.driver.variables:
                var.type # e.g. 'SINGLE_PROP'
                for tgt in var.targets:
                    parent_name = tgt.id.name
                    tgt.data_path # e.g. 'location[0]'
                    tokens = sum([t.split(']') for t in tgt.data_path.split('[')], [])
                    if tokens[0] == 'location':
                        axis = ['X', 'Y', 'Z'][int(tokens[1])]
                        source = make_node(G, 'PROP:T'+axis, parent_name)
                    elif tokens[0] == 'rotation_euler':
                        axis = ['X', 'Y', 'Z'][int(tokens[1])]
                        source = make_node(G, 'PROP:R'+axis, parent_name)
                    elif tokens[0] == 'scale':
                        axis = ['X', 'Y', 'Z'][int(tokens[1])]
                        source = make_node(G, 'PROP:S'+axis, parent_name)
                    else:
                        print(f"Unable to parse driver source '{tgt.data_path}' (var type '{var.type}'), skipping.")
                        continue
                    variable_slots.append(source.outputs[0])

            driver.set_variable_count(len(variable_slots))
            for i, s in enumerate(variable_slots):
                G.links.new(s, driver.inputs[i])

# -------------------------------------------------------------------

def add_parameter_nodes(G, context):
    for param in context.scene.diffparam_parameters:
        pnode = make_node(G, 'PARAM', param.name)
        pnode.use_custom_color = True
        pnode.color = (0.0, 0.603827, 0.610496)

        axis = ['X', 'Y', 'Z', 'W'][param.index]
        if param.prop == 'location':
            driven = make_node(G, 'PROP:T'+axis, param.obj.name)
        elif param.prop == 'rotation_euler':
            driven = make_node(G, 'PROP:R'+axis, param.obj.name)
        elif param.prop == 'scale':
            driven = make_node(G, 'PROP:S'+axis, param.obj.name)
        else:
            print(f"Unknown property: {param.prop}, skipping.")
            return
        driven.ensure_driver_input()
        G.links.new(pnode.outputs[0], driven.inputs["driver"])

# -------------------------------------------------------------------

def update_graph(G, context):
    G.nodes.clear()
    add_xform_nodes(G, context)
    add_mesh_nodes(G, context)
    add_driver_nodes(G, context)
    if hasattr(context.scene, 'diffparam_parameters'):
        add_parameter_nodes(G, context)
