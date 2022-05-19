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

import sys
import os
from os.path import join as P
import shutil
from subprocess import run

#------------------------------------------------------------
# Config

addon_list = [
	"DagAmendment",
	"BMeshInsights",
	"DepsgraphNodes",
]

#------------------------------------------------------------
# Main

def main():
	with cd(this_scripts_directory()):
		accel_build_dir = f"Accel/build-{sys.platform}"
		ensure_dir("releases")
		ensure_dir(accel_build_dir)

		python310_exe = find_python310()

		with cd(accel_build_dir):
			run(["cmake", "..", f"-DPYTHON_EXECUTABLE={python310_exe}", f"-DCMAKE_BUILD_TYPE=Release"])
			run(["cmake", "--build", ".", "--config", "Release"])
			run(["cmake", "--install", "."])

		addon = "DagAmendment"
		version = get_addon_version(addon)
		zip(addon, P("releases", f"{addon}-v{version}"))

		print(f"Done! You may install in Blender the addon releases/{addon}-v{version}.zip.")

#------------------------------------------------------------
# Utils

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, directory):
        self.directory = os.path.expanduser(directory)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.directory)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def ensure_dir(directory):
	os.makedirs(directory, exist_ok=True)

def zip(directory, zipfile):
	"""compresses a directory into a zip file"""
	print(f"Zipping {directory} into {zipfile}...")
	directory = os.path.realpath(directory)
	parent = os.path.dirname(directory)
	base = os.path.basename(directory)
	shutil.make_archive(zipfile, 'zip', parent, base)

def get_addon_version(addon_directory):
	"""Extract the version of the addon from its init file"""
	with open(P(addon_directory, "__init__.py"), 'r') as f:
		text = f.read()
	bl_info = eval(text[text.find("{"):text.find("}")+1])
	return "{}.{}.{}".format(*bl_info["version"])

def this_scripts_directory():
	return os.path.dirname(os.path.realpath(__file__))

def find_python310():
	path_sep = ";" if sys.platform == "win32" else ":"
	python_exe = "python.exe" if sys.platform == "win32" else "python"
	python3_exe = "python3.exe" if sys.platform == "win32" else "python3"
	path = os.environ["PATH"].split(path_sep)
	for p in path:
		try:
			files = os.listdir(p)
		except FileNotFoundError:
			continue
		full_python_exe = None
		if python_exe in files:
			full_python_exe = os.path.join(p, python_exe)
		if python3_exe in files:
			full_python_exe = os.path.join(p, python3_exe)
		if full_python_exe is not None:
			ret = run([full_python_exe, "--version"], capture_output=True)
			if ret.stdout.startswith(b"Python 3.10"):
				return full_python_exe
	print("Could not find Python 3.10 in your PATH!")
	exit(1)

#------------------------------------------------------------

main()
