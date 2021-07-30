import bpy
from subprocess import run
import sys
from os.path import join
import ctypes
import numpy as np
from numpy.linalg import norm

import time
from collections import defaultdict
from math import sqrt

np.random.seed = 3615

# -------------------------------------------------------------------

class Timer():
    def __init__(self):
        self.start = time.perf_counter()

    def ellapsed(self):
        return time.perf_counter() - self.start

# -------------------------------------------------------------------

class ProfilingCounter:
    def __init__(self):
        self.reset()

    def average(self):
        if self.sample_count == 0:
            return 0
        else:
            return self.accumulated / self.sample_count

    def stddev(self):
        if self.sample_count == 0:
            return 0
        else:
            avg = self.average()
            var = self.accumulated_sq / self.sample_count - avg * avg
            return sqrt(max(0, var))

    def add_sample(self, value):
        if type(value) == Timer:
            value = value.ellapsed()
        self.sample_count += 1
        self.accumulated += value
        self.accumulated_sq += value * value

    def reset(self):
        self.sample_count = 0
        self.accumulated = 0.0
        self.accumulated_sq = 0.0

    def summary(self):
        """returns something like XXms (±Xms, X samples)"""
        return (
            f"{self.average()*1000.:.03}ms " +
            f"(±{self.stddev()*1000.:.03}ms, " +
            f"{self.sample_count} samples)"
        )

# -------------------------------------------------------------------

class ProfilingCounterPool:
    def __init__(self):
        self.counters = defaultdict(ProfilingCounter)

    def __getitem__(self, key):
        return self.counters[key]

    def reset(self):
        for c in self.counters.values():
            c.reset()

    def summary(self):
        keys = list(self.counters.keys())
        keys.sort()
        s = [f" - {k}: {self.counters[k].summary()}" for k in keys]
        return "\n".join(s)

# -------------------------------------------------------------------

def matvecmul(M, v):
    return np.squeeze(np.matmul(M, v[:,:,np.newaxis]), axis=-1)

def get_vertex_positions_as_np(mesh):
    data = np.empty((len(mesh.vertices), 3), 'f')
    mesh.vertices.foreach_get('co', data.ravel())
    return data

def get_triangle_corners_as_np(mesh):
    mesh.calc_loop_triangles()
    data = np.empty((len(mesh.loop_triangles), 3), 'i')
    mesh.loop_triangles.foreach_get('vertices', data.ravel())
    return data

def main():
    profiling = ProfilingCounterPool()
    build_dir = r"C:\Elie\src\DiffParamBlender\Accel\build-msvc16"
    proc = run(["cmake", "--build", build_dir, "--config", "Release"])
    if proc.returncode != 0:
        return
    sys.path.append(join(build_dir, "Release"))

    import DiffParamAccel

    sample_count_per_face = 1

    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    me = bpy.context.active_object.data.evaluated_get(depsgraph)
    vertices = get_vertex_positions_as_np(me)
    triangles = get_triangle_corners_as_np(me)
    print(f"active_object.name = {bpy.context.active_object.name}")
    print(f"vertices.shape = {vertices.shape}")
    print(f"samples.shape = ({len(triangles) * sample_count_per_face},3)")

    for jitter_amount in np.linspace(0.0, 1.0, num=20):
        # Random samples
        triangle_indices = list(range(len(triangles))) * sample_count_per_face
        sample_corners = vertices[triangles[triangle_indices]]
        bcoords = np.random.random((len(triangle_indices), 3))
        bcoords /= bcoords.sum(axis=1, keepdims=True)
        samples = matvecmul(sample_corners.transpose(0,2,1), bcoords)

        jitter = np.random.random(samples.shape) * jitter_amount
        jittered_samples = samples + jitter
        
        timer = Timer()
        projections, bcoords, proj_triangles = DiffParamAccel.project(vertices, triangles, samples)
        profiling["project"].add_sample(timer)

        norms = norm(projections - samples, axis=1)
        test1 = norms < jitter_amount + 1e-6
        if not test1.all():
            failing = np.invert(test1)
            print()
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("Test 1 failed:")
            print(f" - jitter_amount = {jitter_amount}")
            print(f" - success = {test1}")
            print(f" - failing norms = {norms[failing]}")
            print(f" - failing samples = {samples[failing]}")
            print(f" - failing projections = {projections[failing]}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print()
            assert(False)

        reconstructed = matvecmul(vertices[triangles[proj_triangles]].transpose(0,2,1), bcoords)
        norms = reconstructed - projections
        test2 = norms < jitter_amount + 1e-6
        if not test2.all():
            failing = np.invert(test2)
            print()
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("Test 2 failed:")
            print(f" - jitter_amount = {jitter_amount}")
            print(f" - success = {test2}")
            print(f" - failing norms = {norms[failing]}")
            print(f" - failing reconstructed = {reconstructed[failing]}")
            print(f" - failing projections = {projections[failing]}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print()
            assert(False)

    print()
    print("------------------------------")
    print("Profiling:")
    print(profiling.summary())
    print("------------------------------")
    print()

main()
