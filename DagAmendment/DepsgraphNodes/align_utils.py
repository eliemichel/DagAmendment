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

from collections import OrderedDict
from itertools import repeat

# -------------------------------------------------------------------

def get_node_height(node):
    """Work around the fact that blender does not update
    dimensions.y for nodes that have just been created"""
    if node.hide:
        return 30
    a = 60 + 30
    b = 21
    return a + b * (len(node.inputs) + len(node.outputs))

# -------------------------------------------------------------------

def nodes_arrange(nodelist, level, margin_x, margin_y, x_last):
    """Largely imported from NodeArrange add-on by JuhaW (GPL)
    https://github.com/JuhaW/NodeArrange"""
    parents = []
    for node in nodelist:
        parents.append(node.parent)
        node.parent = None

    widthmax = max([x.width for x in nodelist])
    xpos = x_last - (widthmax + margin_x) if level != 0 else 0
    
    y = 0

    prev_node = None
    margin = margin_y
    for node in nodelist:
        margin = margin_y
        # ad-hoc for Depsgraph Nodes
        if prev_node is None:
            margin = 0
        else:
            cur_type = node.name.split('@')[0]
            prev_type = prev_node.name.split('@')[0]
            if (
                (prev_type == 'PROP:TX' and cur_type == 'PROP:TY') or
                (prev_type == 'PROP:TY' and cur_type == 'PROP:TZ') or
                (prev_type == 'PROP:RX' and cur_type == 'PROP:RY') or
                (prev_type == 'PROP:RY' and cur_type == 'PROP:RZ') or
                (prev_type == 'PROP:SX' and cur_type == 'PROP:SY') or
                (prev_type == 'PROP:SY' and cur_type == 'PROP:SZ')
            ):
                margin = 0
        
        if node.hide:
            hidey = (get_node_height(node) / 2) - 8
            y = y - hidey
        else:
            hidey = 0

        y = y - margin
        node.location.y = y
        y = y - get_node_height(node) + hidey

        node.location.x = xpos
        prev_node = node

    y = y + margin

    for i, node in enumerate(nodelist):
        node.parent =  parents[i]

    return xpos

# -------------------------------------------------------------------

def find_root_nodes(tree):
    return [
        node
        for node in tree.nodes
        if all([not output.is_linked for output in node.outputs])
    ]

# -------------------------------------------------------------------

def auto_align_nodes(tree, margin_x=100, margin_y=20):
    root_nodes = find_root_nodes(tree)
    if not root_nodes:
        return
    a = []
    a.append(root_nodes)

    visited = set()
    for node in root_nodes:
        visited.add(node.name)

    level = 0

    while a[level]:
        a.append([])

        for node in a[level]:
            for input in node.inputs:
                for nlinks in input.links:
                    prev_node = nlinks.from_node
                    if prev_node.name not in visited or True:
                        visited.add(prev_node.name)
                        a[level + 1].append(prev_node)

        level += 1
        if level > 1000:
            print("Error, maximum number of levels reached")
            break

    del a[level]
    level -= 1

    #remove duplicate nodes at the same level, first wins
    for x, nodes in enumerate(a):
        a[x] = list(OrderedDict(zip(a[x], repeat(None))))

    #remove duplicate nodes in all levels, last wins
    top = level
    for row1 in range(top, 1, -1):
        for col1 in a[row1]:
            for row2 in range(row1-1, 0, -1):
                for col2 in a[row2]:
                    if col1 == col2:
                        a[row2].remove(col2)
                        break

    ########################################

    level_count = level + 1
    x_last = 0
    for level, nodes in enumerate(a):
        x_last = nodes_arrange(nodes, level, margin_x, margin_y, x_last)
