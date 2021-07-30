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
from bpy.types import Panel

from . import operators as ops
from .nodes import DepsGraphNodeTree

# -------------------------------------------------------------------

class DepsgraphNodesPanel(Panel):
    bl_label = "Depsgraph Nodes"
    bl_idname = "NODES_PT_DepsgraphNodes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Depsgraph"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator(ops.UpdateDepsgraphNodes.bl_idname)

# -------------------------------------------------------------------

def node_header(self, context):
    if context.space_data.tree_type != DepsGraphNodeTree.bl_idname:
        return

    row = self.layout.row(align=True)
    row.operator(ops.UpdateDepsgraphNodes.bl_idname)

# -------------------------------------------------------------------

classes = (
    DepsgraphNodesPanel,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    register_cls()
    bpy.types.NODE_HT_header.append(node_header)

def unregister():
    bpy.types.NODE_HT_header.remove(node_header)
    unregister_cls()
