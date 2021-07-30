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
from bpy.types import (
    Scene, Object, PropertyGroup, Collection, ViewLayer
)
from bpy.props import (
    FloatProperty, IntProperty, BoolProperty,
    PointerProperty, CollectionProperty, EnumProperty,
    FloatVectorProperty,
)

from . import profiling_properties
from .SamplePoints import SamplePoints
from .SolvingVisualization import SolvingVisualization
from .CachedProperty import CachedProperty

from . import registries_properties
from . import hyperparameter_properties

# -------------------------------------------------------------------

class SamplePointsProperty(CachedProperty):
    cache_key: IntProperty(name="Cache Key", options={'HIDDEN', 'SKIP_SAVE'}, default=-1)

    def create_instance(self, id_data):
        return SamplePoints(bpy.context)

# -------------------------------------------------------------------

class SolvingVisualizationProperty(CachedProperty):
    cache_key: IntProperty(name="Cache Key", options={'HIDDEN', 'SKIP_SAVE'}, default=-1)

    def create_instance(self, id_data):
        return SolvingVisualization(bpy.context)

# -------------------------------------------------------------------

class SamplePointsPreviewProperties(PropertyGroup):
    scale: FloatProperty(
        name="Preview Scale",
        description="Factor applied to the vectors for visualization",
        default=1,
    )

    brush_color: FloatVectorProperty(
        subtype='COLOR',
        size=4,
        name="Brush Color",
        description="Color used to draw the brush",
        default=(0.1, 0.1, 0.1, 0.5),
        min=0.0, max=1.0,
    )

    show_outer_radius: BoolProperty(
        name="Show outer radius",
        description="Draw a second brush circle to visualize the extent in which negative samples are drawn",
        default=True,
    )

# -------------------------------------------------------------------

class DagAmendmentScenePropertiesCallbacks:
    def view_layers_items(self, context):
        return [
            (vl.name, vl.name, "")
            for vl in context.scene.view_layers
        ]

class DagAmendmentSceneProperties(PropertyGroup):
    cb = DagAmendmentScenePropertiesCallbacks

    sample_points: PointerProperty(type=SamplePointsProperty)

    sample_points_preview: PointerProperty(type=SamplePointsPreviewProperties)

    view_layer_name: EnumProperty(
        name = "View Layer",
        description = "View Layer where only the parametric shape is visible, to avoid interacting with other objects.",
        items = cb.view_layers_items,
    )

    solvers: PointerProperty(type=registries_properties.SolverPropertiesPool)

    jfilters: PointerProperty(type=registries_properties.JFilterPropertiesPool)

    show_slider_overlay: BoolProperty(
        name = "Show Hyper-Parameter Sliders",
        description = "Show an overlay on the 3D view with sliders representing the hyper-parameters",
        default = True,
    )

    solving_visualization: PointerProperty(type=SolvingVisualizationProperty)

    @property
    def view_layer(self):
        scene = self.id_data
        return scene.view_layers[self.view_layer_name]

    def solver_properties(self, solver_name):
        if hasattr(self.solvers, solver_name):
            return getattr(self.solvers, solver_name)

    def jfilter_properties(self, solver_name):
        if hasattr(self.jfilters, solver_name):
            return getattr(self.jfilters, solver_name)

    def ensure_view_layer_depsgraph(self, context):
        """
        Blender does not initialize a view layer's depsgraph until it gets
        active so this automatically activate and deactivate right away the
        parametric shape's view layer if it has no depsgraph yet
        """
        scene = context.scene
        depsgraph = scene.diffparam.view_layer.depsgraph
        if depsgraph is None:
            current_view_layer = context.window.view_layer
            context.window.view_layer = scene.diffparam.view_layer
            depsgraph = context.evaluated_depsgraph_get()
            depsgraph.update()
            context.window.view_layer = current_view_layer

# -------------------------------------------------------------------

classes = (
    SamplePointsProperty,
    SamplePointsPreviewProperties,
    SolvingVisualizationProperty,
    *registries_properties.classes,
    *hyperparameter_properties.classes,
    DagAmendmentSceneProperties,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    profiling_properties.register()
    register_cls()
    Scene.diffparam_parameters = CollectionProperty(
        name="Parameters",
        description="Public parameters of the global parametric shape",
        type=hyperparameter_properties.HyperParameterProperty
    )
    Scene.diffparam_active_parameter = IntProperty(
        name="Active Hyper-Parameter",
        default=0
    )
    Scene.diffparam_controller_collection = PointerProperty(
        name="Controllers",
        type=Collection
    )
    Scene.diffparam = PointerProperty(type=DagAmendmentSceneProperties)

def unregister():
    for scene in bpy.data.scenes:
        scene.diffparam.sample_points.reset()  # clean up draw handlers

    unregister_cls()
    del Scene.diffparam_parameters
    del Scene.diffparam_active_parameter
    del Scene.diffparam_controller_collection
    del Scene.diffparam

    profiling_properties.unregister()
