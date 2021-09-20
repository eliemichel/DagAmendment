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
from mathutils import Vector
from mathutils.interpolate import poly_3d_calc

import numpy as np
from numpy.linalg import norm

from .utils import visible_objects_and_duplis, unproject_circle
from .numpy_utils import random_in_unit_disc, sqnorm
from .profiling import Timer
from .uv_coparam import coparam_to_position

class SamplePoints:
    """
    Points on the surface of the geometry at which we'll measure
    the jacobian.
    Could also be called "Jacobian Buffer"
    """
    def __init__(self, context):
        # Struct of arrays: all these arrays are supposed to have the
        # same length or be all None.
        self.positions = None
        self.coparams = None

        # When ready, jacobians has shape (n, 3, k) where:
        #  n is the number of sample points (length of self.positions
        #    and self.coparams)
        #  k is the number of hyper-parameters
        # Mathematically, self.jacobians[i] is the jacobian of the function
        #     F_i: hyperparams -> point of coparam self.coparams[i]
        self.jacobians = None

        # Is overriden with the parameter given to sample_from_view
        self.max_projection_error = 1e-7

    def is_ready(self):
        """Tells whether some points have been sampled"""
        return self.positions is not None

    def is_jacobian_ready(self):
        """Tells whether some points have been sampled"""
        return self.jacobians is not None

    def compute_jacobians(self, parametric_shape, delta=1e-5):
        """
        Measure the jacobians at the sampled points.
        It is assumed that there are sample points available, i.e. that
        is_ready() returns True.
        This populates self.jacobians, making is_jacobian_ready() return True
        @param delta: factor multiplied by the range of an
               hyper-parameter to get the delta used for finite
               differences.
        """
        base_delta = delta
        timer = Timer()
        assert(self.is_ready())

        n = len(self.positions)
        k = len(parametric_shape.hyperparams)
        self.jacobians = np.zeros((n, 3, k), 'f')

        if len(self.positions) == 0:
            return

        self.original_positions = np.array(self.positions, 'f')  # copy for error display
        parametric_shape.update()

        self._eval_positions(self.positions, parametric_shape)

        new_positions = np.empty_like(self.positions)
        for k, hparam in enumerate(parametric_shape.hyperparams):
            delta = hparam.delta(fac=base_delta)
            value = hparam.eval()

            # Basic finite differences:
            # Add 'delta' to the current parameter, and reevaluate the scene
            hparam.update(add=delta)
            parametric_shape.update()

            self._eval_positions(new_positions, parametric_shape)
            self.jacobians[:,:,k] = (new_positions - self.positions) / delta

            if norm(self.jacobians[:,:,k]) == 0:
                print(f"WARNING null axis {k} (delta={delta})")

            # Restore the original value of the parameter
            hparam.update(set=value)

        bpy.context.scene.profiling["SamplePoints:compute_jacobians"].add_sample(timer)

    def _eval_positions(self, output_array, parametric_shape):
        """Internal step of compute_jacobians, evaluate the current positions
        of points described by self.coparams and save them in output_array,
        that must have shape (point count, 3)"""
        timer = Timer()

        # All points belonging to the same object are evaluated at the same time
        # (thanks to coparam_to_position() being vectorized)
        for obj, indices in zip(self.objects, self.per_object_ranges):
            if not indices:
                continue
            # This part should be in ParametricShape, but we don't want to move
            # the per-primitive sort mechanism to ParametricShape so it is easier
            # to keep this here
            eval_obj = obj.evaluated_get(parametric_shape._depsgraph)
            output_array[indices] = coparam_to_position(self.coparams[indices], eval_obj, max_projection_error=self.max_projection_error)

        bpy.context.scene.profiling["SamplePoints:eval_positions"].add_sample(timer)

    def eval_positions(self, parametric_shape):
        """Evaluate the current world space position of all sample points"""
        positions = np.zeros_like(self.positions)
        self._eval_positions(positions[:], parametric_shape)
        return positions

    def sample_from_view(self, parametric_shape, viewport_state, mouse_x, mouse_y, radius, sample_count=32, max_projection_error=1e-7, discard_by_world_distance=True):
        """
        Resample positions by unprojecting screen space samples around
        the mouse cursor. Only keep points in a given sphere around the
        main point (the one unprojected from the very mouse position).

        This fills self.positions and self.coparams hence
        making is_ready() return True
        """
        timer = Timer()
        
        self.max_projection_error = max_projection_error

        parametric_shape.update()
        self._init_object_lut(parametric_shape)

        all_samples = []
        main_position = None  # closest successful ray cast to the mouse cursor
        min_d2 = None
        sample_count_per_object = [0 for _ in self.object_lut]
        for i in range(sample_count):
            ss_offset = random_in_unit_disc() * radius if i > 0 else np.zeros(2)
            ss_sample = np.array((mouse_x, mouse_y)) + ss_offset
            u, v = ss_sample[0] / viewport_state.width, ss_sample[1] / viewport_state.height
            ray = viewport_state.ray_from_screenpoint(ss_sample)
            hit = parametric_shape.cast_ray(ray, make_coparam=self.coparam_from_hit)
            if hit is None:
                continue
            pos, (coparam, object_id) = hit
            all_samples.append((pos, coparam, object_id, ss_offset))
            sample_count_per_object[object_id] += 1

            if discard_by_world_distance:
                d2 = sqnorm(ss_offset)
                if main_position is None or d2 < min_d2:
                    main_position = pos
                    min_d2 = d2

        if not all_samples:
            return

        # We sort by object ID so that samples that belong to the same object are
        # at consecutive positions in the array. This speeds up slicing when there
        # is a need for treating each object separately (e.g. in compute_jacobians)
        all_samples.sort(key=lambda x: x[2])

        if discard_by_world_distance:
            ray_origin = viewport_state.projector.position
            lens = viewport_state.projector.lens
            depth_gt = norm(ray_origin - main_position)
            ws_radius = unproject_circle(radius, depth_gt, lens, viewport_state.height, 36.0)
            ws_radius *= 1.1
            ws_radius2 = ws_radius * ws_radius

            filtered_samples = []
            sample_count_per_object = [0 for _ in self.object_lut]
            for s in all_samples:
                pos, _, object_id, _ = s
                if sqnorm(pos - main_position) < ws_radius2:
                    filtered_samples.append(s)
                    sample_count_per_object[object_id] += 1
            all_samples = filtered_samples

        # Also remember slicing indices, so that all_samples[samples_per_object_ranges[i]]
        # is all the samples from object #i.
        self.per_object_ranges = [None for _ in self.object_lut]
        prefix_sum = 0
        for object_id, count in enumerate(sample_count_per_object):
            self.per_object_ranges[object_id] = range(prefix_sum, prefix_sum + count)
            prefix_sum += count

        self.positions = np.array([pos for pos, _, _, _ in all_samples], 'f')
        self.coparams = np.array([coparam for _, coparam, _, _ in all_samples], 'f')
        self.ss_offsets = np.array([offset for _, _, _, offset in all_samples], 'f')
        self.jacobians = None

        bpy.context.scene.profiling["SamplePoints:sample_from_view"].add_sample(timer)

    def coparam_from_hit(self, location, normal, poly_index, object, matrix):
        """
        Callback provided to cast_ray, that returns the coparam at hit point
        It gets troubled by this issue in Blender's ray_cast:
            https://developer.blender.org/T72113#1077887
        """
        poly = object.data.polygons[poly_index]
        material_index = poly.material_index
        corners = [matrix @ object.data.vertices[vid].co for vid in poly.vertices]
        bcoords = poly_3d_calc(corners, location)

        uv_layer = object.data.uv_layers.active.data
        corners_uv = [uv_layer[l].uv for l in poly.loop_indices]

        uv = (np.array(corners_uv) * np.array(bcoords)[:,np.newaxis]).sum(axis=0)

        check = sum([b * c for c, b in zip(corners, bcoords)], Vector((0,0,0)))

        if (location - check).magnitude > 0.01:
            print(f"High error in coparam estimation, hit object {object.name} at poly {poly} (#{poly_index}), material_index = {poly.material_index}")
        
        object_id = self.object_lut[object.name]
        #primitive_id = material_index * len(self.object_lut) + object_id
        primitive_id = material_index

        coparam = (*uv, primitive_id)

        return coparam, object_id

    def _init_object_lut(self, parametric_shape):
        """
        Build a mapping (object name -> unique integer ID)
        Call this any time the list of objects changes. In practice, to ensure
        that lut has been built it is called at each sampling, it has a low
        overhead anyways.
        """
        self.object_lut = {}
        self.objects = [] # reciprocal of object_lut, i.e. i == object_lut[objects[i].name]
        next_id = 0
        parametric_shape.update()
        for obj, mat in visible_objects_and_duplis(parametric_shape._depsgraph):
            if obj.name not in self.object_lut:
                self.object_lut[obj.name] = next_id
                self.objects.append(obj)
                next_id += 1

    def get_main_point(self):
        """
        Return the first non-nan position or None, and screen space
        offset to the mouse cursor.
        TODO: test by proximity to the mouse cursor
        """
        for i, pos in enumerate(self.positions):
            if not np.isnan(pos.sum()):
                return pos, self.ss_offsets[i]
        return None, None
