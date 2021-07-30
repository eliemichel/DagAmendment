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
from bpy.types import Operator
from bpy.props import (
    PointerProperty, IntProperty, EnumProperty, BoolProperty,
    FloatProperty, FloatVectorProperty,
)
from mathutils import Vector

import numpy as np
from random import randint
import json

from .utils import get_operator_properties
from . import profiling
from .jfilter_registry import jfilter_registry, instantiate_jfilter
from .solver_registry import solver_registry, instantiate_solver
from .Projector import Projector
from .Brush import Brush
from .Stroke import Stroke
from .ViewportState import ViewportState
from .ParametricShape import ParametricShape
from .profiling import Timer

# -------------------------------------------------------------------

def jfilter_items(self, context):
    items = [
        (JFilter.diffparam_default, name, JFilter.diffparam_label, JFilter.__doc__ if JFilter.__doc__ is not None else "")
        for name, JFilter in jfilter_registry.items()
    ]
    items.sort(key=lambda x: -x[0])
    return [ x[1:] for x in items ]

def solver_items(self, context):
    items = [
        (Solver.diffparam_default, name, Solver.diffparam_label, Solver.__doc__ if Solver.__doc__ is not None else "")
        for name, Solver in solver_registry.items()
    ]
    items.sort(key=lambda x: -x[0])
    return [ x[1:] for x in items ]

class SmartGrab(Operator):
    bl_idname = "diffparam.smart_grab"
    bl_label = "Smart Grab"
    bl_options = {'REGISTER', 'UNDO'}

    solver: EnumProperty(
        name="Solver",
        description="Solver: Strategy to infer the parameter change from the user's stroke",
        items=solver_items,
    )

    jfilter: EnumProperty(
        name="JFilter",
        description="JFilter: Policy used to reduce the jacobian buffer into a single jacobian",
        items=jfilter_items,
    )

    brush_radius: FloatProperty(
        name="Brush Radius",
        description="Radius of the area in which the screenspace jbuffer is averaged",
        default=20,
    )

    # NB: Maybe this could be auto-tuned depending on 1. brush_radius and 2. profiling measures
    sample_count: IntProperty(
        name="Sample Count",
        description="Number of points at which the jacobian is evaluated. More is more precise by slower.",
        default=32,
    )

    jacobian_update_period: IntProperty(
        name="Jacobian Update Period",
        description="Update jacobian every n frames, or never if set to -1. Recomputing more often provides a smoother interaction but is more resource intensive.",
        min=-1,
        default=-1,
    )

    max_projection_error_pow: FloatProperty(
        name="Max Projection Error",
        description="Log10 of the distance in UV space beyond which a point is considered as not found during jacobian estimation",
        default=-7,
    )

    relative_delta_pow: FloatProperty(
        name="Delta",
        description="Log10 of the relative delta added to hyperparameter to measure the jacobian (finite differences)",
        default=-5,
    )

    discard_by_world_distance: BoolProperty(
        name="Discard by World Distance",
        description="After sampling point, removes the points that are outside of a sphere corresponding to the unprojection of the brush circle.",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        # Enable this operator only if we are in a 3D viewport.
        return context.area.type == 'VIEW_3D' and len(context.scene.diffparam_parameters) > 0

    def invoke(self, context, event):
        """
        Main entry point, called when the SmartGrab tool is enabled and the user
        presses left mouse button
        """
        timer = Timer()
        
        self.init_from_context(context, event)

        if not self.init_jbuffer():
            return {'FINISHED'}

        self.init_jacobian()

        context.scene.profiling["SmartGrab:init"].add_sample(timer.ellapsed())

        # modal() is then called at each input event, and on its turn calls
        # on_mouse_move(), on_confirm() and on_cancel().
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def on_mouse_move(self, x, y):
        timer = profiling.Timer()

        self.stroke.append(
            x + self.mouse_offset[0],
            y + self.mouse_offset[1],
        )

        # \Delta\pi in the paper
        # (more generally "valuation" = \pi = value of the hyper-parameters)
        delta_valuation = self.solve()
        
        if delta_valuation is not None:
            # Signal the current solving to the overlay
            self.solving_visualization.solving_lines = [
                (self.origin, self.origin + float(u) * self.jacobian[:3,i])
                for i, u in enumerate(delta_valuation) if u != 0
            ]
            self.parametric_shape.set_hyperparams(self.base_valuation + delta_valuation)
            self.parametric_shape.update()

        # May recompute the jacobian from time to time, if jacobian_update_period is not null
        self.frame_counter += 1
        if self.jacobian_update_period > 0 and self.frame_counter >= self.jacobian_update_period:
            self.frame_counter = 0
            self.update_jacobian()

        bpy.context.scene.profiling["SmartGrab:on_mouse_move"].add_sample(timer.ellapsed())

        return {'RUNNING_MODAL'}

    def on_confirm(self, context):
        return {'FINISHED'}

    def on_cancel(self, context):
        # Reset hyper-parameters
        self.parametric_shape.set_hyperparams(self.original_valuation)
        self.parametric_shape.update()
        return {'CANCELLED'}

    def init_from_context(self, context, event):
        region = context.region
        scene = context.scene

        # Blender entities like viewport projection and parametric shapes and
        # wrapped into our abstraction, so that our filter/solver code can
        # be reused more easily.
        proj = Projector(context)
        self.viewport_state = ViewportState(proj, region.width, region.height)
        self.parametric_shape = ParametricShape.from_scene(scene)

        # The stroke is a radius plus a sequence of mouse position that will
        # get filled throughout the interaction and provided to the solver.
        self.stroke = Stroke(Brush(self.brush_radius))

        # The jbuffer is the set of sample points and their associated jacobians.
        # See SamplePoint.py for more details.
        # We could instanciate it here by just using
        #   self.jbuffer = SamplePoint(context)
        # but it is stored in the scene's properties so that overlay can access
        # it for drawing vizualisation lines.
        self.jbuffer = scene.diffparam.sample_points.get()

        # Various jacobian filters and solvers can be proposed to the user
        # (by copying files in JFilters/ and Solvers/) and here we instantiate
        # the one that has been selected
        self.jfilter_instance = instantiate_jfilter(context, self.jfilter)
        self.solver_instance = instantiate_solver(context, self.solver)
        self.solver_instance.reset()

        self.init_mouse_x = event.mouse_region_x
        self.init_mouse_y = event.mouse_region_y

        self.frame_counter = 0
        self.random_seed = randint(0, 1<<30)

        # Temporary object used to transmit info from this operator to the overlay
        self.solving_visualization = context.scene.diffparam.solving_visualization.get()

    def init_jbuffer(self):
        """
        Initialize the jacobian buffer, including sampling subshapes
        within the extent of the brush (or a bit more when using
        a negative interaction jfilter), and computing the jacobians
        of these subshapes
        """
        np.random.seed(self.random_seed)

        self.jbuffer.sample_from_view(
            self.parametric_shape,
            self.viewport_state,
            self.init_mouse_x,
            self.init_mouse_y,
            self.jfilter_instance.transform_brush_radius(self.brush_radius),
            sample_count=self.sample_count,
            max_projection_error=pow(10, self.max_projection_error_pow),
            discard_by_world_distance=self.discard_by_world_distance,
        )

        if not self.jbuffer.is_ready():
            return False

        # mouse_offset is the screen space offset between the mouse cursor and the closest
        # sample point from the brush. It plays a particular role because other sample points
        # that are too far from it 
        self.origin, self.mouse_offset = self.jbuffer.get_main_point()
        if self.origin is None:
            return False

        return True

    def init_jacobian(self):
        self.update_jacobian(update_origin=False)

        # Cache original hyper-parameter values, in case the user cancels
        self.original_valuation = self.base_valuation[:]

        self.stroke.append(
            self.init_mouse_x + self.mouse_offset[0],
            self.init_mouse_y + self.mouse_offset[1],
        )

    def update_jacobian(self, update_origin=True):
        """
        Cache the value of the jacobian where the stroke starts
        Updates self.jacobian and self.base_valuation
        """

        # 1. Measure the jacobian at each sample point
        self.jbuffer.compute_jacobians(
            self.parametric_shape,
            delta=pow(10, self.relative_delta_pow)
        )

        # 2. Reduce all individual jacobians into a single one (jacobian filtering)
        timer = Timer()
        self.jacobian = self.jfilter_instance.reduce_jacobian(
            self.brush_radius,
            self.jbuffer
        )
        bpy.context.scene.profiling["SmartGrab:reduce_jacobian"].add_sample(timer.ellapsed())

        # Base valuation is the value of the hyper-parameters at the last jacobian update
        self.base_valuation = [
            param.eval()
            for param in self.parametric_shape.hyperparams
        ]

        if update_origin:
            raise NotImplemented

    def solve(self):
        timer = profiling.Timer()

        delta_valuation = self.solver_instance.solve(self.origin,
                                                     self.stroke,
                                                     self.viewport_state,
                                                     self.jacobian,
                                                     self.parametric_shape.hyperparams)

        if delta_valuation is not None:
            delta_valuation = np.nan_to_num(delta_valuation)
        
        bpy.context.scene.profiling["SmartGrab:solve"].add_sample(timer.ellapsed())
        return delta_valuation

    def modal(self, context, event):
        """
        Called at each event, dispatches to the on_something() methods
        """
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            x = event.mouse_region_x
            y = event.mouse_region_y
            return self.on_mouse_move(x, y)

        elif event.type in {'LEFTMOUSE'}:
            return self.on_confirm(context)

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return self.on_cancel(context)

        return {'RUNNING_MODAL'}

# -------------------------------------------------------------------

class ScaleSmartGrabBrush(Operator):
    """
    When the SmartGrab tool is enables, this is called when Ctrl+Click
    is used, to change the size of the brush.
    """
    bl_idname = "diffparam.scale_smart_grab_brush"
    bl_label = "Scale Smart Grab Brush"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        self.start_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        smartgrab_props = get_operator_properties(context, SmartGrab.bl_idname)
        self.start_radius = smartgrab_props.brush_radius
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        
        if event.type in {'MOUSEMOVE', 'LEFTMOUSE'}:
            self.update_radius(context, event)
            if event.type == 'LEFTMOUSE':
                return {'FINISHED'}
            else:
                return {'RUNNING_MODAL'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            smartgrab_props.brush_radius = self.start_radius
            return {'CANCELLED'}
        else:
            return {'RUNNING_MODAL'}

    def update_radius(self, context, event):
        smartgrab_props = get_operator_properties(context, SmartGrab.bl_idname)
        mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        delta_radius = (mouse - self.start_mouse).x
        smartgrab_props.brush_radius = max(self.start_radius + delta_radius, 1)
        context.area.tag_redraw()

# -------------------------------------------------------------------

classes = (
    SmartGrab,
    ScaleSmartGrabBrush,
)
register, unregister = bpy.utils.register_classes_factory(classes)
