#!/usr/bin/env python3
"""
Nuke AI Panel - Comprehensive Dependency Installer

This script installs all required dependencies for the Nuke AI Panel,
including all AI providers (OpenAI, Anthropic, Mistral, Google, Ollama, OpenRouter).

Features:
- Works in both Nuke's Python environment and standalone Python
- Provides clear progress indicators and status messages
- Handles Nuke-specific environment constraints
- Includes provider-specific setup guidance
- Comprehensive error handling and troubleshooting

Usage:
    python install_all_dependencies.py [--check-only] [--skip-optional]
"""

import sys
import subprocess
import os
import platform
import importlib
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

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

# Provider dependencies configuration
PROVIDER_DEPENDENCIES = {
    'core': {
        'packages': [
            'aiohttp==3.9.1',
            'asyncio-throttle==1.0.2',
            'cryptography==41.0.7',
            'pydantic==2.5.2',
            'pyyaml==6.0.1',
            'python-dotenv==1.0.0',
            'tenacity==8.2.3',
            'cachetools==5.3.2',
            'colorlog==6.8.0',
            'aiofiles==23.2.1',
            'httpx==0.25.2'
        ],
        'description': 'Core dependencies required for all providers',
        'required': True
    },
    'openai': {
        'packages': ['openai==1.6.1'],
        'description': 'OpenAI GPT models (GPT-4, GPT-3.5-turbo, etc.)',
        'api_key_env': 'OPENAI_API_KEY',
        'api_key_instructions': 'Get your API key from https://platform.openai.com/api-keys',
        'required': True
    },
    'anthropic': {
        'packages': ['anthropic==0.8.1'],
        'description': 'Anthropic Claude models (Claude-3 Opus, Sonnet, Haiku)',
        'api_key_env': 'ANTHROPIC_API_KEY',
        'api_key_instructions': 'Get your API key from https://console.anthropic.com/settings/keys',
        'required': True
    },
    'google': {
        'packages': ['google-generativeai==0.3.2'],
        'description': 'Google Gemini models',
        'api_key_env': 'GOOGLE_API_KEY',
        'api_key_instructions': 'Get your API key from https://makersuite.google.com/app/apikey',
        'required': True
    },
    'mistral': {
        'packages': ['mistralai==0.1.2'],
        'description': 'Mistral AI models',
        'api_key_env': 'MISTRAL_API_KEY',
        'api_key_instructions': 'Get your API key from https://console.mistral.ai/api-keys/',
        'required': True
    },
    'ollama': {
        'packages': ['ollama==0.1.7'],
        'description': 'Ollama local AI models',
        'setup_instructions': 'Download and install Ollama from https://ollama.ai/download',
        'required': True
    },
    'openrouter': {
        'packages': [],  # Uses OpenAI-compatible API
        'description': 'OpenRouter API (access to multiple AI models)',
        'api_key_env': 'OPENROUTER_API_KEY',
        'api_key_instructions': 'Get your API key from https://openrouter.ai/keys',
        'required': True
    }
}

# Optional dependencies
OPTIONAL_DEPENDENCIES = {
    'ui': {
        'packages': ['PySide6==6.6.1'],
        'description': 'UI dependencies for standalone mode (not needed in Nuke)',
        'required': False
    },
    'data_processing': {
        'packages': ['numpy==1.24.4', 'pandas==2.1.4'],
        'description': 'Data processing libraries for advanced features (requires C compiler)',
        'required': False,
        'compiler_required': True
    },
    'logging': {
        'packages': ['structlog==23.2.0', 'rich==13.7.0'],
        'description': 'Enhanced logging capabilities',
        'required': False
    }
}

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

def check_nuke_environment() -> bool:
    """Check if we're running in a Nuke environment."""
    try:
        import nuke
        return True
    except ImportError:
        return False

def get_python_info() -> Dict[str, str]:
    """Get information about the Python environment."""
    return {
        'executable': sys.executable,
        'version': platform.python_version(),
        'platform': platform.platform(),
        'system': platform.system(),
        'in_nuke': check_nuke_environment()
    }

def test_import(module_name: str) -> bool:
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name.split('==')[0].replace('-', '_'))
        return True
    except ImportError:
        return False
    except Exception:
        return False

def install_package(package: str, python_exe: str = None, upgrade: bool = False) -> Tuple[bool, str]:
    """
    Install a package using pip.
    
    Args:
        package: Package name (with optional version)
        python_exe: Python executable to use
        upgrade: Whether to upgrade the package
        
    Returns:
        Tuple of (success, output)
    """
    if python_exe is None:
        python_exe = sys.executable
    
    # Build the pip command
    pip_cmd = [python_exe, '-m', 'pip', 'install']
    
    if upgrade:
        pip_cmd.append('--upgrade')
    
    pip_cmd.append(package)
    
    try:
        # Run the pip command
        result = subprocess.run(
            pip_cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise an exception on non-zero exit
        )
        
        # Check if the installation was successful
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def check_package_status(package: str) -> Dict[str, Any]:
    """
    Check the installation status of a package.
    
    Args:
        package: Package name (with optional version)
        
    Returns:
        Dictionary with status information
    """
    # Extract the package name without version
    package_name = package.split('==')[0].replace('-', '_')
    
    status = {
        'package': package,
        'name': package_name,
        'installed': False,
        'version': None,
        'import_error': None
    }
    
    try:
        # Try to import the module
        module = importlib.import_module(package_name)
        status['installed'] = True
        
        # Try to get the version
        try:
            version = getattr(module, '__version__', None)
            if version:
                status['version'] = version
        except:
            pass
            
    except ImportError as e:
        status['import_error'] = str(e)
    except Exception as e:
        status['import_error'] = str(e)
    
    return status

def install_dependency_group(group_name: str, config: Dict[str, Any], upgrade: bool = False) -> Dict[str, Any]:
    """
    Install a group of dependencies.
    
    Args:
        group_name: Name of the dependency group
        config: Configuration for the dependency group
        upgrade: Whether to upgrade packages
        
    Returns:
        Dictionary with installation results
    """
    print_subheader(f"Installing {group_name.upper()} dependencies")
    print_info(config['description'])
    
    # Check if this group requires a compiler
    if config.get('compiler_required', False):
        print_tip("This dependency group requires a C compiler for installation.")
        print_tip("If installation fails, you may need to install a compiler or use pre-built wheels.")
    
    results = {
        'group': group_name,
        'description': config['description'],
        'packages': [],
        'success_count': 0,
        'total_count': len(config['packages']),
        'success': False
    }
    
    # Install each package in the group
    for package in config['packages']:
        print(f"\nInstalling {package}...")
        
        # Check if already installed
        status = check_package_status(package)
        if status['installed'] and not upgrade:
            print_status(f"{package} is already installed (version: {status['version'] or 'unknown'})")
            results['packages'].append({
                'package': package,
                'success': True,
                'already_installed': True,
                'output': f"Already installed (version: {status['version'] or 'unknown'})"
            })
            results['success_count'] += 1
            continue
        
        # For packages that might need compilation, try to use wheels first
        if config.get('compiler_required', False):
            try:
                # Try to install with --only-binary option first
                print_info(f"Attempting to install {package} using pre-built wheel...")
                wheel_success, wheel_output = install_package(f"--only-binary=:all: {package}", upgrade=upgrade)
                
                if wheel_success:
                    print_status(f"{package} installed successfully using pre-built wheel")
                    results['packages'].append({
                        'package': package,
                        'success': True,
                        'output': wheel_output
                    })
                    results['success_count'] += 1
                    continue
                else:
                    print_status(f"Could not find pre-built wheel for {package}, trying source installation...", warning=True)
            except Exception as e:
                print_status(f"Error trying wheel installation: {e}", warning=True)
        
        # Standard installation
        success, output = install_package(package, upgrade=upgrade)
        
        if success:
            print_status(f"{package} installed successfully")
            results['packages'].append({
                'package': package,
                'success': True,
                'output': output
            })
            results['success_count'] += 1
        else:
            print_status(f"Failed to install {package}", success=False)
            print_status(f"Error: {output}", success=False)
            
            # Provide specific guidance for compiler-required packages
            if config.get('compiler_required', False):
                print_tip(f"This package requires a C compiler. Install Visual C++ Build Tools on Windows")
                print_tip(f"or gcc/clang on Linux/macOS to build from source.")
                print_tip(f"Alternatively, you can install a pre-built version manually.")
            
            results['packages'].append({
                'package': package,
                'success': False,
                'output': output
            })
    
    # Check if all packages were installed successfully
    results['success'] = results['success_count'] == results['total_count']
    
    # Print summary
    if results['success']:
        print_status(f"\nAll {group_name.upper()} dependencies installed successfully ({results['success_count']}/{results['total_count']})")
    else:
        print_status(f"\nSome {group_name.upper()} dependencies failed to install ({results['success_count']}/{results['total_count']})", success=False)
    
    return results

def print_provider_setup_instructions(provider: str, config: Dict[str, Any]) -> None:
    """Print setup instructions for a provider."""
    print_subheader(f"Setup Instructions for {provider.upper()}")
    
    if 'api_key_env' in config:
        print_info(f"API Key Environment Variable: {config['api_key_env']}")
        print_info(f"Instructions: {config.get('api_key_instructions', 'No specific instructions provided.')}")
        print_tip(f"Set this in your environment or in a .env file in your project directory.")
    
    if 'setup_instructions' in config:
        print_info(f"Setup: {config['setup_instructions']}")
    
    print()  # Add a blank line for spacing

def verify_installations() -> Dict[str, Any]:
    """
    Verify all installations and return a status report.
    
    Returns:
        Dictionary with verification results
    """
    print_header("VERIFYING INSTALLATIONS")
    
    results = {
        'providers': {},
        'optional': {},
        'core': {},
        'success_count': 0,
        'total_count': 0
    }
    
    # Verify core dependencies
    print_subheader("Verifying Core Dependencies")
    core_success = True
    core_results = []
    
    for package in PROVIDER_DEPENDENCIES['core']['packages']:
        package_name = package.split('==')[0]
        status = check_package_status(package_name)
        
        if status['installed']:
            print_status(f"{package_name} is installed (version: {status['version'] or 'unknown'})")
            core_results.append({
                'package': package_name,
                'installed': True,
                'version': status['version']
            })
        else:
            print_status(f"{package_name} is not installed", success=False)
            core_results.append({
                'package': package_name,
                'installed': False,
                'error': status['import_error']
            })
            core_success = False
    
    results['core'] = {
        'success': core_success,
        'packages': core_results
    }
    
    if core_success:
        results['success_count'] += 1
    results['total_count'] += 1
    
    # Verify provider dependencies
    print_subheader("Verifying Provider Dependencies")
    
    for provider, config in PROVIDER_DEPENDENCIES.items():
        if provider == 'core':
            continue
            
        provider_success = True
        provider_results = []
        
        print(f"\n{provider.upper()}:")
        for package in config['packages']:
            if not package:
                continue
                
            package_name = package.split('==')[0]
            status = check_package_status(package_name)
            
            if status['installed']:
                print_status(f"{package_name} is installed (version: {status['version'] or 'unknown'})")
                provider_results.append({
                    'package': package_name,
                    'installed': True,
                    'version': status['version']
                })
            else:
                print_status(f"{package_name} is not installed", success=False)
                provider_results.append({
                    'package': package_name,
                    'installed': False,
                    'error': status['import_error']
                })
                provider_success = False
        
        results['providers'][provider] = {
            'success': provider_success,
            'packages': provider_results
        }
        
        if provider_success:
            results['success_count'] += 1
        results['total_count'] += 1
    
    # Verify optional dependencies
    print_subheader("Verifying Optional Dependencies")
    
    for group, config in OPTIONAL_DEPENDENCIES.items():
        group_success = True
        group_results = []
        
        print(f"\n{group.upper()}:")
        for package in config['packages']:
            package_name = package.split('==')[0]
            status = check_package_status(package_name)
            
            if status['installed']:
                print_status(f"{package_name} is installed (version: {status['version'] or 'unknown'})")
                group_results.append({
                    'package': package_name,
                    'installed': True,
                    'version': status['version']
                })
            else:
                print_status(f"{package_name} is not installed", warning=True)
                group_results.append({
                    'package': package_name,
                    'installed': False,
                    'error': status['import_error']
                })
                group_success = False
        
        results['optional'][group] = {
            'success': group_success,
            'packages': group_results
        }
    
    return results

def print_summary(installation_results: Dict[str, Any], verification_results: Dict[str, Any]) -> None:
    """Print a summary of the installation and verification results."""
    print_header("INSTALLATION SUMMARY")
    
    # Print core dependencies status
    core_success = installation_results.get('core', {}).get('success', False)
    if core_success:
        print_status("Core dependencies: Installed successfully")
    else:
        print_status("Core dependencies: Some installations failed", success=False)
    
    # Print provider dependencies status
    print("\nProvider dependencies:")
    for provider, result in installation_results.items():
        if provider == 'core':
            continue
            
        if result.get('success', False):
            print_status(f"  {provider.upper()}: Installed successfully")
        else:
            print_status(f"  {provider.upper()}: Some installations failed", success=False)
    
    # Print optional dependencies status
    print("\nOptional dependencies:")
    for group, result in installation_results.get('optional', {}).items():
        if result.get('success', False):
            print_status(f"  {group.upper()}: Installed successfully")
        else:
            print_status(f"  {group.upper()}: Some installations failed", warning=True)
    
    # Print overall status
    total_success = all(result.get('success', False) for result in installation_results.values() 
                        if result.get('required', True))
    
    print("\nOverall status:")
    if total_success:
        print_status("All required dependencies installed successfully")
    else:
        print_status("Some required dependencies failed to install", success=False)
        print_tip("Check the installation log for details on failed installations")
        print_tip("You may need to install some dependencies manually")
    
    # Print next steps
    print_subheader("NEXT STEPS")
    print_info("1. Configure API keys for each provider")
    print_info("2. Test the Nuke AI Panel integration")
    print_info("3. Refer to the INSTALLATION_GUIDE.md for detailed instructions")
    
    # Print troubleshooting tips if there were failures
    if not total_success:
        print_subheader("TROUBLESHOOTING TIPS")
        print_tip("1. Check your internet connection")
        print_tip("2. Make sure you have the necessary permissions to install packages")
        print_tip("3. Try installing failed packages manually using pip")
        print_tip("4. Check for version conflicts with existing packages")
        print_tip("5. For packages requiring compilation (numpy, pandas):")
        print_tip("   - On Windows: Install Visual C++ Build Tools")
        print_tip("   - On Linux: Install gcc and required development packages")
        print_tip("   - On macOS: Install Xcode Command Line Tools")
        print_tip("6. Consult the documentation for specific error messages")

def setup_provider_config(provider_name: str, config: Dict[str, Any]) -> None:
    """
    Provide guidance for setting up a provider configuration.
    
    Args:
        provider_name: Name of the provider
        config: Provider configuration
    """
    print_provider_setup_instructions(provider_name, config)

def main() -> None:
    """Main function to install all dependencies."""
    parser = argparse.ArgumentParser(
        description="Nuke AI Panel - Comprehensive Dependency Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install_all_dependencies.py                # Install all dependencies
  python install_all_dependencies.py --check-only   # Only check installation status
  python install_all_dependencies.py --skip-optional # Skip optional dependencies
        """
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check installation status, do not install anything'
    )
    
    parser.add_argument(
        '--skip-optional',
        action='store_true',
        help='Skip installation of optional dependencies'
    )
    
    parser.add_argument(
        '--upgrade',
        action='store_true',
        help='Upgrade packages to the latest version'
    )
    
    args = parser.parse_args()
    
    # Print header
    print_header("NUKE AI PANEL - DEPENDENCY INSTALLATION")
    
    # Get Python environment information
    python_info = get_python_info()
    print_info(f"Python executable: {python_info['executable']}")
    print_info(f"Python version: {python_info['version']}")
    print_info(f"Platform: {python_info['platform']}")
    print_info(f"Running in Nuke: {'Yes' if python_info['in_nuke'] else 'No'}")
    
    # If check-only mode, just verify installations and exit
    if args.check_only:
        verification_results = verify_installations()
        print_header("INSTALLATION CHECK COMPLETE")
        return
    
    # Initialize results dictionary
    installation_results = {}
    
    # Install core dependencies first
    core_results = install_dependency_group('core', PROVIDER_DEPENDENCIES['core'], upgrade=args.upgrade)
    installation_results['core'] = core_results
    
    # Install provider dependencies
    for provider, config in PROVIDER_DEPENDENCIES.items():
        if provider == 'core':
            continue
            
        provider_results = install_dependency_group(provider, config, upgrade=args.upgrade)
        installation_results[provider] = provider_results
    
    # Install optional dependencies if not skipped
    if not args.skip_optional:
        installation_results['optional'] = {}
        for group, config in OPTIONAL_DEPENDENCIES.items():
            group_results = install_dependency_group(group, config, upgrade=args.upgrade)
            installation_results['optional'][group] = group_results
    
    # Verify all installations
    verification_results = verify_installations()
    
    # Print provider setup instructions
    print_header("PROVIDER SETUP INSTRUCTIONS")
    for provider, config in PROVIDER_DEPENDENCIES.items():
        if provider == 'core':
            continue
            
        setup_provider_config(provider, config)
    
    # Print summary
    print_summary(installation_results, verification_results)
    
    print_header("INSTALLATION COMPLETE")
    print_info("Thank you for installing the Nuke AI Panel dependencies!")
    print_info("For more information, please refer to the INSTALLATION_GUIDE.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nAn error occurred during installation: {e}")
        sys.exit(1)