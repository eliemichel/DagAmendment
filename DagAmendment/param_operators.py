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
from bpy.types import Operator, Collection
from bpy.props import PointerProperty, IntProperty, EnumProperty, BoolProperty, FloatProperty
from mathutils import Vector

# -------------------------------------------------------------------

class AddParameter(Operator):
    """Create a new parameter. A parameter is a publicly exposed property of an object
    used as input of the global scene rig."""
    bl_idname = "diffparam.add_parameter"
    bl_label = "Add Parameter"

    def execute(self, context):
        scene = context.scene
        param = scene.diffparam_parameters.add()
        param.prop = "location"
        scene.diffparam_active_parameter = len(scene.diffparam_parameters) - 1
        return {'FINISHED'}

# -------------------------------------------------------------------

class RemoveActiveParameter(Operator):
    """Remove the parameter currently refered to by the
    scene.diffparam_active_parameter property"""
    bl_idname = "diffparam.remove_active_parameter"
    bl_label = "Remove Active Parameter"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        i = scene.diffparam_active_parameter
        return i >= 0 and i < len(scene.diffparam_parameters)

    def execute(self, context):
        scene = context.scene
        params = scene.diffparam_parameters
        i = scene.diffparam_active_parameter
        params.remove(i)
        scene.diffparam_active_parameter = min(
            i,
            len(params) - 1
        )
        return {'FINISHED'}

# -------------------------------------------------------------------

class RemoveAllParameters(Operator):
    bl_idname = "diffparam.remove_all_parameters"
    bl_label = "Remove All Parameters"

    @classmethod
    def poll(cls, context):
        return len(context.scene.diffparam_parameters) > 0

    def execute(self, context):
        context.scene.diffparam_parameters.clear()
        return {'FINISHED'}

# -------------------------------------------------------------------

class MoveActiveParameter(Operator):
    """Move in the UI the parameter currently refered to by the
    scene.diffparam_active_parameter property, either UP or DOWN"""
    bl_idname = "diffparam.move_active_parameter"
    bl_label = "Move Active Parameter"

    direction: EnumProperty(
        name='Direction',
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        ),
    )

    @classmethod
    def poll(cls, context):
        scene = context.scene
        i = scene.diffparam_active_parameter
        l = len(scene.diffparam_parameters)
        return l > 1 and i >= 0 and i < l

    def execute(self, context):
        scene = context.scene
        i = scene.diffparam_active_parameter
        eps = 1 if self.direction == 'DOWN' else -1
        scene.diffparam_parameters.move(i, i + eps)
        scene.diffparam_active_parameter = min(max(
            0,
            i + eps),
            len(scene.diffparam_parameters) - 1
        )
        return {'FINISHED'}

# -------------------------------------------------------------------

class SelectParameterFromActiveObject(Operator):
    """Select the first parameter that refers to the object being
    currently active."""
    bl_idname = "diffparam.select_parameter_from_active_object"
    bl_label = "Select from Active Object"

    @classmethod
    def poll(cls, context):
        return len(context.scene.diffparam_parameters) > 0

    def execute(self, context):
        scene = context.scene
        for i, param in enumerate(scene.diffparam_parameters):
            if param.obj == context.active_object:
                scene.diffparam_active_parameter = i
                break
        return {'FINISHED'}

# -------------------------------------------------------------------

class SetActiveParameter(Operator):
    """Set the active parameter by index, and optionnaly select the
    corresponding object in the 3D scene."""
    bl_idname = "diffparam.set_active_parameter"
    bl_label = "Select the parameter in the rig panel"

    index: IntProperty(
        name="Parameter Index",
        description="Index of the parameter to make active."
    )

    select_object: BoolProperty(
        name="Select the controler object",
        description="Also select the object to which the target parameter is associated.",
        default=True
    )

    def execute(self, context):
        scene = context.scene
        if self.index >= 0 and self.index < len(scene.diffparam_parameters):
            scene.diffparam_active_parameter = self.index    
            if self.select_object:
                objects = context.view_layer.objects
                for o in objects:
                    o.select_set(False)
                obj = scene.diffparam_parameters[self.index].obj
                obj.select_set(True)
                objects.active = obj
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

# -------------------------------------------------------------------

class SetupFromCollection(Operator):
    """Walk through the scene.diffparam_controller_collection collection
    to create parameters for all the non-locked loc/rot/scale attributes"""
    bl_idname = "diffparam.setup_from_collection"
    bl_label = "Setup From Collection"

    @classmethod
    def poll(cls, context):
        return context.scene.diffparam_controller_collection is not None

    def extend_unlocked_parameters(self, obj, params):
        """Append to 'params' the ids of the loc/rot/scale parameters
        of 'obj' when they are not locked"""
        for i in range(3):
            if not obj.lock_location[i]:
                params.append((obj, 'location', i))
        if obj.rotation_mode == 'QUATERNION':
            for i in range(3):
                if not obj.lock_rotation[i]:
                    params.append((obj, 'rotation_quaternion', i))
            if obj.lock_rotations_4d and not obj.lock_rotation_w:
                params.append((obj, 'rotation_quaternion', 3))
        else:
            for i in range(3):
                if not obj.lock_rotation[i]:
                    params.append((obj, 'rotation_euler', i))
        for i in range(3):
            if not obj.lock_scale[i]:
                params.append((obj, 'scale', i))


    def init_parameter_lut(self, scene):
        self.param_lut = set()
        for param in scene.diffparam_parameters:
            self.param_lut.add(
                (param.obj, param.prop, param.index)
            )

    def does_parameter_exist(self, param_id):
        if not hasattr(self, 'param_lut'):
            raise Exception("init_parameter_lut() must be called before any use of does_parameter_exist()")
        return param_id in self.param_lut

    def add_parameter(self, scene, param_id):
        (obj, prop, index) = param_id
        default = getattr(obj, prop)[index]
        param = scene.diffparam_parameters.add()
        param.prop = prop
        param.index = index
        param.minimum = min(0, default)
        param.maximum = max(default, 1)
        param.default = default
        param.obj = obj

    def execute(self, context):
        scene = context.scene
        collection = scene.diffparam_controller_collection

        param_ids = []
        for obj in collection.all_objects:
            if obj.visible_get():
                self.extend_unlocked_parameters(obj, param_ids)

        self.init_parameter_lut(scene)
        for h in param_ids:
            if not self.does_parameter_exist(h):
                self.add_parameter(scene, h)

        return {'FINISHED'}

# -------------------------------------------------------------------

class ResetAllParameters(Operator):
    """Set all parameters to their default value"""
    bl_idname = "diffparam.reset_all_parameters"
    bl_label = "Reset All Parameters"

    @classmethod
    def poll(cls, context):
        return len(context.scene.diffparam_parameters) > 0

    def execute(self, context):
        for param in context.scene.diffparam_parameters:
            if param.obj is not None and hasattr(param.obj, param.prop):
                attr = getattr(param.obj, param.prop)
                if param.index < len(attr):
                    attr[param.index] = param.default
        return {'FINISHED'}

# -------------------------------------------------------------------

classes = (
    AddParameter,
    RemoveActiveParameter,
    RemoveAllParameters,
    MoveActiveParameter,
    SelectParameterFromActiveObject,
    SetActiveParameter,
    SetupFromCollection,
    ResetAllParameters,
)
register, unregister = bpy.utils.register_classes_factory(classes)
