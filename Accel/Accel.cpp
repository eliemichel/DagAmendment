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

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <glm/glm.hpp>

#include <iostream>
#include <limits>

#include "closest_point.h"

constexpr std::tuple<int,int,int> version(1, 0, 0);

namespace py = pybind11;

#define UNUSED(x) (void)x

// ======================================================================== //
//                              main entry point                            //
// ======================================================================== //

/**
 * For each sample, find the closest point on the mesh defined by (vertices, triangles)
 * @param vertices (n,3) array of vertex coordinates
 * @param triangles (m,3) array of indices in (0,n-1) telling which vertiçces
 *                  are connected by each face
 * @param samples (p,3) array of points to project
 * @return (
 *     projections (p,3) array of closest points to sample within the mesh
 *     bcoords (p,2) array of barycentric coordinates of the closest points within their triangle
 *     proj_triangles (p,) array of triangle indices, telling which face the closest point belongs to
 * )
 */
template<typename Float, typename Vec3>
std::tuple<py::array_t<Float>,py::array_t<Float>,py::array_t<int>>
project(py::array_t<Float> vertices, py::array_t<int> triangles, py::array_t<Float> samples)
{
	py::buffer_info vertices_buf = vertices.request();

	if (vertices_buf.ndim != 2)
		throw std::runtime_error("vertices must have dimension 2");

	if (vertices_buf.shape[1] != 3)
		throw std::runtime_error("vertices must have shape (*, 3)");

	py::buffer_info triangles_buf = triangles.request();

	if (triangles_buf.ndim != 2)
		throw std::runtime_error("triangles must have dimension 2");

	if (triangles_buf.shape[1] != 3)
		throw std::runtime_error("triangles must have shape (*, 3)");

	py::buffer_info samples_buf = samples.request();

	if (samples_buf.ndim != 2)
		throw std::runtime_error("samples must have dimension 2");

	if (samples_buf.shape[1] != 3)
		throw std::runtime_error("samples must have shape (*, 3)");

	auto samples_data = samples.template unchecked<2>();
	for (long long idx = 0; idx < vertices_buf.shape[0]; idx++) {
		samples_data(idx, 0);
	}

	auto triangles_data = triangles.template unchecked<2>();
	auto vertices_data = vertices.template unchecked<2>();

	// Copy to output
	auto projections = py::array_t<Float>({ static_cast<size_t>(samples_buf.shape[0]), static_cast<size_t>(3) });
	auto bcoords = py::array_t<Float>({ static_cast<size_t>(samples_buf.shape[0]), static_cast<size_t>(3) });
	auto proj_triangles = py::array_t<int>( static_cast<pybind11::ssize_t>(samples_buf.shape[0]) );
	auto projections_data = projections.template mutable_unchecked<2>();
	auto bcoords_data = bcoords.template mutable_unchecked<2>();
	auto proj_triangles_data = proj_triangles.template mutable_unchecked<1>();

	#pragma omp parallel for
	for (long long sample_idx = 0; sample_idx < samples_buf.shape[0]; sample_idx++) {
		Vec3 query_point = Vec3(
			samples_data(sample_idx, 0), samples_data(sample_idx, 1), samples_data(sample_idx, 2)
		);

		auto hit = Hit<Float, Vec3>();
		auto best_hit = Hit<Float, Vec3>();
		Vec3 a, b, c, diff;
		Float err;
		Float min_err = std::numeric_limits<Float>::max();
		long long best_tri = -1;
		for (long long triangle_idx = 0 ; triangle_idx < triangles_buf.shape[0] ; ++triangle_idx) {
			int vert_idx0 = triangles_data(triangle_idx, 0);
			int vert_idx1 = triangles_data(triangle_idx, 1);
			int vert_idx2 = triangles_data(triangle_idx, 2);
			a = Vec3(vertices_data(vert_idx0, 0), vertices_data(vert_idx0, 1), vertices_data(vert_idx0, 2));
			b = Vec3(vertices_data(vert_idx1, 0), vertices_data(vert_idx1, 1), vertices_data(vert_idx1, 2));
			c = Vec3(vertices_data(vert_idx2, 0), vertices_data(vert_idx2, 1), vertices_data(vert_idx2, 2));
			hit = closestPointTriangle<Float,Vec3>(query_point, a, b, c);
			diff = hit.point - query_point;
			err = dot(diff, diff);
			if (err < min_err) {
				min_err = err;
				best_hit = hit;
				best_tri = triangle_idx;
			}
		}
		
		projections_data(sample_idx, 0) = best_hit.point.x;
		projections_data(sample_idx, 1) = best_hit.point.y;
		projections_data(sample_idx, 2) = best_hit.point.z;
		bcoords_data(sample_idx, 0) = best_hit.ba;
		bcoords_data(sample_idx, 1) = best_hit.bb;
		bcoords_data(sample_idx, 2) = best_hit.bc;
		proj_triangles_data(sample_idx) = static_cast<int>(best_tri);
	}


	return std::tuple<py::array_t<Float>,py::array_t<Float>,py::array_t<int>>(projections, bcoords, proj_triangles);
}

PYBIND11_MODULE(Accel, m) {
	m.doc() = "Accel internal module for DagAmendment";
	m.attr("__version__") = version;
	m.def("project", &project<double, glm::dvec3>,
		"Project points onto a mesh",
		py::arg("vertices"),
		py::arg("triangles"),
		py::arg("samples")
		);
}
