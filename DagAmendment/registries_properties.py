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
from bpy.types import PropertyGroup
from bpy.props import PointerProperty

from .props import BoolProperty, IntProperty, FloatProperty
from .solver_registry import solver_registry
from .jfilter_registry import jfilter_registry

# A fistull of introspection magic to import Properties defined in Solvers

# -------------------------------------------------------------------

# Convert our GPL free property types into bpy's
prop_type_lut = {
    BoolProperty: bpy.props.BoolProperty,
    IntProperty: bpy.props.IntProperty,
    FloatProperty: bpy.props.FloatProperty,
}

# -------------------------------------------------------------------

class SolverPropertiesPool(PropertyGroup):
    __annotations__ = {}

solver_properties_classes = []

for solver_name, Solver in solver_registry.items():
    class SolverProperties(PropertyGroup):
        __annotations__ = {}
    SolverProperties.__name__ = solver_name + "Properties"
    
    if hasattr(Solver, '__annotations__'):
        for prop_name, prop_def in Solver.__annotations__.items():
            SolverProperties.__annotations__[prop_name] = prop_type_lut[type(prop_def)](**prop_def.kwargs)

    SolverPropertiesPool.__annotations__[solver_name] = PointerProperty(type=SolverProperties)
    solver_properties_classes.append(SolverProperties)

# -------------------------------------------------------------------

class JFilterPropertiesPool(PropertyGroup):
    __annotations__ = {}

jfilter_properties_classes = []

for jfilter_name, JFilter in jfilter_registry.items():
    class JFilterProperties(PropertyGroup):
        __annotations__ = {}
    JFilterProperties.__name__ = jfilter_name + "Properties"
    
    if hasattr(JFilter, '__annotations__'):
        for prop_name, prop_def in JFilter.__annotations__.items():
            JFilterProperties.__annotations__[prop_name] = prop_type_lut[type(prop_def)](**prop_def.kwargs)

    JFilterPropertiesPool.__annotations__[jfilter_name] = PointerProperty(type=JFilterProperties)
    jfilter_properties_classes.append(JFilterProperties)

# -------------------------------------------------------------------

classes = (
    *solver_properties_classes,
    *jfilter_properties_classes,
    SolverPropertiesPool,
    JFilterPropertiesPool,
)
