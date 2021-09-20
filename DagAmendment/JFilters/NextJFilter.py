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

from ..props import IntProperty, FloatProperty, BoolProperty

import numpy as np
from numpy.linalg import norm

from .AbstractJFilter import AbstractJFilter

class NextJFilter(AbstractJFilter):
    """
    Experiments toward the next jfilter
    """
    diffparam_label = "Next JFilter"
    diffparam_default = True

    extra_radius: IntProperty(
        name = "Extra Radius",
        description = "Offset added to the radius to define where to sample points of negative influence",
        default = 40,
    )

    contrast_dropout_threshold: FloatProperty(
        name = "Contrast Dropout Threshold",
        description = "Ratio to the best contrast (between inner and outer radii) bellow which a parameter's influence is ignored",
        default = 0.75,
        min = 0.0,
        max = 1.0,
    )

    variation_dropout_threshold: FloatProperty(
        name = "Variation Dropout Threshold",
        description = "Ratio to the least coefficient of variation beyond which the parameter is considered too noisy and hence ignored",
        default = 5.0,
        min = 1.0,
    )

    def __init__(self):
        self.min_least_variation = 1e-2

    def reduce_jacobian(self, brush_radius, sample_points):
        # The value exposed to the user is the inverse of lambda_v (more intuitive)
        lambda_v = 1 / self.variation_dropout_threshold
        lambda_c = self.contrast_dropout_threshold

        inside_brush_mask = norm(sample_points.ss_offsets, ord=2, axis=1) < brush_radius
        outside_brush_mask = np.invert(inside_brush_mask)

        inside_jacobian = np.nanmean(sample_points.jacobians[inside_brush_mask], axis=0)
        outside_jacobian = np.nanmean(sample_points.jacobians[outside_brush_mask], axis=0)

        inside_norm = norm(sample_points.jacobians[inside_brush_mask], axis=1)
        outside_norm = norm(sample_points.jacobians[outside_brush_mask], axis=1)

        inside_norm_mean = np.nanmean(inside_norm, axis=0)
        outside_norm_mean = np.nanmean(outside_norm, axis=0)
        inside_norm_std = np.nanstd(inside_norm, axis=0)
        outside_norm_std = np.nanstd(outside_norm, axis=0)

        # Compute coefficients of variation (v_k in the paper)
        inside_norm_cv = inside_norm_std / inside_norm_mean

        # 1. Drop out parameters of high variation within the inner brush
        min_inside_norm_cv = np.nan_to_num(inside_norm_cv, nan=np.inf).min()
        min_inside_norm_cv = max(min_inside_norm_cv, self.min_least_variation)
        variation_ratio = min_inside_norm_cv / inside_norm_cv
        variation_dropout = variation_ratio < lambda_v
        inside_norm_mean[variation_dropout] = 0.0

        contrast = inside_norm_mean / outside_norm_mean
        contrast[outside_norm_mean < 1e-8] = np.inf
        contrast[inside_norm_mean < 1e-8] = 0.0

        # 2. We cannot compare the raw parameters to each others,
        # but we can compare their contrasts (affine invariant, because
        # ratio (scale invariant) + differential (offset invariant))
        # Qualitatively, we want to foster high contrast parameters.
        contrast_dropout = contrast / contrast.max() < lambda_c

        dropout = np.logical_or(contrast_dropout, variation_dropout)

        # 3. Recompute average on significant points only (sort of median)
        significant_mask = inside_norm > np.maximum(inside_norm_mean - 2 * np.maximum(inside_norm_std, 1e-5), 1e-8)
        all_inside_jacobians = sample_points.jacobians[inside_brush_mask]
        (_, dim, n) = all_inside_jacobians.shape
        corrected_inside_jacobian = np.empty((dim, n), 'f')

        for k in range(n):
            mask_k = significant_mask[:,k]
            if mask_k.any():
                corrected_inside_jacobian[:,k] = np.nanmean(all_inside_jacobians[:,:,k][mask_k], axis=0)
            else:
                corrected_inside_jacobian[:,k] = 0

        #corrected_inside_jacobian = np.nanmean(sample_points.jacobians[inside_brush_mask][significant_mask], axis=0)

        # Dropped out hyper-parameters are excluded from solving by setting
        # their column to 0 in the output jacobian.
        jacobian = corrected_inside_jacobian
        jacobian[:,dropout] = 0.0

        return jacobian

    def transform_brush_radius(self, brush_radius):
        return brush_radius + self.extra_radius
