# This file is part of DagAmendment, the reference implementation of:
#
#   Michel, Élie and Boubekeur, Tamy (2021).
#   DAG Amendment for Inverse Control of Parametric Shapes
#   ACM Transactions on Graphics (Proc. SIGGRAPH 2021), 173:1-173:14.
#
# Copyright (c) 2020-2021 -- Télécom Paris (Élie Michel <elie.michel@telecom-paris.fr>)
# 
# The MIT license:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software is provided “as is”, without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and non-infringement. In no event shall the
# authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising
# from, out of or in connection with the software or the use or other dealings
# in the Software.

# no bpy here

import numpy as np
from numpy.linalg import svd, norm, inv

# -------------------------------------------------------------------

def normalize(v):
	return v / norm(v, keepdims=1)

# -------------------------------------------------------------------

def sqnorm(x):
    return np.inner(x, x)

# -------------------------------------------------------------------

def random_in_unit_disc():
    """Sample a random 2D point in the unit disk"""
    sample = None
    while sample is None or norm(sample) > 1:
        sample = np.random.random((2,)) * 2 - 1
    return sample

# -------------------------------------------------------------------

def matvecmul(M, v):
    """
    @param M batch of matrices, or single matrix
    @param v batch of vectors
    """
    return np.squeeze(np.matmul(M, v[:,:,np.newaxis]), axis=-1)

# -------------------------------------------------------------------

def svd_inverse(J):
    """
    @param J is a (param_count, 2 or 3) matrix of screen or world space
    variations of a point's position when altering parameters
    (the transposed Jacobian)
    @return its pseudo inverse and a kernel matrix so that
    the space of solutions of J.T @ X = PT is
    X = Jinv @ PT + ker @ Y for any Y"""
    U, S, Vh = svd(J)
    Sinv = np.zeros((len(U), len(Vh)))
    for i, s_i in enumerate(S):
        Sinv[i][i] = 1.0 / s_i if abs(s_i) > 1e-6 else 0.0
    Jinv = U @ Sinv @ Vh
    ker = np.eye(len(J)) - Jinv @ J.T
    return Jinv, ker

# -------------------------------------------------------------------

