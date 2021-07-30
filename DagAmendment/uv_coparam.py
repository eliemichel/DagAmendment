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

"""
What is called "UV-coparam" here is the fact that we use as coparam the product
of UV space and material ID.
"""

import bpy

import numpy as np
from numpy.linalg import norm

from .profiling import Timer
from .utils import get_vertex_positions_as_np
from .numpy_utils import matvecmul
from .Accel import project as project_on_mesh

# -------------------------------------------------------------------

def get_uv_mesh(mesh):
    """
    Get a mesh whose spatial embedding has been replaced by
    (u, v, material_id) coordinates.
    @return the point positions, a triangle index list, and a mapping
    from corners of this uv mesh to the vertices of the original mesh.
    """
    timer = Timer()

    mesh.calc_loop_triangles()
    uv_layer = mesh.uv_layers.active

    tri_to_mat = np.empty(len(mesh.loop_triangles), 'i')
    mesh.loop_triangles.foreach_get('material_index', tri_to_mat.ravel())

    tri_to_loop = np.empty((len(mesh.loop_triangles), 3), 'i')
    mesh.loop_triangles.foreach_get('loops', tri_to_loop.ravel())
    
    loop_to_uv = np.empty((len(mesh.loops), 2), 'f')
    uv_layer.data.foreach_get('uv', loop_to_uv.ravel())

    loop_to_vert = np.empty(len(mesh.loops), 'i')
    mesh.loops.foreach_get('vertex_index', loop_to_vert.ravel())
    
    uv_loop_triangles = tri_to_loop
    uv_coords = np.concatenate((loop_to_uv, np.empty((len(loop_to_uv), 1), 'f')), axis=1)
    uv_coords[tri_to_loop,2] = tri_to_mat[:,np.newaxis]
    uv_loop_to_vert = loop_to_vert

    bpy.context.scene.profiling["build_uv_coords"].add_sample(timer)
    return uv_coords, uv_loop_triangles, uv_loop_to_vert

# -------------------------------------------------------------------

def coparam_to_position(uv_coparam_vec, obj, max_projection_error = 1e-7):
    """
    Given a coparam, return the current position of points within the
    given object.
    @return array of 3D positions with as many lines as in uv_coparam_vec
    """
    profiling = bpy.context.scene.profiling
    timer = Timer()
    
    # start init
    orig_me = obj.data
    M = np.array(obj.matrix_world)
    R, T = M[:3,:3], M[:3,3]

    orig_coords = get_vertex_positions_as_np(orig_me)

    uv_coords, uv_loop_triangles, uv_loop_to_vert = get_uv_mesh(orig_me)
    
    samples = np.array(uv_coparam_vec, 'f')

    projections, bcoords, proj_triangle_indices = project_on_mesh(uv_coords, uv_loop_triangles, samples)
    
    # Convert parameter to position (quick once vectorized)
    diff = projections - samples
    sq_err = norm(diff, ord=2, axis=1)
    sq_max = max_projection_error * max_projection_error

    orig_corners_idx = uv_loop_to_vert[uv_loop_triangles[proj_triangle_indices]]
    orig_corners_local = orig_coords[orig_corners_idx]
    orig_loc_local = matvecmul(orig_corners_local.transpose(0,2,1), bcoords)
    orig_loc = matvecmul(R, orig_loc_local) + T
    orig_loc[sq_err > sq_max] = np.nan

    profiling["coparam_to_position"].add_sample(timer)
    return orig_loc

# -------------------------------------------------------------------
