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

# -------------------------------------------------------------------

# Utility functions to load registries from subdirectories like we do
# for Reducers and eventually for Solvers.

# -------------------------------------------------------------------

def get_modules(module_dirname):
    import os
    from os.path import join, dirname, realpath, isfile
    import importlib

    module_names = []
    module_dir = join(dirname(realpath(__file__)), module_dirname)
    for f in os.listdir(module_dir):
        if f.endswith(".py") and isfile(join(module_dir, f)):
            module_names.append(f[:-3])

    return [
        importlib.import_module(f".{module_dirname}.{name}", package=__package__)
        for name in module_names
    ]

# -------------------------------------------------------------------

def load_registry(module_dirname, cls):
    """Recurse in the module directory to build the registry"""
    registry = {}
    for module in get_modules(module_dirname):
        # Find variables of type AbstractReducer in the module and register them in registry
        for identifier in dir(module):
            if identifier == cls.__name__ or identifier.startswith("Abstract"):
                continue
            member = getattr(module, identifier)
            if isinstance(member, type) and issubclass(member, cls):
                registry[identifier] = member

    return registry

# -------------------------------------------------------------------

def consolidate_register_functions(module_dirname):
    """Recurse in the module directory to gather register and unregister functions"""
    register_fonctions = []
    unregister_fonctions = []
    for module in get_modules(module_dirname):
        if hasattr(module, 'register'):
            register_fonctions.append(getattr(module, 'register'))
        if hasattr(module, 'unregister'):
            unregister_fonctions.append(getattr(module, 'unregister'))
    def register():
        for f in register_fonctions:
            f()
    def unregister():
        for f in unregister_fonctions[::-1]:
            f()
    return register, unregister
