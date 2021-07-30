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
from numpy.linalg import norm, inv

# TODO: rename perspective_matrix into projection_matrix

class Projector:
    """Holds the transformation from world space to manipulation space"""
    def __init__(self, context=None, perspective_matrix=None, view_matrix=None, lens=None):
        """Build a projector from the current 3D view
        (weird API for backward compat: context is used only if matrices are None)"""
        if perspective_matrix is None or view_matrix is None:
            from .utils import get_viewport, get_viewport_area
            region, rv3d = get_viewport(context)
            space_3d = get_viewport_area(context).spaces[0]
            M = np.array(((.5,0,0,.5),(0,.5,0,.5),(0,0,1,0),(0,0,0,1)))
            perspective_matrix = M @ np.array(rv3d.window_matrix)
            view_matrix = np.array(rv3d.view_matrix)
            lens = space_3d.lens

        self.perspective_matrix = perspective_matrix
        self.view_matrix = view_matrix
        self.P = self.perspective_matrix @ self.view_matrix
        self.w = 3
        self.inv_view_matrix = inv(view_matrix)
        self.lens = lens
        #assert(np.isclose(self.P, np.array(M @ rv3d.perspective_matrix)).all())

    def eval(self, X):
        """Output in [0,1]"""
        Y = self.P @ np.array((*X, 1))
        return Y[:2] / Y[self.w]

    def jacobian(self, X):
        Y = self.P @ np.array((*X, 1))
        projX = Y[:2] / Y[self.w]
        J = (self.P[:2] - np.outer(projX, self.P[self.w])) / Y[self.w]
        return J[:,:3]

    def unproject(self, uv):
        """Take a uv screen pos in range [0,1]² and return a world space
        direction"""
        u, v = uv
        proj = self.perspective_matrix

        screenspace = np.array((u, v, 0.0, 1.0))
        viewspace = inv(proj) @ screenspace
        viewspace[3] = 1
        worldspace = self.inv_view_matrix @ viewspace
        worldspace = worldspace[:3]

        direction = worldspace - self.position
        return direction / norm(direction)

    @property
    def position(self):
        return self.inv_view_matrix[:3,3]

    @property
    def yfov(self):
        return 2.0 * np.arctan(0.5 / self.perspective_matrix[1,1])# * 180.0 / np.pi

    @property
    def xfov(self):
        return 2.0 * np.arctan(0.5 / self.perspective_matrix[0,0])# * 180.0 / np.pi

    def to_json(self):
        return {
            'presp': self.perspective_matrix.tolist(),
            'view': self.view_matrix.tolist(),
            'lens': self.lens
        }

    @classmethod
    def from_json(cls, data):
        view = np.array(data['presp'])
        presp = np.array(data['view'])
        lens = np.array(data['lens'])
        return Projector(perspective_matrix=presp, view_matrix=view, lens=lens)
