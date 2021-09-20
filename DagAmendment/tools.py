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
from bpy.types import WorkSpaceTool, Menu, Operator
from gpu_extras.presets import draw_circle_2d

from . import operators as ops
from . import overlays
from .utils import get_operator_properties
from .draw_utils import draw_lines_2d

# -------------------------------------------------------------------

class SolverPropertiesMenu(Menu):
    bl_label = "Solver Properties"
    bl_idname = "DIFFPARAM_MT_solver_properties"
    
    def draw(self, context):
        layout = self.layout
        layout.emboss = 'NORMAL'
        smartgrab_props = get_operator_properties(context, ops.SmartGrab.bl_idname)

        solver_props = context.scene.diffparam.solver_properties(smartgrab_props.solver)
        
        layout.label(text="Solver Properties")
        for prop in solver_props.bl_rna.properties.keys():
            if prop == "name" or prop == "rna_type":
                continue
            layout.prop(solver_props, prop)

# -------------------------------------------------------------------

class JFilterPropertiesMenu(Menu):
    bl_label = "JFilter Properties"
    bl_idname = "DIFFPARAM_MT_jfilter_properties"
    
    def draw(self, context):
        layout = self.layout
        layout.emboss = 'NORMAL'
        smartgrab_props = get_operator_properties(context, ops.SmartGrab.bl_idname)

        jfilter_props = context.scene.diffparam.jfilter_properties(smartgrab_props.jfilter)
        
        layout.label(text="JFilter Properties")
        for prop in jfilter_props.bl_rna.properties.keys():
            if prop == "name" or prop == "rna_type":
                continue
            layout.prop(jfilter_props, prop)

# -------------------------------------------------------------------

class DisplayPropertiesMenu(Menu):
    bl_label = "Display Properties"
    bl_idname = "DIFFPARAM_MT_display_properties"
    
    def draw(self, context):
        layout = self.layout
        layout.emboss = 'NORMAL'
        preview_props = context.scene.diffparam.sample_points_preview
        smartgrab_props = get_operator_properties(context, ops.SmartGrab.bl_idname)
        layout.label(text="Display Properties")

        layout.prop(preview_props, "scale")
        layout.prop(preview_props, "brush_color")
        layout.prop(preview_props, "show_outer_radius")

# -------------------------------------------------------------------

class SamplerPropertiesMenu(Menu):
    bl_label = "Sampler Properties"
    bl_idname = "DIFFPARAM_MT_sampler_properties"
    
    def draw(self, context):
        layout = self.layout
        layout.emboss = 'NORMAL'
        props = get_operator_properties(context, ops.SmartGrab.bl_idname)
        layout.label(text="Sampler Properties")

        layout.prop(props, "brush_radius")
        layout.prop(props, "sample_count")
        layout.prop(props, "jacobian_update_period")
        layout.prop(props, "relative_delta_pow")
        layout.prop(props, "max_projection_error_pow")
        layout.prop(props, "discard_by_world_distance")

# -------------------------------------------------------------------

class SmartGrabTool(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_idname = "diffparam.smart_grab_tool"
    bl_label = "Smart Grab"
    bl_description = '\n'.join([
        "Grab points from a parametric shape",
        "and auto updates parameters to fit the move",
    ])
    bl_icon = "ops.generic.select_circle"
    bl_widget = overlays.SmartGrabToolWidgetGroup.bl_idname
    bl_keymap = (
        (ops.SmartGrab.bl_idname,
            {"type": 'LEFTMOUSE', "value": 'PRESS'},
            {"properties": []}),
        (ops.ScaleSmartGrabBrush.bl_idname,
            {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True},
            {"properties": []}),
        (ops.ScaleSmartGrabBrush.bl_idname,
            {"type": 'F', "value": 'PRESS'},
            {"properties": []}),
    )
    bl_cursor = 'NONE' # ('DEFAULT', 'NONE', 'WAIT', 'CROSSHAIR', 'MOVE_X', 'MOVE_Y', 'KNIFE', 'TEXT', 'PAINT_BRUSH', 'PAINT_CROSS', 'DOT', 'ERASER', 'HAND', 'SCROLL_X', 'SCROLL_Y', 'SCROLL_XY', 'EYEDROPPER')

    def draw_settings(context, layout, tool):
        props = tool.operator_properties(ops.SmartGrab.bl_idname)

        row = layout.row(align=True)
        row.prop(props, "solver", text="")
        row.menu(SolverPropertiesMenu.bl_idname, text="", icon='OPTIONS')

        row = layout.row(align=True)
        row.prop(props, "jfilter", text="")
        row.menu(JFilterPropertiesMenu.bl_idname, text="", icon='OPTIONS')

        layout.menu(SamplerPropertiesMenu.bl_idname, text="Sampler", icon='OPTIONS')
        layout.menu(DisplayPropertiesMenu.bl_idname, text="Display", icon='OPTIONS')

    def draw_cursor(context, tool, xy):
        diffparam = context.scene.diffparam
        try: # try/catch to avoid spamming subsequent to another error
            smartgrab_props = tool.operator_properties(ops.SmartGrab.bl_idname)
        except RuntimeError:
            return
        preview_props = diffparam.sample_points_preview
        radius = smartgrab_props.brush_radius
        #for offset, color in [ (-1, (0,0,0,0.3)), (0, (1,1,1,0.5)) ]:
        for offset, color in [ (0, preview_props.brush_color) ]:
            x, y = xy
            if radius > 1:
                draw_circle_2d((x + offset, y + offset), color, radius, 200)
            if radius < 5:
                draw_lines_2d([
                    (x + 15 + offset, y + offset), (x + radius + offset, y + offset),
                    (x - 15 + offset, y + offset), (x - radius + offset, y + offset),
                    (x + offset, y + 15 + offset), (x + offset, y + radius + offset),
                    (x + offset, y - 15 + offset), (x + offset, y - radius + offset),
                ], color)

            if (smartgrab_props.jfilter in {'NegativeJFilter', 'NextJFilter'}
                and preview_props.show_outer_radius):
                jfilter_props = diffparam.jfilter_properties(smartgrab_props.jfilter)
                r = radius + jfilter_props.extra_radius
                draw_circle_2d((x + offset, y + offset), color, r, 200)

# -------------------------------------------------------------------

tool_classes = (
    SmartGrabTool,
)

classes = (
    SolverPropertiesMenu,
    JFilterPropertiesMenu,
    DisplayPropertiesMenu,
    SamplerPropertiesMenu,
)

register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    register_cls()
    if not bpy.app.background:
        for cls in tool_classes:
            bpy.utils.register_tool(cls)

def unregister():
    for cls in tool_classes[::-1]:
        bpy.utils.unregister_tool(cls)
    unregister_cls()
    
