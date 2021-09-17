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
from bpy.types import Operator
from bpy.props import (
    PointerProperty, IntProperty, EnumProperty, BoolProperty,
    FloatProperty, FloatVectorProperty,
)

# -------------------------------------------------------------------

class DagAmendment(Operator):
    """Edit the whole scene to ensure that UV+object index+material
    index uniquely identifies any point of a surface."""
    bl_idname = "diffparam.dag_amendment"
    bl_label = "Dag Amendment"
    bl_options = {'REGISTER', 'UNDO'}

    update_graph: BoolProperty(
        name = "Update Graph",
        description = "Recompute depsgraph nodes before applying update (otherwise call it manually)",
        default = True
    )

    update_leaf_parameter: BoolProperty(
        name = "Update UVs",
        description = "Initialize overlap free UVs at leaf nodes",
        default = True
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        # We build a graph-based representation of Blender's underlying scene,
        # so that we can run our DAG amendment on it in a more unified way.
        if not hasattr(bpy.ops, "depsgraph_nodes"):
            self.report({'ERROR'}, "This operator requires the DepsgraphNode add-on")
        if self.update_graph:
            bpy.ops.depsgraph_nodes.update()
        graph = bpy.data.node_groups.get('DEPSGRAPH')
        
        # Here "root" means the output of the DAG whereas "leaf" means
        # a generator node, that has no input.
        root_node = graph.nodes[f"OTHER:VIEW_LAYER@{context.view_layer.name}"]

        ### Global outline: ###

        # 1. We cound how many paths each node produces
        self.reset_path_counts_rec(root_node)
        self.count_paths_rec(root_node)

        # 2. If asked, we reset the leaf parameter to ensure that it does not
        # overlap (calling a naive parameterization used for light maps, no
        # need to care about distorsion, this parameterization is not use for
        # texturing but only for recognizing points when hyper-parameters change).
        if self.update_leaf_parameter:
            self.init_leaf_parameters_rec(context, root_node)

        # 3. Perform DAG amendment
        self.insert_nodes_rec(root_node)

        return {'FINISHED'}

    def get_mesh_inputs(self, node):
        """Get the list of node inputs that carry mesh data. Others may be floats or
        matrices and are not important for the DAG amendment."""
        return [ input for input in node.inputs if input.name.startswith("mesh") ]

    def get_node_duplication_count(self, node):
        """return the maximum number of duplication that the node may produce"""
        if node.subtype == 'OP:MODIFIER_UNARY':
            mod = bpy.data.objects[node.objname].modifiers[node.variant]
            mod_type = mod.type
            if mod_type == 'MIRROR':
                return 2
            elif mod_type == 'ARRAY':
                # This assumes the number of duplications is not affected by hyper params
                # TODO: visit the graph to determine if it is actually the case
                return mod.count
            elif mod_type == 'SOLIDIFY':
                self.report({'WARNING'}, f"Solidify modifier creates overlap in UVs, consider applying it and using hook. (object '{node.objname}')")
            elif mod_type == 'SCREW':
                self.report({'WARNING'}, f"Screw modifier creates overlap in UVs, prefer using shape keys. (object '{node.objname}')")

        return 1

    def reset_path_counts_rec(self, node):
        node.path_count = -1

        mesh_inputs = self.get_mesh_inputs(node)
        for input in mesh_inputs:
            for nlinks in input.links:
                self.reset_path_counts_rec(nlinks.from_node)
        

    def count_paths_rec(self, node):
        """Count paths flowing out of "node" and memoize it in node.path_count."""

        # If not -1, it means there is already a memoized value, we simply use it
        if node.path_count != -1:
            return node.path_count

        mesh_inputs = self.get_mesh_inputs(node)
        if len(mesh_inputs) == 0:
            node.path_count = 1
            return 1

        path_count = 0
        for input in mesh_inputs:
            for nlinks in input.links:
                path_count += self.count_paths_rec(nlinks.from_node)

        path_count *= self.get_node_duplication_count(node)

        node.path_count = path_count
        return path_count

    def insert_nodes_rec(self, node):
        """When possible, we use the built in options that modifier expose
        to offset UVs rather than actually creating a new one."""
        mesh_inputs = self.get_mesh_inputs(node)
        duplication_count = self.get_node_duplication_count(node)

        # Only nodes that correspond to modifier may need amendment, other
        # ones (like local-to-world transform) simply forward attributes.
        is_modifier = node.subtype in {'OP:MODIFIER_UNARY','OP:MODIFIER_DUARY'}

        if is_modifier:
            obj = bpy.data.objects[node.objname]
            mod = obj.modifiers[node.variant]
            mod_idx = obj.modifiers.find(node.variant)
            mod_type = mod.type
            if mod_type == 'MIRROR':
                # offset by the number of incoming paths
                mod.offset_u = node.path_count / duplication_count

            if mod_type == 'ARRAY':
                # For some unexplainable reason 'offset_u' is stuck within [-1,1]
                # for the array modifier so we trick it by scaling UVs before and
                # after the operation
                before_mod = self.insert_path_index_mod_before(obj, mod_idx)
                mod_idx = obj.modifiers.find(node.variant)
                after_mod = self.insert_path_index_mod_after(obj, mod_idx)

                offset = node.path_count / duplication_count
                before_mod.scale[0] = 1 / offset
                mod.offset_u = 1
                after_mod.scale[0] = offset

            elif mod_type == 'BOOLEAN':
                # it is more convenient to consider the reminder of the
                # modifier stack of this object as the secondary input
                # i.e. the one that must have its UV offset
                other_node = mesh_inputs[1].links[0].from_node

                extra_mod = self.insert_path_index_mod_before(obj, mod_idx)
                extra_mod.offset[0] = other_node.path_count


        # recursive calls
        for input in mesh_inputs:
            for nlinks in input.links:
                self.insert_nodes_rec(nlinks.from_node)

    def insert_path_index_mod_before(self, obj, mod_idx):
        """Ensure that there is a "path index modifier" in the stack just before
        the modifier number "mod_idx" of object "obj". A "path index modifier" is
        a modifier that offsets the path index (in effect, that offsets the UV
        because we encore the path index into a global integer translation of the UVs)
        If the modifier already exists, we just return it (we recognize it based
        on its name)."""
        if mod_idx > 0:
            prev_mod = obj.modifiers[mod_idx - 1]
            if prev_mod.name.startswith("_AMENDMENT_BEFORE_"):
                return prev_mod

        mod = obj.modifiers[mod_idx]
        extra_mod = obj.modifiers.new("_AMENDMENT_BEFORE_" + mod.name, 'UV_WARP')
        override = { 'active_object': obj }
        bpy.ops.object.modifier_move_to_index(override, modifier=extra_mod.name, index=mod_idx)
        return extra_mod

    def insert_path_index_mod_after(self, obj, mod_idx):
        """Same as insert_path_index_mod_before, but after the selected modifier."""
        if mod_idx < len(obj.modifiers) - 1:
            next_mod = obj.modifiers[mod_idx + 1]
            if next_mod.name.startswith("_AMENDMENT_AFTER_"):
                return next_mod

        mod = obj.modifiers[mod_idx]
        extra_mod = obj.modifiers.new("_AMENDMENT_AFTER_" + mod.name, 'UV_WARP')
        override = { 'active_object': obj }
        bpy.ops.object.modifier_move_to_index(override, modifier=extra_mod.name, index=mod_idx + 1)
        return extra_mod

    def init_leaf_parameters_rec(self, context, node):
        """Call light pack UV unwrapping for each leaf node, if you want to
        use UVs for material add a secondary UV layer, the active one will
        be affected by this operation."""
        mesh_inputs = self.get_mesh_inputs(node)

        if not mesh_inputs:
            mesh = bpy.data.meshes[node.objname]
            self.init_leaf_parameters(context, mesh)

        # recursive calls
        for input in mesh_inputs:
            for nlinks in input.links:
                self.init_leaf_parameters_rec(context, nlinks.from_node)

    def init_leaf_parameters(self, context, mesh):
        view_layer = context.view_layer
        for other in bpy.data.objects:
            other.select_set(False)
        obj = bpy.data.objects.new("temporary object", mesh)
        view_layer.active_layer_collection.collection.objects.link(obj)
        obj.select_set(True)
        view_layer.objects.active = obj
        
        #bpy.ops.object.mode_set(mode='EDIT')
        #bpy.ops.uv.lightmap_pack('EXEC_DEFAULT', PREF_CONTEXT='ALL_FACES')
        #bpy.ops.object.mode_set(mode='OBJECT')
        try:
            bpy.ops.uv.lightmap_pack()
        except RuntimeError as e:
            print(f"Warning: {e}")
        bpy.ops.object.delete()

# -------------------------------------------------------------------

classes = (
    DagAmendment,
)
register, unregister = bpy.utils.register_classes_factory(classes)
