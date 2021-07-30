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
    Scene, Object, PropertyGroup, Collection
)
from bpy.props import (
    FloatProperty, IntProperty, StringProperty, BoolProperty,
    PointerProperty, CollectionProperty, EnumProperty
)

from random import randint
from math import sqrt
from .profiling import Timer

# -------------------------------------------------------------------

class ProfilingCounterProperty(PropertyGroup):
    sample_count: IntProperty(
        name="Sample Count",
        description="Number of sampled values accumulated in the total count",
        default=0,
        min=0,
    )

    accumulated: FloatProperty(
        name="Accumulated Values",
        description="Sum of all samples",
        default=0.0,
    )

    accumulated_sq: FloatProperty(
        name="Accumulated Squared Values",
        description="Sum of the square value of all samples (to compute standard deviation)",
        default=0.0,
    )

    def average(self):
        if self.sample_count == 0:
            return 0
        else:
            return self.accumulated / self.sample_count

    def stddev(self):
        if self.sample_count == 0:
            return 0
        else:
            avg = self.average()
            var = self.accumulated_sq / self.sample_count - avg * avg
            return sqrt(max(0, var))

    def add_sample(self, value):
        if hasattr(value, 'ellapsed'):
            value = value.ellapsed()
        self.sample_count += 1
        self.accumulated += value
        self.accumulated_sq += value * value

    def reset(self):
        self.sample_count = 0
        self.accumulated = 0.0
        self.accumulated_sq = 0.0

    def summary(self):
        """returns something like XXms (±Xms, X samples)"""
        return (
            f"{self.average()*1000.:.03}ms " +
            f"(±{self.stddev()*1000.:.03}ms, " +
            f"{self.sample_count} samples)"
        )

# -------------------------------------------------------------------

class ProfilingCounterPool(PropertyGroup):
    """wrapper around a collection of ProfilingCounterProperty that
    acts like a defaultdict"""
    counters: CollectionProperty(
        type=ProfilingCounterProperty,
        name="Counters",
        description="Collection of profiling counters",
    )

    def __getitem__(self, key):
        if key not in self.counters:
            c = self.counters.add()
            c.name = key
            return c
        else:
            return self.counters[key]

    def summary(self):
        return [f" - {prof.name}: {prof.summary()}" for prof in self.counters]

# -------------------------------------------------------------------

classes = (
    ProfilingCounterProperty,
    ProfilingCounterPool,
)
register_cls, unregister_cls = bpy.utils.register_classes_factory(classes)

def register():
    register_cls()
    Scene.profiling = PointerProperty(type=ProfilingCounterPool)

def unregister():
    unregister_cls()
    del Scene.profiling
