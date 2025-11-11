"""
Deployment validation script for 540_NAN_COPY project.
Comprehensive checks to ensure project is deployment-ready.
"""

import sys
import os
from pathlib import Path
import subprocess


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_check(message, passed, details=""):
    """Print a check result with color coding."""
    symbol = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"{symbol} {message:<50} [{status}]")
    if details:
        print(f"  → {details}")


def check_file_exists(filepath, description):
    """Check if a file exists."""
    full_path = PROJECT_ROOT / filepath
    exists = full_path.exists()
    print_check(description, exists, f"{filepath}" if not exists else "")
    return exists


def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    full_path = PROJECT_ROOT / dirpath
    exists = full_path.is_dir()
    print_check(description, exists, f"{dirpath}/" if not exists else "")
    return exists


def validate_required_files():
    """Check that all required files exist."""
    print_section("Required Files")
    
    required_files = {
        'README.md': 'Main documentation',
        'SETUP.md': 'Setup instructions',
        'DEPLOYMENT.md': 'Deployment guide',
        'requirements.txt': 'Dependencies list',
        'setup.sh': 'Unix setup script',
        'setup.bat': 'Windows setup script',
        'test_setup.py': 'Setup test script',
        'validate_deployment.py': 'Validation script',
        'lib/neurallib/__init__.py': 'Neurallib package init',
        'lib/README.md': 'Library documentation',
        'analysis/assembly.py': 'Assembly script',
        'analysis/data_preparation.ipynb': 'Data preparation notebook',
        'analysis/data_analysis.ipynb': 'Data analysis notebook',
    }
    
    results = []
    for filepath, description in required_files.items():
        results.append(check_file_exists(filepath, description))
    
    return all(results)


def validate_directory_structure():
    """Check that required directories exist."""
    print_section("Directory Structure")
    
    required_dirs = {
        'data': 'Data directory',
        'data/infiles': 'Input files directory',
        'analysis': 'Analysis scripts directory',
        'results': 'Results output directory',
        'lib': 'Libraries directory',
        'lib/neurallib': 'Neurallib package directory',
    }
    
    results = []
    for dirpath, description in required_dirs.items():
        results.append(check_directory_exists(dirpath, description))
    
    return all(results)


def validate_neurallib_modules():
    """Check that all neurallib modules exist."""
    print_section("Neurallib Modules")
    
    modules = [
        'clean.py',
        'extract.py',
        'plot.py',
        'stats.py',
        'imotionstools.py',
        'tobiitools.py',
        'batch.py',
        'signal_processing.py',
        'project_management.py',
    ]
    
    results = []
    for module in modules:
        filepath = f'lib/neurallib/{module}'
        results.append(check_file_exists(filepath, f'Module: {module}'))
    
    return all(results)


def validate_imports():
    """Check that key packages can be imported."""
    print_section("Package Imports")
    
    packages = [
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'seaborn',
        'sklearn',
        'statsmodels',
        'pingouin',
        'plotly',
    ]
    
    results = []
    for package in packages:
        try:
            __import__(package)
            print_check(f"Import {package}", True)
            results.append(True)
        except ImportError as e:
            print_check(f"Import {package}", False, str(e))
            results.append(False)
    
    return all(results)


def validate_neurallib_import():
    """Check that neurallib can be imported."""
    print_section("Neurallib Import")
    
    # Add lib to path
    lib_path = PROJECT_ROOT / "lib"
    if str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))
    
    modules = [
        'neurallib',
        'neurallib.clean',
        'neurallib.plot',
        'neurallib.stats',
    ]
    
    results = []
    for module in modules:
        try:
            __import__(module)
            print_check(f"Import {module}", True)
            results.append(True)
        except Exception as e:
            print_check(f"Import {module}", False, str(e))
            results.append(False)
    
    return all(results)


def validate_script_config():
    """Check that scripts have proper path configuration."""
    print_section("Script Configuration")
    
    script_path = PROJECT_ROOT / 'analysis' / 'assembly.py'
    
    if not script_path.exists():
        print_check("assembly.py exists", False)
        return False
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'PROJECT_ROOT definition': 'PROJECT_ROOT' in content,
        'sys.path configuration': 'sys.path.insert' in content and 'lib' in content,
        'neurallib import': 'from neurallib' in content or 'import neurallib' in content,
    }
    
    results = []
    for check_name, passed in checks.items():
        print_check(f"assembly.py: {check_name}", passed)
        results.append(passed)
    
    return all(results)


def validate_notebook_config():
    """Check that notebooks have proper path configuration."""
    print_section("Notebook Configuration")
    
    notebook_path = PROJECT_ROOT / 'analysis' / 'data_preparation.ipynb'
    
    if not notebook_path.exists():
        print_check("data_preparation.ipynb exists", False)
        return False
    
    with open(notebook_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'PROJECT_ROOT definition': 'PROJECT_ROOT' in content,
        'sys.path configuration': 'sys.path.insert' in content,
        'neurallib import': 'neurallib' in content,
    }
    
    results = []
    for check_name, passed in checks.items():
        print_check(f"data_preparation.ipynb: {check_name}", passed)
        results.append(passed)
    
    return all(results)


def validate_data_files():
    """Check for representative data files."""
    print_section("Data Files")
    
    data_dirs = [
        'data/infiles/Sensors',
        'data/infiles/Keys',
        'data/infiles/ET',
        'data/infiles/GSR',
    ]
    
    results = []
    for data_dir in data_dirs:
        dir_path = PROJECT_ROOT / data_dir
        if dir_path.exists():
            files = list(dir_path.glob('*.*'))
            has_files = len(files) > 0
            count = len(files) if has_files else 0
            print_check(f"{data_dir} has files", has_files, 
                       f"{count} files found" if has_files else "Directory empty")
            results.append(has_files)
        else:
            print_check(f"{data_dir} exists", False)
            results.append(False)
    
    # At least some data dirs should have files
    return any(results)


def validate_gitignore():
    """Check that .gitignore exists and excludes key patterns."""
    print_section("Git Configuration")
    
    gitignore_path = PROJECT_ROOT / '.gitignore'
    
    if not gitignore_path.exists():
        print_check(".gitignore exists", False, "Create .gitignore file")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_patterns = {
        '.venv': 'Virtual environment',
        '__pycache__': 'Python cache',
        '*.pyc': 'Compiled Python',
        '.ipynb_checkpoints': 'Jupyter checkpoints',
        'results/': 'Results directory (optional)',
    }
    
    results = []
    for pattern, description in required_patterns.items():
        present = pattern in content
        # Results directory is optional to exclude
        if pattern == 'results/':
            print_check(f"Excludes {description}", present, 
                       "Optional - results may be tracked")
            continue
        print_check(f"Excludes {description}", present,
                   f"Add '{pattern}' to .gitignore" if not present else "")
        results.append(present)
    
    return all(results)


def validate_git_status():
    """Check git repository status."""
    print_section("Repository Status")
    
    try:
        # Check if git is available
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode != 0:
            print_check("Git available", False, "Git not installed")
            return False
        
        print_check("Git available", True)
        
        # Check if this is a git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode != 0:
            print_check("Git repository", False, "Not a git repository")
            return False
        
        print_check("Git repository", True)
        
        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        has_changes = len(result.stdout.strip()) > 0
        print_check("Working directory clean", not has_changes,
                   f"{Colors.YELLOW}Uncommitted changes present{Colors.RESET}" if has_changes else "")
        
        return True
        
    except FileNotFoundError:
        print_check("Git available", False, "Git not installed")
        return False


def validate_requirements_file():
    """Check requirements.txt content."""
    print_section("Requirements File")
    
    req_path = PROJECT_ROOT / 'requirements.txt'
    
    if not req_path.exists():
        print_check("requirements.txt exists", False)
        return False
    
    with open(req_path, 'r') as f:
        content = f.read()
    
    required_packages = [
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'seaborn',
        'plotly',
        'scikit-learn',
        'statsmodels',
        'pingouin',
        'jupyter',
    ]
    
    results = []
    for package in required_packages:
        present = package.lower() in content.lower()
        print_check(f"Lists {package}", present)
        results.append(present)
    
    return all(results)


def generate_summary(results):
    """Generate and print summary of all checks."""
    print_section("Summary")
    
    total_checks = len(results)
    passed_checks = sum(results.values())
    failed_checks = total_checks - passed_checks
    
    pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"Total Checks:  {total_checks}")
    print(f"{Colors.GREEN}Passed:       {passed_checks}{Colors.RESET}")
    if failed_checks > 0:
        print(f"{Colors.RED}Failed:       {failed_checks}{Colors.RESET}")
    else:
        print(f"Failed:       {failed_checks}")
    print(f"Pass Rate:     {pass_rate:.1f}%")
    print()
    
    if pass_rate == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All validation checks passed!{Colors.RESET}")
        print(f"{Colors.GREEN}Project is deployment-ready.{Colors.RESET}")
        return 0
    elif pass_rate >= 80:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Most validation checks passed{Colors.RESET}")
        print(f"{Colors.YELLOW}Review failed checks above. Project may be usable with limitations.{Colors.RESET}")
        return 1
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Multiple validation checks failed{Colors.RESET}")
        print(f"{Colors.RED}Project is not deployment-ready. Address issues above.{Colors.RESET}")
        return 1


def main():
    """Run all validation checks."""
    print(f"\n{Colors.BOLD}540_NAN_COPY Deployment Validation{Colors.RESET}")
    print(f"Project Root: {PROJECT_ROOT}")
    
    results = {
        'Required Files': validate_required_files(),
        'Directory Structure': validate_directory_structure(),
        'Neurallib Modules': validate_neurallib_modules(),
        'Package Imports': validate_imports(),
        'Neurallib Import': validate_neurallib_import(),
        'Script Configuration': validate_script_config(),
        'Notebook Configuration': validate_notebook_config(),
        'Data Files': validate_data_files(),
        'Git Configuration': validate_gitignore(),
        'Git Status': validate_git_status(),
        'Requirements File': validate_requirements_file(),
    }
    
    return generate_summary(results)


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).parent.absolute()
    exit_code = main()
    sys.exit(exit_code)
