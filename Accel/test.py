#!C:\Python37\python.exe
from subprocess import run
import sys
from os.path import join

build_dir = "build-msvc16"
proc = run(["cmake", "--build", build_dir, "--config", "Release"])
if proc.returncode != 0:
	exit(proc.returncode)
sys.path.append(join(build_dir, "Release"))

import DiffParamAccel
import numpy as np

vertices = np.zeros((128, 3), 'f')
triangles = np.zeros((12, 3), 'i')
out_data, foo, bar = DiffParamAccel.pack(vertices, triangles)

print((out_data, foo, bar))
