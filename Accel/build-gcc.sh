#!/bin/bash

# Place all build related files in a specific directory.
# Whenever you'd like to clean the build and restart it from scratch, you can
# delete this directory without worrying about deleting important files.
mkdir build-gcc
cd build-gcc

# Call cmake to generate the Makefile. You can then build with 'make' and
# install with 'make install'
cmake .. -DCMAKE_BUILD_TYPE=Release

# Check that it run all right
if [ $? -eq 0 ]
then
	echo [92mSuccessful[0m
else
	echo [91mUnsuccessful[0m
fi
