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

from bpy.types import PropertyGroup, Object
from bpy.props import (
    IntProperty, StringProperty, PointerProperty,
    EnumProperty, BoolProperty, FloatProperty,
)

# -------------------------------------------------------------------

class HyperParameterPropertyCallbacks:
    """Callbacks used in HyperParameterProperty"""
    def update_path(self, context):
        self.auto_name()

    def update_object(self, context):
        self.auto_name()
        value = self.eval()
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)
        self.default = value

    def turn_auto_name_off(self, context):
        if self.lock:
            return
        self.auto_name = False

    def update_minmax(self, context):
        self.clamp_default_value()

    def update_default(self, context):
        if self.lock:
            return
        self.lock = True
        self.clamp_default_value()
        self.lock = False

    prop_presets = ['location', 'rotation_euler', 'scale']
    def get_prop_helper(self):
        if self.prop in __class__.prop_presets:
            return __class__.prop_presets.index(self.prop)
        else:
            return 3

    def set_prop_helper(self, value):
        if value < 3:
            self.prop = __class__.prop_presets[value]
        else:
            self.prop = ""

# -------------------------------------------------------------------

class HyperParameterProperty(PropertyGroup):
    cb = HyperParameterPropertyCallbacks

    name: StringProperty(
        name="Display name",
        update=cb.turn_auto_name_off
    )
    obj: PointerProperty(
        name="Object",
        type=Object,
        update=cb.update_object,
    )
    prop: StringProperty(
        name="Property",
        update=cb.update_path,
    )
    index: IntProperty(
        name="Index",
        min=0,
        max=3,
        update=cb.update_path,
    )
    minimum: FloatProperty(
        name="Minimum",
        default=0.0,
        update=cb.update_minmax,
    )
    maximum: FloatProperty(
        name="Maximum",
        default=1.0,
        update=cb.update_minmax,
    )
    default: FloatProperty(
        name="Default",
        default=0.5,
        update=cb.update_default,
    )

    # Advanced properties

    normalizer: FloatProperty(
        name="Normalizer",
        description="Multiplicative factor used when comparing parameters to each others (for single direction solver)",
        default=1.0,
    )

    # Hidden properties

    prop_helper: EnumProperty(
        name="Property",
        items=[
            ('location', 'Location', ''),
            ('rotation_euler', 'Rotation', ''),
            ('scale', 'Scale', ''),
            ('custom', 'Custom', ''),
        ],
        get=cb.get_prop_helper,
        set=cb.set_prop_helper,
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    lock: BoolProperty( # to prevent infinite recursion in callbacks
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    use_auto_name: BoolProperty(
        default=True,
        description="The name is automatically guessed until it is manually set",
        options={'HIDDEN'}
    )

    # Public methods

    def eval(self, target_object = None):
        """Return 0 if the parameter is not valid, and its value otherwise
        @param target_object allows to override self.obj"""
        if target_object is None:
            target_object = self.obj

        if target_object is None or not hasattr(target_object, self.prop):
            return 0.0
        
        attr = getattr(target_object, self.prop)

        if self.index < 0 or self.index >= len(attr):
            return 0.0

        return attr[self.index]

    def update(self, set=None, add=None):
        """Set or increment by <add> the value of the parameter if it is valid"""
        if self.obj is None or not hasattr(self.obj, self.prop):
            print(f"ERROR: object {self.obj} has no property {self.prop}")
            return
        
        attr = getattr(self.obj, self.prop)

        if self.index < 0 or self.index >= len(attr):
            print(f"ERROR: index out of bounds: {self.index} (should be in range (0, {len(attr) - 1})")
            return

        if set is not None:
            attr[self.index] = set
        elif add is not None:
            attr[self.index] += add

        self.obj.update_tag()

    def delta(self, fac=1e-5):
        """Define what a "small" increment means for this parameter"""
        delta = (self.maximum - self.minimum) * fac

        # Go away from boundary to ensure that we can measure finite difference without the risk of being clamped
        value = self.eval()
        to_min = value - self.minimum
        to_max = self.maximum - value
        if to_max < to_min:
            return -delta
        else:
            return delta

    # Internal methods

    def auto_name(self):
        if not self.use_auto_name:
            return
        short_props = {
            'location': 'T',
            'rotation_euler': 'R',
            'scale': 'S',
        }
        objname = self.obj.name if self.obj is not None else "(None)"
        p = short_props.get(self.prop, self.prop)
        x = ['X', 'Y', 'Z', 'W'][self.index]
        self.lock = True
        self.name = f'{objname} {p}{x}'
        self.lock = False

    def clamp_default_value(self):
        self.default = min(max(self.minimum, self.default), self.maximum)

    def keyframe_insert(self, value=None, frame=None):
        if frame is None:
            frame = bpy.context.scene.frame_current
        
        if value is not None:
            prev_value = self.eval()
            self.update(set=value)
        
        self.obj.keyframe_insert(data_path=self.prop, index=self.index, frame=frame)

        if value is not None:
            self.update(set=prev_value)

    def keyframe_delete(self, frame=None):
        if self.obj.animation_data.action is None:
            return
        if frame is None:
            frame = bpy.context.scene.frame_current
        self.obj.keyframe_delete(data_path=self.prop, index=self.index, frame=frame)

# -------------------------------------------------------------------

classes = (
    HyperParameterProperty,
)
