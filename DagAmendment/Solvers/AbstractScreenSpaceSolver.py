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

from .AbstractSolver import AbstractSolver
from ..Projector import Projector

class AbstractScreenSpaceSolver(AbstractSolver):
    """
    A simpler interface for Solver that uses an already projected jacobian
    and mouse move, for purely screen space solvers.
    """

    def solve2d(self, PT, J, parameters):
        raise NotImplemented
    
    def solve(self, origin_worldspace, stroke, viewport_state, origin_jacobian, parameters):
        unstacked = origin_jacobian.reshape(-1, 3, len(parameters))

        resolution = np.array((viewport_state.width, viewport_state.height))
        current_mouse = np.array(stroke.trajectory[-1]) / resolution
        start_mouse = viewport_state.projector.eval(origin_worldspace)

        PT = np.array(current_mouse - start_mouse)
        PT = PT.reshape(1,-1).repeat(len(unstacked), axis=0).reshape(-1)

        J_proj = viewport_state.projector.jacobian(origin_worldspace)
        J = np.concatenate(J_proj @ unstacked)

        return self.solve2d(PT, J, parameters)
