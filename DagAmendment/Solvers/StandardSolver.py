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

from ..props import BoolProperty, FloatProperty

import numpy as np
from numpy.linalg import svd, norm, inv

from .AbstractScreenSpaceSolver import AbstractScreenSpaceSolver
from ..numpy_utils import svd_inverse

# -------------------------------------------------------------------

class StandardSolver(AbstractScreenSpaceSolver):
    diffparam_label = "Standard"
    diffparam_default = True

    use_active_sets: BoolProperty(
        name = "Use Active Sets",
        description = "Be aware of hyper-parameter boundaries during solving",
        default = True,
    )

    use_previous_solution: BoolProperty(
        name = "Use Previous Solution",
        description = "Initialize the solver using its previous output",
        default = True,
    )

    max_change_per_frame: FloatProperty(
        name = "Maximum Change per Frame",
        description = "Relative maximum amplitude of the change of an hyper-parameter between two frames (if using previous solution)",
        default = 0.1,
    )

    def reset(self):
        super().reset()
        self.init = False

    def solve2d(self, PT, J, parameters):
        if not self.use_active_sets:
            Jinv, _ = svd_inverse(J.T)
            update = Jinv @ PT
            return update

        if not self.init:
            values = np.array([p.eval() for p in parameters])
            self.min_update = np.array([p.minimum for p in parameters]) - values
            self.max_update = np.array([p.maximum for p in parameters]) - values
            self.previous_update = np.zeros(len(parameters))
            self.init = True

        # Contains ones, then some zeros to freeze hyper-parameters once they
        # reached a boundary.
        active_set = np.array([1.0 for p in parameters])

        if self.use_previous_solution:
            update = self.previous_update
        else:
            update = np.zeros(len(parameters))

        # most probably repeating 5 times is enough, but we should repeat
        # until 'update' reaches a fixed point.
        for i in range(5):
            # Solve only for unfreezed hyper-parameters
            Jinv, _ = svd_inverse((J @ np.diag(active_set)).T)
            nth_update = Jinv @ (PT - J @ update)

            if self.use_previous_solution:
                limit = self.max_change_per_frame * (self.max_update - self.min_update)
                clamped = abs(nth_update) > limit
                if np.any(clamped):
                    pass
                nth_update = np.minimum(np.maximum(-limit, nth_update), limit)

            update += nth_update

            min_clamped = update < self.min_update
            max_clamped = update > self.max_update
            clamped = np.logical_or(min_clamped, max_clamped)
            active_set *= np.invert(clamped)

            update = np.minimum(np.maximum(self.min_update, update), self.max_update)

        self.previous_update = update
        return update

# -------------------------------------------------------------------
