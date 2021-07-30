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

class AbstractSolver:
    """A solver"""
    diffparam_label = "Abstract"
    diffparam_default = False
    
    def solve(self, origin_worldspace, stroke, viewport_state, origin_jacobian, parameters):
        """
        (mandatory)
        @return a list of the update to apply to each parameter value
        or None to mean no update.

        @param origin_worldspace: position of the point where stroke started (world space)
          (one can get the equivalent screen space position using
          start_mouse = stroke.trajectory[0]
        
        @param stroke: brush info and sequence of mouse positions (screen space, in range [0,1])

        @param viewport_state: info about the viewport like resolution and view angle
        
        @param origin_jacobian: jacobian of the origin point, which means jacobian[i] is
          the way parameter #i offsets the origin point, in world space
          (to get screenspace jacobian, use
          self.world_to_screenspace(origin_worldspace + origin_jacobian[i]) - start_mouse)
        
        @param parameters: list of parameters of the parametric shape, as instances of
          ShapeParameterProperty (see properties.py)
        """
        raise NotImplemented

    def reset(self):
        """
        (optional)
        Reset any cached value (typically for hystersis effects).
        Called when the user stroke starts, prior to any call to solve().
        """
        pass
