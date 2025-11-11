# Setup Guide - 540_NAN_COPY Project

Complete setup instructions for the Nandos neural data analysis project.

## Table of Contents
- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Automated Setup](#automated-setup)
- [Manual Setup](#manual-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## Quick Start

**For most users, use the automated setup:**

### Windows
```powershell
.\setup.bat
```

### Unix/macOS
```bash
chmod +x setup.sh
./setup.sh
```

This will automatically create a virtual environment, install dependencies, and verify the installation.

## System Requirements

### Minimum Requirements
- **Python:** 3.8 or later
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 2GB free space
- **OS:** Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)

### Required Software
- Python 3.8+ with pip
- Git (for version control)
- Jupyter (installed via requirements.txt)

### Check Python Version
```bash
python --version
# or
python3 --version
```

Should output: `Python 3.8.0` or higher

## Automated Setup

The automated setup scripts (`setup.sh` and `setup.bat`) perform these steps:

1. **Verify Python installation** - Checks for Python 3.8+
2. **Create virtual environment** - Creates `.venv` directory
3. **Activate environment** - Activates the virtual environment
4. **Upgrade pip** - Updates to latest pip version
5. **Install dependencies** - Installs all packages from requirements.txt
6. **Run tests** - Validates installation with test_setup.py

### Windows Automated Setup

```powershell
# Navigate to project directory
cd C:\path\to\540_NAN_COPY

# Run setup script
.\setup.bat

# Wait for completion (may take 5-10 minutes)
```

### Unix/macOS Automated Setup

```bash
# Navigate to project directory
cd /path/to/540_NAN_COPY

# Make script executable
chmod +x setup.sh

# Run setup script
./setup.sh

# Wait for completion (may take 5-10 minutes)
```

## Manual Setup

If the automated setup fails or you prefer manual control:

### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
```

**Unix/macOS:**
```bash
python3 -m venv .venv
```

### Step 2: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Unix/macOS:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` prefix in your terminal prompt.

### Step 3: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Data processing: pandas, numpy
- Statistics: scipy, statsmodels, pingouin, scikit-posthocs
- Visualization: matplotlib, seaborn, plotly
- ML tools: scikit-learn
- Image/NLP: Pillow, wordcloud, nltk
- Jupyter: jupyter, ipykernel, ipywidgets

### Step 5: Verify Installation

```bash
python test_setup.py
```

All tests should pass with ✓ marks.

## Verification

### Test Package Imports

Open Python in the virtual environment:

```bash
python
```

Then test imports:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
print("✓ All standard packages imported successfully")

# Test neurallib
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'lib'))
from neurallib import clean, plot, stats
print("✓ Neurallib package imported successfully")
```

### Run Validation Script

```bash
python validate_deployment.py
```

Should show all checks passing.

### Test Jupyter

```bash
jupyter notebook
```

Opens Jupyter in your browser. Try opening `analysis/data_preparation.ipynb`.

## Troubleshooting

### Common Issues

#### 1. Python Not Found

**Error:** `python: command not found` or `'python' is not recognized`

**Solution:**
- Install Python from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Restart terminal after installation
- Try `python3` instead of `python` on Unix/macOS

#### 2. Virtual Environment Activation Failed (Windows)

**Error:** `Activate.ps1 cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry activation.

#### 3. pip Install Fails

**Error:** `Could not find a version that satisfies the requirement...`

**Solutions:**
- Update pip: `python -m pip install --upgrade pip`
- Check internet connection
- Try installing packages individually:
  ```bash
  pip install pandas numpy scipy matplotlib
  ```
- If specific package fails, check Python version compatibility

#### 4. Neurallib Import Fails

**Error:** `ModuleNotFoundError: No module named 'neurallib'`

**Solution:**
- Verify `lib/neurallib/` directory exists
- Check that `lib/neurallib/__init__.py` exists
- Ensure analysis scripts have PROJECT_ROOT configuration:
  ```python
  import os, sys
  PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  sys.path.insert(0, os.path.join(PROJECT_ROOT, "lib"))
  ```

#### 5. Jupyter Kernel Not Found

**Error:** `Kernel not found` when opening notebooks

**Solution:**
```bash
# Activate virtual environment first
# Windows: .venv\Scripts\activate
# Unix/macOS: source .venv/bin/activate

# Install kernel
python -m ipykernel install --user --name=540_nan_copy --display-name="Python (540_nan_copy)"

# Select this kernel in Jupyter
```

#### 6. Memory Errors with Large Data Files

**Error:** `MemoryError` when loading data

**Solutions:**
- Close other applications
- Process data in chunks using pandas `chunksize` parameter
- Use data types optimization: `pd.read_csv(..., low_memory=False)`
- Increase system swap/page file

#### 7. Matplotlib Display Issues

**Error:** Plots not displaying or `%matplotlib inline` needed

**Solution:**
- In Jupyter notebooks, add to first cell:
  ```python
  %matplotlib inline
  ```
- For scripts, add:
  ```python
  import matplotlib
  matplotlib.use('Agg')  # Non-interactive backend
  ```

### Package-Specific Issues

#### NLTK Data Download

If wordcloud or NLTK features fail:

```python
import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
```

#### Plotly in Jupyter

If plotly plots don't render:

```bash
pip install "notebook>=5.3" "ipywidgets>=7.5"
jupyter nbextension enable --py widgetsnbextension
```

### Platform-Specific Notes

#### Windows

- Use PowerShell or Command Prompt (not Git Bash for activation)
- Some packages may require [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Long path names may cause issues - keep project close to root (e.g., `C:\Projects\540_NAN_COPY`)

#### macOS

- May need Xcode Command Line Tools: `xcode-select --install`
- Use `python3` instead of `python`
- M1/M2 Macs may need Rosetta for some packages

#### Linux

- May need system packages:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-dev python3-pip python3-venv
  sudo apt-get install build-essential
  ```

## Advanced Configuration

### Custom Python Location

To use a specific Python installation:

```bash
/path/to/specific/python -m venv .venv
```

### Proxy Configuration

If behind a corporate proxy:

```bash
pip install --proxy=http://proxy.example.com:8080 -r requirements.txt
```

### Offline Installation

1. Download packages on a machine with internet:
   ```bash
   pip download -r requirements.txt -d packages/
   ```

2. Transfer `packages/` folder to offline machine

3. Install from local packages:
   ```bash
   pip install --no-index --find-links=packages/ -r requirements.txt
   ```

### Jupyter Remote Access

To access Jupyter from another machine:

```bash
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser
```

Then access via `http://<server-ip>:8888`

### IDE Configuration

#### VS Code
1. Install Python extension
2. Select interpreter: Ctrl+Shift+P → "Python: Select Interpreter"
3. Choose `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Unix)

#### PyCharm
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `.venv/Scripts/python.exe` or `.venv/bin/python`

## Environment Variables

Optional environment variables for configuration:

```bash
# Set data directory (if different from default)
export NEURAL_DATA_DIR=/path/to/data

# Set results output directory
export NEURAL_RESULTS_DIR=/path/to/results

# Python optimization (reduces memory usage)
export PYTHONOPTIMIZE=1
```

## Deactivation

When finished working on the project:

```bash
deactivate
```

This returns you to the system Python environment.

## Updating Dependencies

To update packages to latest versions:

```bash
pip install --upgrade -r requirements.txt
```

To update a specific package:

```bash
pip install --upgrade pandas
```

## Uninstallation

To completely remove the environment:

1. Deactivate: `deactivate`
2. Delete virtual environment:
   - Windows: `rmdir /s .venv`
   - Unix/macOS: `rm -rf .venv`

The project files remain intact.

## Getting Help

If issues persist:

1. Check all paths are correct
2. Verify Python version: `python --version`
3. List installed packages: `pip list`
4. Check for conflicting packages: `pip check`
5. Review error messages carefully
6. Consult package-specific documentation

For project-specific issues, refer to [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md).

---

**Last Updated:** 2025-01-11
