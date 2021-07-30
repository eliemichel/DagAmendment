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
from bpy.app.handlers import depsgraph_update_post, load_post, persistent

# -------------------------------------------------------------------

@persistent
def diffparam_ensure_parameter_boundaries(scene):
    """
    Try to put as little as possible here as this is called really often
    FIXME: There is an issue if parameters are directly interdependent
    because Blender ensures that this callback isn't called recursively
    """
    for param in scene.diffparam_parameters:
        v = param.eval()
        if v < param.minimum:
            param.update(set=param.minimum)
        if v > param.maximum:
            param.update(set=param.maximum)

@persistent
def diffparam_on_load(scene):
    if scene is not None:
        for obj in scene.objects:
            obj.jbuffer.reset()
        scene.jbuffer.reset()

# -------------------------------------------------------------------

def remove_handler(handlers_list, cb):
    """Remove any handler with the same name from a given handlers list"""
    to_remove = [h for h in handlers_list if h.__name__ == cb.__name__]
    for h in to_remove:
        handlers_list.remove(h)

def register():
    unregister()
    depsgraph_update_post.append(diffparam_ensure_parameter_boundaries)
    load_post.append(diffparam_on_load)

def unregister():
    remove_handler(depsgraph_update_post, diffparam_ensure_parameter_boundaries)
    remove_handler(load_post, diffparam_on_load)

# -------------------------------------------------------------------
