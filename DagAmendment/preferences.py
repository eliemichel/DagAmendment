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
from bpy.props import BoolProperty

addon_idname = __package__.split(".")[0]

# -------------------------------------------------------------------

def getPreferences(context=None):
    if context is None: context = bpy.context
    preferences = context.preferences
    addon_preferences = preferences.addons[addon_idname].preferences
    return addon_preferences

# -------------------------------------------------------------------

class DagAmendmentPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_idname

    show_profiling_panel: BoolProperty(
        name = "Show Profiling Panel",
        description = "Show a panel with time measurements",
        default = False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="This is the reference implementation of the paper")

        col = layout.column(align=True)
        col.label(text="Michel, Élie and Boubekeur, Tamy (2021).")
        col.label(text="DAG Amendment for Inverse Control of Parametric Shapes,")
        col.label(text="ACM Transactions on Graphics (Proc. SIGGRAPH 2021)")

        layout.prop(self, 'show_profiling_panel')

# -------------------------------------------------------------------

classes = (DagAmendmentPreferences,)
register, unregister = bpy.utils.register_classes_factory(classes)
