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

from random import randint

from bpy.types import PropertyGroup
from bpy.props import IntProperty

from .pools import cached_properties_pool

# -------------------------------------------------------------------

class CachedProperty(PropertyGroup):
    """Property used as proxy to access a cached value.
    This is used bellow to convert arbitrary classes to properties."""

    # This property must be redeclared in subclasses
    cache_key: IntProperty(
        name="Cache Key",
        options={'HIDDEN', 'SKIP_SAVE'},
        default=-1, # -1 means not cached
    )

    # Public methods

    def get_pool(self):
        return cached_properties_pool

    def create_instance(self, id_data):
        """Implement this in subclasses"""
        raise NotImplemented

    def set(self, data):
        if self.cache_key == -1:
            self.createKey()
        self.get_pool()[self.cache_key] = data

    def get(self, default=None, create=True):
        pool = self.get_pool()
        if self.cache_key in pool:
            data = pool[self.cache_key]
            if not hasattr(data, 'is_valid') or data.is_valid():
                return data
            else:
                if hasattr(data, 'cleanup'):
                    data.cleanup(bpy.context)
                del pool[self.cache_key]
        elif create:
            self.reset() # avoid key collisions
            data = self.create_instance(self.id_data)
            self.set(data)
            return data
        else:
            return default

    def reset(self):
        pool = self.get_pool()
        if self.cache_key in pool:
            data = pool[self.cache_key]
            if hasattr(data, 'cleanup'):
                data.cleanup(bpy.context)
            del pool[self.cache_key]
        self.cache_key = -1

    # Internals

    def createKey(self):
        pool = self.get_pool()
        if len(pool.keys()) > 100000:
            print("Warning: Heavy pool")
        while self.cache_key == -1 or self.cache_key in pool:
            self.cache_key = randint(0, 1<<24)
