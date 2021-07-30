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
from .Projector import Projector
from .Ray import Ray

# -------------------------------------------------------------------

class ViewportState:
    """State of the viewport at the beginning of a stroke, provided
    to the solver as context."""

    def __init__(self, projector, width, height):
        self.projector = projector
        self.width = width
        self.height = height

    def ray_from_screenpoint(self, point):
        point = np.array(point) / np.array((self.width, self.height))
        origin = self.projector.position
        direction = self.projector.unproject(point)
        return Ray(origin, direction)

    def to_json(self):
        return {
            'projector': self.projector.to_json(),
            'width': self.width,
            'height': self.height,
        }

    @classmethod
    def from_json(cls, data):
        proj = Projector.from_json(data['projector'])
        width = float(data['width'])
        height = float(data['height'])
        return ViewportState(projector, width, height)

# -------------------------------------------------------------------
