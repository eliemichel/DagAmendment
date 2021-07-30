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

from .profiling import Timer

class ParametricShape:
    """Wraps the Blender scene to provide an interface whose names
    match better the terms of the paper and that may be used to
    more easily port this to other software.

    Use ParametricShape.from_scene(scene) to get the parametric shape
    of a given scene."""

    __init_guard = object()  # to prevent one from using __init__

    @classmethod
    def from_scene(cls, scene):
        """Get the parametric shape from the current Blender scene"""
        import bpy
        scene.diffparam.ensure_view_layer_depsgraph(bpy.context)
        view_layer = scene.diffparam.view_layer
        depsgraph = view_layer.depsgraph
        
        shape = ParametricShape(ParametricShape.__init_guard)
        shape.hyperparams = scene.diffparam_parameters
        shape._scene = scene
        shape._depsgraph = depsgraph
        shape._view_layer = view_layer
        return shape

    def __init__(self, init_guard):
        if init_guard != ParametricShape.__init_guard:
            raise Exception("Don't create ParametricShape instances manually, " +
                            "use ParametricShape.from_scene() instead")
        self.hyperparams = None
        self._scene = None
        self._depsgraph = None
        self._view_layer = None

    def set_hyperparams(self, values):
        assert(len(values) == len(self.hyperparams))
        for hparam, val in zip(self.hyperparams, values):
            hparam.update(set=val)

    def update(self):
        """
        Update the currently evaluated static geometry from the hyper parameters
        """
        timer = Timer()
        self._depsgraph.update()
        self._scene.profiling["ParametricShape:update"].add_sample(timer)

    def cast_ray(self, ray, make_coparam=None):
        """
        Cast a ray onto the currently evaluated geometry (call update()
        to reevaluate)
        @param ray: Ray to intersect with the shape
        @param make_coparam: Optional callback returning a coparam from a hit point
        @return (hit position, hit coparam)
        """
        self._view_layer.update()
        assert(self._scene == self._view_layer.id_data)
        assert(self._depsgraph == self._view_layer.depsgraph)

        hit = self._scene.ray_cast(self._depsgraph, ray.origin, ray.direction)
        success, location, normal, poly_index, obj, matrix = hit

        if not success:
            return None

        if make_coparam is not None:
            coparam = make_coparam(location, normal, poly_index, obj.evaluated_get(self._depsgraph), matrix)
        else:
            coparam = None

        return location, coparam

