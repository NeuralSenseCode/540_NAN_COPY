@echo off
REM Setup script for 540_NAN_COPY project (Windows)
REM This script creates a virtual environment and installs all dependencies

echo ==================================================
echo 540_NAN_COPY Project Setup
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

REM Display Python version
echo Found:
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip
)
echo pip upgraded
echo.

REM Install requirements
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed
echo.

REM Run smoke tests
echo Running setup validation tests...
python test_setup.py
set TEST_RESULT=%errorlevel%

echo.
if %TEST_RESULT%==0 (
    echo ==================================================
    echo Setup completed successfully!
    echo ==================================================
    echo.
    echo To activate the environment:
    echo   .venv\Scripts\activate
    echo.
    echo To deactivate when done:
    echo   deactivate
    echo.
) else (
    echo ==================================================
    echo Setup completed with warnings
    echo ==================================================
    echo Please review the test output above
    echo.
)

pause
