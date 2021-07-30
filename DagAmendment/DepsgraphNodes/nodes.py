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
from bpy.types import NodeTree, Node, NodeSocket
from bpy.props import StringProperty, IntProperty

# -------------------------------------------------------------------

class DepsGraphNodeTree(NodeTree):
    """A node tree type for visualizing internal dependency graph"""
    bl_idname = 'DepsGraphNodeTree'
    bl_label = "Depsgraph Nodes"
    bl_icon = 'NODETREE'

# -------------------------------------------------------------------

class ValueDependencySocket(NodeSocket):
    """Indicate a dependency, used to solve the ordering in which evaluating the scene"""
    bl_label = "Value Dependency"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)

class MeshDependencySocket(NodeSocket):
    """Indicate a dependency, used to solve the ordering in which evaluating the scene"""
    bl_label = "Mesh Dependency"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.216, 0.4, 1.0, 0.5)

# -------------------------------------------------------------------

class DepsgraphTreeNode:
    entity_name: StringProperty(
        name="Entity Name",
    )

    path_count: IntProperty(
        name="Path Count",
        default=0,
    )

    path_multiplier: IntProperty(
        name="Path Multiplier",
        default=1,
    )

    subtype: StringProperty(
        name="Node Type",
    )

    objname: StringProperty(
        name="Parent Object",
    )

    variant: StringProperty(
        name="Variant",
        description = "e.g. Modifier name",
    )
    
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == DepsGraphNodeTree.bl_idname
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "entity_name", text="")
        layout.prop(self, "path_count")

def make_class(name, inputs, output_type = 'Value'):
    class SomeNode(Node, DepsgraphTreeNode):
        bl_idname = name
        bl_label = name
        
        def init(self, context):
            for i in inputs:
                sock = 'MeshDependencySocket' if i.startswith("mesh") else 'ValueDependencySocket'
                self.inputs.new(sock, i)
                
            if output_type is not None:
                self.outputs.new(output_type + 'DependencySocket', "")
        
        def draw_label(self):
            return f"{name}@{self.entity_name}"

        def ensure_driver_input(self):
            if "driver" not in self.inputs:
                self.inputs.new('ValueDependencySocket', "driver")
        
    return SomeNode

node_classes = list(map(lambda x: make_class(*x), [
    ("PARAM", []),
    ("PROP:TX", []),
    ("PROP:TY", []),
    ("PROP:TZ", []),
    ("PROP:RX", []),
    ("PROP:RY", []),
    ("PROP:RZ", []),
    ("PROP:SX", []),
    ("PROP:SY", []),
    ("PROP:SZ", []),
    ("PROP:T", ["X", "Y", "Z"]),
    ("PROP:R", ["X", "Y", "Z"]),
    ("PROP:S", ["X", "Y", "Z"]),
    ("PROP:MESH", [], 'Mesh'),
    ("PROP:OUT_MESH", ["mesh"], 'Mesh'),
    ("PROP:XFORM", ["xform"]),
    ("OP:XFORM", ["T", "R", "S", "parent"]),
    ("OP:XFORM_MESH", ["mesh", "xform"], 'Mesh'),
    ("OP:MODIFIER_UNARY", ["mesh"], 'Mesh'),
    ("OP:MODIFIER_DUARY", ["mesh1", "mesh2"], 'Mesh'),
    ("OTHER:VIEW_LAYER", [], None),
]))

class DriverNode(Node, DepsgraphTreeNode):
    bl_idname = 'OP:DRIVER'
    bl_label = 'OP:DRIVER'
    
    def init(self, context):
        self.outputs.new('ValueDependencySocket', "")
    
    def draw_label(self):
        return f"OP:DRIVER@{self.entity_name}"

    def set_variable_count(self, count):
        for i in range(len(self.inputs), count):
            self.inputs.new('ValueDependencySocket', f"var{i}")
        while len(self.inputs) > count:
            self.inputs.remove(self.inputs[-1])

# -------------------------------------------------------------------

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

class DepsgraphNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == DepsGraphNodeTree.bl_idname

node_categories = [
    DepsgraphNodeCategory('OPS', "Operations", items=[
        NodeItem(SomeNode.bl_idname)
        for SomeNode in node_classes
        if SomeNode.bl_idname.startswith("OP:")
    ]),
    DepsgraphNodeCategory('PROPS', "Properties", items=[
        NodeItem(SomeNode.bl_idname)
        for SomeNode in node_classes
        if SomeNode.bl_idname.startswith("PROP:")
    ]),
    DepsgraphNodeCategory('OTHER', "Other", items=[
        NodeItem(SomeNode.bl_idname)
        for SomeNode in node_classes
        if not SomeNode.bl_idname.startswith("OP:")
        and not SomeNode.bl_idname.startswith("PROP:")
    ]),
]

# -------------------------------------------------------------------

classes = (
    DepsGraphNodeTree,
    ValueDependencySocket,
    MeshDependencySocket,
    DriverNode,
    *node_classes,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    register_cls()
    try:
    	nodeitems_utils.unregister_node_categories('DEPSGRAPH_NODES')
    except:
    	pass
    nodeitems_utils.register_node_categories('DEPSGRAPH_NODES', node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories('DEPSGRAPH_NODES')
    unregister_cls()
