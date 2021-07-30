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

# -------------------------------------------------------------------

"""
The UI is split into two panels reflecting the intended workflow
associated to this tool:

Rig:
Used to create the list of exposed parameters and setup their
min/max/default values. This is a designer/rigger's job.

Animation:
Used to interact with the parametric shapes once it's been set up.
This panels intends to be as easy/fluid as possible to use for one
to focus on the art.
"""

import bpy
from bpy.types import Panel, Menu, VIEW3D_PT_gizmo_display
from . import operators as ops

from .preferences import getPreferences

# -------------------------------------------------------------------

class ParametricShapeAnimPanel(Panel):
    """This panel is for interacting with the parametric shape once
    it's been set up in the Rig panel"""
    bl_label = "Parametric Shape - Anim"
    bl_idname = "SCENE_PT_ParametricShapeAnim"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        for i, param in enumerate(scene.diffparam_parameters):
            row = layout.row(align=True)
            self.draw_param_value(param, row)
            row.operator(ops.SetActiveParameter.bl_idname,icon='RESTRICT_SELECT_OFF', text="").index = i
        layout.operator(ops.ResetAllParameters.bl_idname)

    def draw_param_value(self, param, layout):
        objname = param.obj.name if param.obj is not None else "___"
        if param.obj is not None and hasattr(param.obj, param.prop):
            layout.prop(param.obj, param.prop, index=param.index, text=param.name)
        else:
            layout.label(text=f"{param.name} (invalid)")

# -------------------------------------------------------------------

class DIFFPARAM_UL_ParameterUIList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        param = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(param, "obj", text="", emboss=False, icon_value=icon)
            layout.prop(param, "prop", text="", emboss=False, icon_value=icon)
            layout.prop(param, "index", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

# -------------------------------------------------------------------

class DIFFPARAM_MT_list_context_menu(Menu):
    bl_label = "Parameter Specials"

    def draw(self, _context):
        layout = self.layout
        layout.operator(ops.RemoveAllParameters.bl_idname)
        layout.operator(ops.SelectParameterFromActiveObject.bl_idname)

# -------------------------------------------------------------------

class ParametricShapeRigPanel(Panel):
    """This panel is for setting up the parametric shape, defining the
    parameters and their boundaries."""
    bl_label = "Parametric Shape - Rig"
    bl_idname = "SCENE_PT_ParametricShapeRig"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.prop(scene.diffparam, 'view_layer_name')

        self.draw_setup_op(scene, layout)

        layout.operator(ops.DagAmendment.bl_idname)

        self.draw_param_list(scene, layout)

        i = scene.diffparam_active_parameter
        if i >= 0 and i < len(scene.diffparam_parameters):
            self.draw_param_props(scene.diffparam_parameters[i], layout)

    def draw_setup_op(self, scene, layout):
        row = layout.row(align=True)
        row.operator(ops.SetupFromCollection.bl_idname)
        row.prop(scene, 'diffparam_controller_collection', text="")

    def draw_param_list(self, scene, layout):
        row = layout.row()

        row.template_list(
            "DIFFPARAM_UL_ParameterUIList", # or "UI_UL_list"
            "", # local id
            scene,
            "diffparam_parameters", # list prop
            scene,
            "diffparam_active_parameter") # index prop

        col = row.column(align=True)
        col.operator(ops.AddParameter.bl_idname, icon='ADD', text="")
        col.operator(ops.RemoveActiveParameter.bl_idname, icon='REMOVE', text="")

        col.separator()
        col.menu("DIFFPARAM_MT_list_context_menu", icon='DOWNARROW_HLT', text="")

        if len(scene.diffparam_parameters) > 1:
            col.separator()
            col.operator(ops.MoveActiveParameter.bl_idname, icon='TRIA_UP', text="").direction = 'UP'
            col.operator(ops.MoveActiveParameter.bl_idname, icon='TRIA_DOWN', text="").direction = 'DOWN'

    def draw_param_props(self, param, layout):
        col = layout.column()
        self.draw_param_target(param, col)

        col.separator()
        self.draw_param_settings(param, col)

        col.separator()
        self.draw_param_value(param, col)

    def draw_param_target(self, param, layout):
        layout.label(text="Driven Property:")
        layout.prop(param, "obj")
        row = layout.row(align=True)
        row.prop(param, "prop_helper", text="")
        x = row.column(align=True) 
        sub = x.column(align=True)
        sub.enabled = param.prop_helper == 'custom'
        sub.prop(param, "prop", text="")
        x.prop(param, "index")

    def draw_param_settings(self, param, layout):
        layout.label(text="Settings:")
        row = layout.row(align=True)
        row.prop(param, "minimum")
        row.prop(param, "maximum")
        layout.prop(param, "default")
        layout.prop(param, "name")

        layout.label(text="Advanced:")
        layout.prop(param, "normalizer")

    def draw_param_value(self, param, layout):
        layout.label(text="Value:")
        objname = param.obj.name if param.obj is not None else "___"
        value = "[error]"
        if param.prop != "" and param.obj is not None and hasattr(param.obj, param.prop):
            attr = getattr(param.obj, param.prop)
            if len(attr) > param.index:
                value = attr[param.index]
        if param.obj is not None and hasattr(param.obj, param.prop):
            layout.prop(param.obj, param.prop, index=param.index, text=f"{objname}.{param.prop}[{param.index}]")
        else:
            sub = layout.column(align=True)
            sub.enabled = False
            sub.prop(param, 'default', text=f"{objname}.{param.prop}[{param.index}]")

# -------------------------------------------------------------------

class ParametricShapeProfilingPanel(Panel):
    """Panel for dev and debug tools"""
    bl_label = "Parametric Shape - Profiling"
    bl_idname = "SCENE_PT_ParametricShapeProfiling"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        return getPreferences(context).show_profiling_panel

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        self.draw_profiling(scene, layout)
        
        layout.operator(ops.CopyProfiling.bl_idname)
        layout.operator(ops.ResetProfiling.bl_idname)

    def draw_profiling(self, scene, layout):
        layout.label(text="Profiling:")

        col = layout.column(align=True)
        
        for prof in scene.profiling.counters:
            col.label(text=f" - {prof.name}: {prof.summary()}")

# -------------------------------------------------------------------

def VIEW3D_MT_diffparam_gizmos(self, context):
    col = self.layout.column()
    col.label(text="DiffParam")
    col.prop(context.scene.diffparam, 'show_slider_overlay')

# -------------------------------------------------------------------

classes = (
    DIFFPARAM_UL_ParameterUIList,
    DIFFPARAM_MT_list_context_menu,
    ParametricShapeAnimPanel,
    ParametricShapeRigPanel,
    ParametricShapeProfilingPanel,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    register_cls()
    VIEW3D_PT_gizmo_display.append(VIEW3D_MT_diffparam_gizmos)

def unregister():
    VIEW3D_PT_gizmo_display.remove(VIEW3D_MT_diffparam_gizmos)
    unregister_cls()
