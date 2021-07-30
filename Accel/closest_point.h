/**
 * This file is part of DagAmendment, the reference implementation of:
 *
 *   Michel, Élie and Boubekeur, Tamy (2021).
 *   DAG Amendment for Inverse Control of Parametric Shapes
 *   ACM Transactions on Graphics (Proc. SIGGRAPH 2021), 173:1-173:14.
 *
 * Copyright (c) 2020-2021 -- Télécom Paris (Élie Michel <elie.michel@telecom-paris.fr>)
 * 
 * The MIT license:
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the “Software”), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * The Software is provided “as is”, without warranty of any kind, express or
 * implied, including but not limited to the warranties of merchantability,
 * fitness for a particular purpose and non-infringement. In no event shall the
 * authors or copyright holders be liable for any claim, damages or other
 * liability, whether in an action of contract, tort or otherwise, arising
 * from, out of or in connection with the software or the use or other dealings
 * in the Software.
 */

#pragma once

template<typename Float, typename Vec3>
struct Hit {
    Vec3 point;
    Float ba, bb, bc; // barycentric coords
};

template<typename Float, typename Vec3>
Hit<Float,Vec3> closestPointTriangle(Vec3 const& p, Vec3 const& a, Vec3 const& b, Vec3 const& c)
{
    const Vec3 ab = b - a;
    const Vec3 ac = c - a;
    const Vec3 ap = p - a;

    const Float d1 = dot(ab, ap);
    const Float d2 = dot(ac, ap);
    if (d1 <= 0.f && d2 <= 0.f) {
        return Hit<Float,Vec3> {
            a,
            1.0f, 0.0f, 0.0f
        };
    }

    const Vec3 bp = p - b;
    const Float d3 = dot(ab, bp);
    const Float d4 = dot(ac, bp);
    if (d3 >= 0.f && d4 <= d3) {
        return Hit<Float,Vec3> {
            b,
            0.0f, 1.0f, 0.0f
        };
    }

    const Vec3 cp = p - c;
    const Float d5 = dot(ab, cp);
    const Float d6 = dot(ac, cp);
    if (d6 >= 0.f && d5 <= d6) {
        return Hit<Float,Vec3> {
            c,
            0.0f, 0.0f, 1.0f
        };
    }

    const Float vc = d1 * d4 - d3 * d2;
    if (vc <= 0.f && d1 >= 0.f && d3 <= 0.f)
    {
        const Float v = d1 / (d1 - d3);
        return Hit<Float,Vec3> {
            a + v * ab,
            1.0f - v, v, 0.0f
        };
    }

    const Float vb = d5 * d2 - d1 * d6;
    if (vb <= 0.f && d2 >= 0.f && d6 <= 0.f)
    {
        const Float w = d2 / (d2 - d6);
        return Hit<Float,Vec3> {
            a + w * ac,
            1.0f - w, 0.0f, w
        };
    }

    const Float va = d3 * d6 - d5 * d4;
    if (va <= 0.f && (d4 - d3) >= 0.f && (d5 - d6) >= 0.f)
    {
        const Float v = (d4 - d3) / ((d4 - d3) + (d5 - d6));
        return Hit<Float,Vec3> {
            b + v * (c - b),
            0.0f, 1.0f - v, v
        };
    }

    const Float denom = 1.f / (va + vb + vc);
    const Float v = vb * denom;
    const Float w = vc * denom;
    return Hit<Float,Vec3> {
        a + v * ab + w * ac,
        1.0f - v - w, v, w
    };
}
