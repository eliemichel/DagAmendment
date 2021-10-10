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
import bgl
import gpu
from bpy.types import Gizmo, GizmoGroup

from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from .shaders import line_shader, point_shader

from mathutils import Vector
from math import cos, sin, pi
import numpy as np

from .palettes import palette0, from_html_color

# NB: It is not possible to subclass View3DOverlay so overlays are
# mimicked using a gizmo+gizmogroup with no interaction.

# -------------------------------------------------------------------

def add_line(buf, pt1, pt2):
    buf.append(pt1)
    buf.append(pt2)

def add_circle(buf, center, radius, normal, res=16):
    center = np.array(center)
    normal = np.array(normal)
    def normalize(v):
        l = np.linalg.norm(v)
        return v / l if l > 0 else v * 0.0
    vertical = np.array([0, 0, 1])
    if normalize(normal).dot(vertical) > 0.99:
        vertical = np.array([0, 1, 0])
    X = normalize(np.cross(normal, vertical))
    Y = normalize(np.cross(normal, X))
    th = np.linspace(0.0, 2.0 * pi, num=res)
    pts = center + radius * (np.outer(np.cos(th), X) + np.outer(np.sin(th), Y))
    pts = np.roll(pts.repeat(2, 0), -1, axis=0)
    buf.extend(pts)

class SmartGrabToolWidget(Gizmo):
    bl_idname = "VIEW3D_GT_smart_grab_tool"

    def draw(self, context):
        matrix = context.region_data.perspective_matrix

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glLineWidth(2)
        
        line_shader.bind()
        line_shader.uniform_float("viewProjectionMatrix", matrix)

        solving_visualization = context.scene.diffparam.solving_visualization.get(create=False)
        if solving_visualization is not None:
            grey_lines = []
            red_lines = []

            for line in solving_visualization.solving_lines:
                axis = line[1] - line[0]
                axis = (line[0], line[0] + axis * 100.0, line[0], line[0] - axis * 100.0)
                grey_lines.extend(axis)
                red_lines.extend(line)

            batch = batch_for_shader(line_shader, 'LINES', {"position": grey_lines})
            line_shader.uniform_float("color", (1.0, 1.0, 1.0, 0.2))
            batch.draw(line_shader)

            bgl.glDisable(bgl.GL_DEPTH_TEST)
            batch = batch_for_shader(line_shader, 'LINES', {"position": red_lines})
            line_shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
            batch.draw(line_shader)

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_DEPTH_TEST)

        self.draw_sample_points(context)

    def draw_sample_points(self, context, show_coparam=False):
        sample_points = context.scene.diffparam.sample_points.get(create=False)
        if sample_points is None or not sample_points.is_ready():
            return
        matrix = context.region_data.perspective_matrix
        n = len(sample_points.positions)
        preview_props = context.scene.diffparam.sample_points_preview

        # Sample points in 3D space
        shader = point_shader
        batch = batch_for_shader(shader, 'POINTS', {"position": sample_points.positions.astype('f')})
        shader.bind()
        shader.uniform_float("color", (1, 1, 0, 1))
        shader.uniform_float("viewProjectionMatrix", matrix)
        batch.draw(shader)
        
        # Sample points in Coparam space
        if show_coparam:
            shader = point_shader
            batch = batch_for_shader(shader, 'POINTS', {"position": sample_points.coparams.astype('f')})
            shader.bind()
            shader.uniform_float("color", (1, 0, 1, 1))
            shader.uniform_float("viewProjectionMatrix", matrix)
            batch.draw(shader)

        # Jacobian
        if sample_points.is_jacobian_ready():
            hyperparams = context.scene.diffparam_parameters
            for k in range(len(hyperparams)):
                lines = np.empty((2 * n, 3), 'f')
                lines[0::2,:] = sample_points.positions
                lines[1::2,:] = sample_points.positions + np.nan_to_num(sample_points.jacobians[:,:,k]) * preview_props.scale

                shader = line_shader
                batch = batch_for_shader(shader, 'LINES', {"position": lines})
                shader.bind()
                shader.uniform_float("color", from_html_color(palette0[k % len(palette0)]))
                shader.uniform_float("viewProjectionMatrix", matrix)
                batch.draw(shader)

# -------------------------------------------------------------------

class SmartGrabToolWidgetGroup(GizmoGroup):
    bl_idname = "SCENE_GGT_smart_grab_tool"
    bl_label = "Smart Grab Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    def setup(self, context):
        self.gizmos.new(SmartGrabToolWidget.bl_idname)

    def refresh(self, context):
        pass

# -------------------------------------------------------------------

classes = (
    SmartGrabToolWidget,
    SmartGrabToolWidgetGroup,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    register_cls()
    
def unregister():
    unregister_cls()
