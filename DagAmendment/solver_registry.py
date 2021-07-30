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

from .Solvers.AbstractSolver import AbstractSolver

from .registry_utils import load_registry, consolidate_register_functions

# -------------------------------------------------------------------

def instantiate_solver(context, solver_name):
    """Create a solver instance from its name and copy its properties
    from values stored in the scene settings."""
    solver_instance = solver_registry[solver_name]()
    solver_props = context.scene.diffparam.solver_properties(solver_name)
    
    for prop in solver_props.bl_rna.properties.keys():
        if prop == "name" or prop == "rna_type":
            continue
        setattr(solver_instance, prop, getattr(solver_props, prop))

    return solver_instance

# -------------------------------------------------------------------

solver_registry = load_registry("Solvers", AbstractSolver)

register, unregister = consolidate_register_functions("Solvers")
