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

bl_info = {
    "name": "Dag Amendment",
    "author": "Élie Michel <elie.michel@telecom-paris.fr>",
    "version": (1, 0, 1),
    "blender": (2, 93, 0),
    "location": "Properties > Scene",
    "description": "DAG Amendment for Inverse Control of Parametric Shapes",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://perso.telecom-paris.fr/boubek/papers/DAG_Amendment",
    "support": "COMMUNITY",
    "category": "3D view",
}

# -------------------------------------------------------------------

def on_reload_plugins():
    from . import pools
    pools.cached_properties_pool = {}

dev = False

# When loaded is already in local, we know this is called by "Reload plugins"
if locals().get('loaded') or dev:
    loaded = False
    from importlib import reload
    from sys import modules
    import os

    for i in range(2):
        modules[__name__] = reload(modules[__name__])
        submodules = list(modules.items())
        for name, mod in submodules:
            if name not in modules:
                continue  # may have changed during iteration
            if name.startswith(f"{__package__}."):
                if mod.__file__ is not None and not os.path.isfile(mod.__file__):
                    print(f"module does not exist: {name}")
                    # file has been removed
                    if name in modules:
                        del modules[name]
                    if name in globals():
                        del globals()[name]
                else:
                    print(f"Reloading: {mod}")
                    new_mod = reload(mod)
                    if name in modules:
                        modules[name] = new_mod
                    if name in globals():
                        globals()[name] = new_mod
        #del reload, modules
    on_reload_plugins()

# -------------------------------------------------------------------
    
from . import DepsgraphNodes
from . import jfilter_registry
from . import solver_registry
from . import preferences
from . import properties
from . import operators
from . import panels
from . import overlays
from . import tools
from . import handlers

submodules = (
    DepsgraphNodes,
    jfilter_registry,
    solver_registry,
    preferences,
    properties,
    operators,
    panels,
    overlays,
    tools,
    handlers,
)

def register():
    for m in submodules:
        m.register()

def unregister():
    for m in submodules[::-1]:
        m.unregister()

loaded = True
