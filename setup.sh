#!/bin/bash
# Setup script for 540_NAN_COPY project (Unix/macOS)
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "=================================================="
echo "540_NAN_COPY Project Setup"
echo "=================================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or later"
    exit 1
fi

# Display Python version
PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Run smoke tests
echo "Running setup validation tests..."
python test_setup.py
RESULT=$?

echo ""
if [ $RESULT -eq 0 ]; then
    echo "=================================================="
    echo "✓ Setup completed successfully!"
    echo "=================================================="
    echo ""
    echo "To activate the environment:"
    echo "  source .venv/bin/activate"
    echo ""
    echo "To deactivate when done:"
    echo "  deactivate"
    echo ""
else
    echo "=================================================="
    echo "⚠ Setup completed with warnings"
    echo "=================================================="
    echo "Please review the test output above"
    echo ""
fi
