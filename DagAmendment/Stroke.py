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
from .Brush import Brush

# -------------------------------------------------------------------

class Stroke:
    def __init__(self, brush, trajectory = []):
        self.brush = brush
        self.trajectory = trajectory

    def append(self, *mouse_position):
        self.trajectory.append(np.array(mouse_position))


    def to_json(self):
        return {
            'brush': self.brush.to_json(),
            'trajectory': [x.tolist() for x in self.trajectory],
        }

    @classmethod
    def from_json(cls, data):
        brush = Brush.from_json(data['brush'])
        trajectory = [np.array(x) for x in data['trajectory']]
        return Stroke(brush, trajectory)
