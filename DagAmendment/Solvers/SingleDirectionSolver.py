# This file is part of DagAmendment, the reference implementation of:
#
#   Michel, Élie and Boubekeur, Tamy (2021).
#   DAG Amendment for Inverse Control of Parametric Shapes
#   ACM Transactions on Graphics (Proc. SIGGRAPH 2021), 173:1-173:14.
#
# Copyright (c) 2020-2021 -- Télécom Paris (Élie Michel <elie.michel@telecom-paris.fr>)
# 
# The MIT license:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software is provided “as is”, without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and non-infringement. In no event shall the
# authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising
# from, out of or in connection with the software or the use or other dealings
# in the Software.

# no bpy here

import numpy as np
from numpy.linalg import norm

from ..props import FloatProperty, BoolProperty
from .AbstractSolver import AbstractSolver
from ..Projector import Projector
from ..numpy_utils import normalize

# -------------------------------------------------------------------

class SingleDirectionSolver(AbstractSolver):
    """A solver that is constrained to affect exactly one hyper-parameter only."""
    diffparam_label = "Single Direction"

    freeze_parameter_threshold: FloatProperty(
        name="Freeze Threshold",
        description="Distance in pixels beyond which the parameter that the grab action acts on can no longer change.",
        default=10,
    )

    weighted: BoolProperty(
        name="Weighted",
        description="Take per-hyperparameter normalizer into account",
        default=False,
    )

    def reset(self):
        self.last_param_index = None
        self.freezed_param_index = None
        self.mouse_start = None

    def solve(self, origin_worldspace, stroke, viewport_state, origin_jacobian, parameters):
        """
        Return a list of the update to apply to each parameter value
        or None to mean no update
        """
        if origin_jacobian.shape[0] != 3:
            raise Exception("Stacked Reducer is not compatible with Single Direction Solver")

        resolution = np.array((viewport_state.width, viewport_state.height))
        self.mouse_start = stroke.trajectory[0]
        current_mouse = stroke.trajectory[-1] / resolution
        selected, amplitude = self.select_best_parameter(origin_worldspace, current_mouse, viewport_state, origin_jacobian, parameters)
        if selected is None:
            return None

        # Save selected parameter
        self.last_param_index = selected
        self.maybe_freeze(stroke.trajectory)

        return [amplitude if i == selected else 0 for i in range(len(parameters))]

    def select_best_parameter(self, origin_worldspace, current_mouse, viewport_state, origin_jacobian, parameters):
        """Select the most appropriate direction among the d_i
        if the parameter is freezed (because the user moved by more than
        the threshold pixels) then this function simply returns the previously
        selected parameter
        Also return the amplitude of the parameter change"""
        current_mouse = np.array(current_mouse)

        start_mouse = viewport_state.projector.eval(origin_worldspace)
        move = current_mouse - start_mouse

        argmax = None
        amplitude = 0
        for i, param in enumerate(parameters):
            if self.freezed_param_index is not None and i != self.freezed_param_index:
                continue
            normalizer = param.normalizer if self.weighted else 1.0

            # new location that the clicked point would have if we would apply the
            # change to parameter #i
            offset_mouse = viewport_state.projector.eval(origin_worldspace + origin_jacobian.T[i] * normalizer)
            if offset_mouse is None:
                continue

            move_param = offset_mouse - start_mouse

            # Score of the move corresponding to the current parameter. The selected
            # parameter is the one with the highest score.
            # This is a mixture of the direction proximity and the magnitude of the 
            # move.
            cos_theta = abs(np.dot(normalize(move), normalize(move_param)))
            score = cos_theta + 0.5 * norm(move_param)

            if (argmax is None or score > max_score) and norm(move_param) > 0.01:
                max_score = score
                argmax = i
                amplitude = np.dot(move, move_param) / np.dot(move_param, move_param) * normalizer

        return argmax, amplitude

    def maybe_freeze(self, trajectory):
        """Switch to freezed mode (the tuned parameter can no longer change)
        if the mouse moved by more than the threshold"""
        if self.freezed_param_index is None:
            if norm(trajectory[0] - trajectory[-1]) > self.freeze_parameter_threshold:
                self.freezed_param_index = self.last_param_index

# -------------------------------------------------------------------
