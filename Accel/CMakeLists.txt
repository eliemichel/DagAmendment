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

cmake_minimum_required(VERSION 3.10)
project(Accel)

set (CMAKE_CXX_STANDARD 17)

add_subdirectory(pybind11)

pybind11_add_module(Accel
	Accel.cpp
)

set(DAG_AMENDMENT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/..")

target_include_directories(Accel PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(Accel PUBLIC TASKING_INTERNAL)
target_compile_definitions(Accel PUBLIC TASKING_INTERNAL)

find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    target_link_libraries(Accel PUBLIC OpenMP::OpenMP_CXX)
endif()

# Treat warnings as errors
if(MSVC)
  target_compile_options(Accel PRIVATE /W4 /WX)
else()
  target_compile_options(Accel PRIVATE -Wall -Wextra -pedantic -Werror -Wno-deprecated-declarations)
endif()

install(TARGETS Accel DESTINATION "${DAG_AMENDMENT_ROOT}/DagAmendment")
