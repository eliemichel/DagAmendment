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

from . import backend
from .nodes import DepsGraphNodeTree
from .align_utils import auto_align_nodes

# -------------------------------------------------------------------

class UpdateDepsgraphNodes(Operator):
    """Recreates the 'DEPSGRAPH' node tree to sync it with the current scene"""
    bl_idname = "depsgraph_nodes.update"
    bl_label = "Update Depsgraph Nodes"

    def execute(self, context):
        graph = bpy.data.node_groups.get('DEPSGRAPH')
        if graph is None:
            graph = bpy.data.node_groups.new(name='DEPSGRAPH', type=DepsGraphNodeTree.bl_idname)
        backend.update_graph(graph, context)
        auto_align_nodes(graph)
        return {'FINISHED'}

# -------------------------------------------------------------------

classes = (
    UpdateDepsgraphNodes,
)
register, unregister = bpy.utils.register_classes_factory(classes)
