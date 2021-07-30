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
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from random import random
from pathlib import Path

from .profiling import Timer

# -------------------------------------------------------------------

class ResetProfiling(Operator):
    bl_idname = "diffparam.reset_profiling"
    bl_label = "Reset Profiling Counters"

    def execute(self, context):
        scene = context.scene
        for c in scene.profiling.counters:
            c.reset()
        return {'FINISHED'}

# -------------------------------------------------------------------

class CopyProfiling(Operator):
    """Copy profiling counters to clipboard"""
    bl_idname = "diffparam.copy_profiling"
    bl_label = "Copy Profiling Counters"

    def execute(self, context):
        msg = ""
        scene = context.scene
        for c in scene.profiling.counters:
            msg += f" - {c.name}: {c.summary()}\n"
        bpy.context.window_manager.clipboard = msg
        return {'FINISHED'}

# -------------------------------------------------------------------

classes = (
    ResetProfiling,
    CopyProfiling,
)
register, unregister = bpy.utils.register_classes_factory(classes)
