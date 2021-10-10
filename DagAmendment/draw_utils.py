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
import gpu
import random
from mathutils import Matrix
from gpu_extras.presets import draw_circle_2d
from bgl import *

# -------------------------------------------------------------------

def has_attr(shader, attr):
    try:
        shader.attr_from_name(attr)
        return True
    except ValueError:
        return False

def has_uniform(shader, attr):
    try:
        shader.uniform_from_name(attr)
        return True
    except ValueError:
        return False

def set_uniform_int(shader, attr, value):
    if has_uniform(shader, attr):
        shader.uniform_int(attr, value)

def set_uniform_float(shader, attr, value):
    if has_uniform(shader, attr):
        shader.uniform_float(attr, value)

# -------------------------------------------------------------------

def draw_lines_2d(verts, color):
    import gpu
    from gpu.types import (
        GPUBatch,
        GPUVertBuf,
        GPUVertFormat,
    )

    with gpu.matrix.push_pop():
        fmt = GPUVertFormat()
        pos_id = fmt.attr_add(id="pos", comp_type='F32', len=2, fetch_mode='FLOAT')
        vbo = GPUVertBuf(len=len(verts), format=fmt)
        vbo.attr_fill(id=pos_id, data=verts)
        batch = GPUBatch(type='LINES', buf=vbo)
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch.program_set(shader)
        shader.uniform_float("color", color)
        batch.draw()

# -------------------------------------------------------------------

def draw_points(point_count):
    # for some reason this gives a different result than using gpu_extras.batch
    # (the normalized clip space is different)
    vao = Buffer(GL_INT, 1)
    glGenVertexArrays(1, vao)
    glBindVertexArray(vao[0])
    glDrawArrays(GL_POINTS, 0, point_count)
    glBindVertexArray(0)
    glDeleteVertexArrays(1, vao)

# -------------------------------------------------------------------
