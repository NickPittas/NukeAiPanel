#!/usr/bin/env python3
"""
Nuke AI Panel - Numpy Installation Fix

This script fixes the "Cannot import 'setuptools.build_meta'" error when installing numpy
on newer Python versions like 3.13. It attempts multiple installation methods:

1. First updates setuptools and wheel
2. Tries to install using pre-compiled binaries
3. Falls back to a compatible version if needed

Usage:
    python fix_numpy_installation.py [--version VERSION]
"""

import sys
import subprocess
import argparse
import platform
from typing import Tuple, Optional

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Check if we're running on Windows and adjust color codes if needed
if platform.system() == "Windows":
    # Try to enable ANSI colors on Windows
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        # If that fails, disable colors
        for attr in dir(Colors):
            if not attr.startswith('__'):
                setattr(Colors, attr, '')

def print_header(message: str) -> None:
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")

def print_subheader(message: str) -> None:
    """Print a formatted subheader message."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'-' * 60}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD} {message}{Colors.ENDC}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'-' * 60}{Colors.ENDC}")

def print_status(message: str, success: bool = True, warning: bool = False) -> None:
    """Print a status message with appropriate coloring."""
    if success:
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
    elif warning:
        print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_info(message: str) -> None:
    """Print an informational message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")

def print_tip(message: str) -> None:
    """Print a tip message."""
    print(f"{Colors.YELLOW}💡 {message}{Colors.ENDC}")

def run_command(cmd: list) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def get_python_info() -> dict:
    """Get information about the Python environment."""
    return {
        'executable': sys.executable,
        'version': platform.python_version(),
        'version_info': sys.version_info,
        'platform': platform.platform(),
        'system': platform.system(),
        'architecture': platform.architecture()[0]
    }

def update_setuptools() -> bool:
    """Update setuptools and wheel to the latest versions."""
    print_subheader("Updating setuptools and wheel")
    
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"]
    success, output = run_command(cmd)
    
    if success:
        print_status("setuptools and wheel updated successfully")
        return True
    else:
        print_status("Failed to update setuptools and wheel", success=False)
        print_status(f"Error: {output}", success=False)
        return False

def install_numpy_binary(version: Optional[str] = None) -> bool:
    """Try to install numpy using pre-compiled binary."""
    version_str = f"=={version}" if version else ""
    package = f"numpy{version_str}"
    
    print_subheader(f"Installing {package} using pre-compiled binary")
    
    cmd = [sys.executable, "-m", "pip", "install", "--only-binary=:all:", package]
    success, output = run_command(cmd)
    
    if success:
        print_status(f"{package} installed successfully using pre-compiled binary")
        return True
    else:
        print_status(f"Failed to install {package} using pre-compiled binary", success=False)
        print_status(f"Error: {output}", success=False)
        return False

def install_numpy_source(version: Optional[str] = None) -> bool:
    """Try to install numpy from source."""
    version_str = f"=={version}" if version else ""
    package = f"numpy{version_str}"
    
    print_subheader(f"Installing {package} from source")
    
    cmd = [sys.executable, "-m", "pip", "install", package]
    success, output = run_command(cmd)
    
    if success:
        print_status(f"{package} installed successfully from source")
        return True
    else:
        print_status(f"Failed to install {package} from source", success=False)
        print_status(f"Error: {output}", success=False)
        return False

def install_compatible_numpy() -> bool:
    """Try to install the latest compatible version of numpy."""
    print_subheader("Finding compatible numpy version")
    
    # Try different versions in order of preference
    versions = ["1.26.4", "1.25.2", "1.24.4", "1.23.5"]
    
    for version in versions:
        print_info(f"Trying numpy=={version}...")
        
        # Try binary first
        if install_numpy_binary(version):
            return True
        
        # Then try source
        if install_numpy_source(version):
            return True
    
    print_status("Could not find a compatible numpy version", success=False)
    return False

def verify_numpy_installation() -> bool:
    """Verify that numpy is installed and working."""
    print_subheader("Verifying numpy installation")
    
    try:
        import numpy
        version = numpy.__version__
        print_status(f"numpy is installed (version: {version})")
        print_info("Testing basic numpy functionality...")
        
        # Test basic functionality
        arr = numpy.array([1, 2, 3])
        result = arr.mean()
        print_status(f"numpy test successful: {arr} → mean = {result}")
        return True
    except ImportError:
        print_status("numpy is not installed", success=False)
        return False
    except Exception as e:
        print_status(f"numpy is installed but not working correctly: {e}", success=False)
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Fix numpy installation issues on newer Python versions",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version',
        help='Specific numpy version to install (e.g., 1.24.4)'
    )
    
    args = parser.parse_args()
    
    print_header("NUMPY INSTALLATION FIX")
    
    # Get Python info
    python_info = get_python_info()
    print_info(f"Python executable: {python_info['executable']}")
    print_info(f"Python version: {python_info['version']}")
    print_info(f"Platform: {python_info['platform']}")
    print_info(f"Architecture: {python_info['architecture']}")
    
    # Check if we're on Python 3.13+
    is_py313_plus = python_info['version_info'] >= (3, 13)
    if is_py313_plus:
        print_info("Detected Python 3.13 or newer - special handling required")
    
    # Update setuptools and wheel
    if not update_setuptools():
        print_tip("Continuing despite setuptools update failure...")
    
    # Try installation methods
    success = False
    
    # 1. Try binary installation with specific version if provided
    if args.version:
        success = install_numpy_binary(args.version)
        
        # If binary fails, try source
        if not success:
            success = install_numpy_source(args.version)
    else:
        # 2. Try binary installation of latest version
        success = install_numpy_binary()
        
        # 3. If that fails, try source installation
        if not success:
            success = install_numpy_source()
        
        # 4. If that fails, try compatible versions
        if not success:
            success = install_compatible_numpy()
    
    # Verify installation
    if success:
        verified = verify_numpy_installation()
        if verified:
            print_header("NUMPY INSTALLATION SUCCESSFUL")
            print_info("numpy has been successfully installed and verified.")
            return 0
        else:
            print_header("NUMPY INSTALLATION INCOMPLETE")
            print_info("numpy was installed but verification failed.")
            return 1
    else:
        print_header("NUMPY INSTALLATION FAILED")
        print_info("All installation methods failed.")
        
        # Provide troubleshooting tips
        print_subheader("TROUBLESHOOTING TIPS")
        print_tip("1. Install a C compiler appropriate for your system:")
        print_tip("   - Windows: Install Visual C++ Build Tools")
        print_tip("   - macOS: Install Xcode Command Line Tools")
        print_tip("   - Linux: Install gcc and python-dev packages")
        print_tip("2. Try installing a pre-built wheel manually:")
        print_tip("   - Visit https://pypi.org/project/numpy/#files")
        print_tip("   - Download a compatible wheel for your system")
        print_tip("   - Install with: pip install path/to/wheel.whl")
        print_tip("3. Consider using a different Python version (3.8-3.12)")
        print_tip("4. For Nuke integration, use Nuke's built-in Python")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())