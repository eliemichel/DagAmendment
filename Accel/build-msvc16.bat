:: Place all build related files in a specific directory.
:: Whenever you'd like to clean the build and restart it from scratch, you can
:: delete this directory without worrying about deleting important files.
mkdir build-msvc16
cd build-msvc16

:: Call cmake to generate the all configured Visual Studio solution
cmake .. ^
	-G "Visual Studio 16 2019" -A x64 ^
	-DPYTHON_EXECUTABLE=C:\Python37\python.exe ^
	-Dembree_DIR="C:\Program Files\Intel\Embree3"

@echo off
:: Check that it run all right
if errorlevel 1 (
	echo [91mUnsuccessful[0m
) else (
	echo [92mSuccessful[0m
)
pause
