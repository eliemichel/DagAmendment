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

from .JFilters.AbstractJFilter import AbstractJFilter

from .registry_utils import load_registry, consolidate_register_functions

# -------------------------------------------------------------------

def instantiate_jfilter(context, jfilter_name):
    """Create a jfilter instance from its name and copy its properties
    from values stored in the scene settings."""
    jfilter_instance = jfilter_registry[jfilter_name]()
    jfilter_props = context.scene.diffparam.jfilter_properties(jfilter_name)
    
    for prop in jfilter_props.bl_rna.properties.keys():
        if prop == "name" or prop == "rna_type":
            continue
        setattr(jfilter_instance, prop, getattr(jfilter_props, prop))

    return jfilter_instance

# -------------------------------------------------------------------

jfilter_registry = load_registry("JFilters", AbstractJFilter)

register, unregister = consolidate_register_functions("JFilters")
