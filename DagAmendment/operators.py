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

from . import param_operators
from . import dag_amendment_operators
from . import smartgrab_operators
from . import dev_operators

submodules = (
    param_operators,
    dag_amendment_operators,
    smartgrab_operators,
    dev_operators,
)

# -------------------------------------------------------------------

# Import all exposed classes from submodules
for m in submodules:
    for c in m.classes:
        locals()[c.__name__] = c

# -------------------------------------------------------------------

def register():
    for m in submodules:
        m.register()

def unregister():
    for m in submodules[::-1]:
        m.unregister()
