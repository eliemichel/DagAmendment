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
from bpy_extras import view3d_utils
from mathutils import Vector

import numpy as np
from numpy.linalg import norm

from .profiling import Timer

# -------------------------------------------------------------------

def remove_object(obj):
    bpy.ops.object.delete({"selected_objects": [obj]})

# -------------------------------------------------------------------

def get_viewport_area(context):
    if context.area is not None and context.area.type == 'VIEW_3D':
        return context.area
    else:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                return area
    return None

def get_viewport(context):
    area = get_viewport_area(context)
    for region in area.regions:
            if region.type == 'WINDOW':
                break
    rv3d = area.spaces[0].region_3d
    return region, rv3d
             
def get_ray(context, u, v):
    region, rv3d = get_viewport(context)
    coord = u * region.width, v * region.height

    # get the ray from the viewport and mouse
    ray_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    return ray_origin, ray_direction

def project_point(context, point):
    region, rv3d = get_viewport(context)
    coord = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
    if coord is None:
        return None
    return Vector((coord[0] / region.width, coord[1] / region.height))

# -------------------------------------------------------------------

def visible_objects_and_duplis(depsgraph):
    """Loop over (object, matrix) pairs, returning one couple per instance"""
    for dup in depsgraph.object_instances:
        if dup.object.type != 'MESH':
            continue
        if dup.is_instance:  # Real dupli instance
            obj = dup.instance_object
            yield (obj, dup.matrix_world.copy())
        else:  # Usual object
            obj = dup.object
            yield (obj, obj.matrix_world.copy())

# -------------------------------------------------------------------

def trysetattr(obj, attr, value):
    if hasattr(obj, attr):
        setattr(obj, attr, value)

# -------------------------------------------------------------------

def get_vertex_positions_as_np(mesh):
    data = np.empty((len(mesh.vertices), 3), 'f')
    mesh.vertices.foreach_get('co', data.ravel())
    return data

# -------------------------------------------------------------------

def get_triangle_corners_as_np(mesh):
    mesh.calc_loop_triangles()
    data = np.empty((len(mesh.loop_triangles), 3), 'i')
    mesh.loop_triangles.foreach_get('vertices', data.ravel())
    return data

# -------------------------------------------------------------------

def get_operator_properties(context, op_idname):
    # https://blenderartists.org/t/share-operator-properties-in-workspacetool/1253663
    any_tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=True)
    return any_tool.operator_properties(op_idname)

# -------------------------------------------------------------------

def unproject_circle(radius, depth, focal_length, pixel_height, sensor_height):
    """
    Get the worldspace radius of a sphere that projects to
    the target circle (approximation, the true unprojection is
    an ellipsis, here we assume that the circle is at center)
    """
    c = (2 * radius / pixel_height) / (focal_length / sensor_height)
    return depth * c / np.sqrt(1 + c * c)
