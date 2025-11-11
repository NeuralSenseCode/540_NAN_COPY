"""
Setup validation script for 540_NAN_COPY project.
Tests that all dependencies are installed and the project structure is correct.
"""

import sys
import os
from pathlib import Path


def test_python_version():
    """Verify Python version is 3.8 or later."""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} (requires 3.8+)")
        return False


def test_imports():
    """Test that all required packages can be imported."""
    print("\nChecking package imports:")
    
    packages = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('scipy', None),
        ('sklearn', None),
        ('statsmodels', None),
        ('pingouin', 'pg'),
        ('scikit_posthocs', 'sp'),
        ('matplotlib', None),
        ('matplotlib.pyplot', 'plt'),
        ('seaborn', 'sns'),
        ('plotly', None),
        ('PIL', None),
        ('wordcloud', None),
        ('nltk', None),
    ]
    
    failed = []
    for package_info in packages:
        if isinstance(package_info, tuple):
            package, alias = package_info
        else:
            package, alias = package_info, None
            
        try:
            if alias:
                exec(f"import {package} as {alias}")
            else:
                exec(f"import {package}")
            print(f"  ✓ {package}")
        except ImportError as e:
            print(f"  ✗ {package} - {e}")
            failed.append(package)
    
    return len(failed) == 0, failed


def test_neurallib():
    """Test that neurallib package can be imported."""
    print("\nChecking neurallib package:")
    
    # Add lib to path if not already there
    project_root = Path(__file__).parent.absolute()
    lib_path = project_root / "lib"
    if str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))
    
    modules = [
        'neurallib',
        'neurallib.clean',
        'neurallib.extract',
        'neurallib.plot',
        'neurallib.stats',
        'neurallib.imotionstools',
        'neurallib.tobiitools',
        'neurallib.batch',
        'neurallib.signal_processing',
        'neurallib.project_management',
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module} - {e}")
            failed.append(module)
    
    return len(failed) == 0, failed


def test_directory_structure():
    """Verify required directories exist."""
    print("\nChecking directory structure:")
    
    project_root = Path(__file__).parent.absolute()
    required_dirs = [
        'data',
        'data/infiles',
        'analysis',
        'results',
        'lib',
        'lib/neurallib',
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ (missing)")
            missing.append(dir_path)
    
    return len(missing) == 0, missing


def test_key_files():
    """Verify key project files exist."""
    print("\nChecking key files:")
    
    project_root = Path(__file__).parent.absolute()
    required_files = [
        'requirements.txt',
        'setup.sh',
        'setup.bat',
        'lib/neurallib/__init__.py',
        'analysis/assembly.py',
        'analysis/data_preparation.ipynb',
        'analysis/data_analysis.ipynb',
    ]
    
    missing = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (missing)")
            missing.append(file_path)
    
    return len(missing) == 0, missing


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("540_NAN_COPY Setup Validation")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Python Version", test_python_version()))
    
    imports_ok, failed_imports = test_imports()
    results.append(("Package Imports", imports_ok))
    
    neurallib_ok, failed_neurallib = test_neurallib()
    results.append(("Neurallib Package", neurallib_ok))
    
    dirs_ok, missing_dirs = test_directory_structure()
    results.append(("Directory Structure", dirs_ok))
    
    files_ok, missing_files = test_key_files()
    results.append(("Key Files", files_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All tests passed! Project is ready to use.")
        return 0
    else:
        print("✗ Some tests failed. Please review the output above.")
        print()
        if failed_imports:
            print("Missing packages:", ", ".join(failed_imports))
            print("Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
