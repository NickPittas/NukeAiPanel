#!/usr/bin/env python3
"""
Nuke AI Panel Dependency Installer - Fixed Version

This script helps install AI provider dependencies in Nuke's Python environment.
It handles the common issues with missing dependencies and provides clear guidance.

Usage:
    python nuke_dependency_installer_fixed.py [--provider PROVIDER] [--all]
    
Examples:
    python nuke_dependency_installer_fixed.py --all
    python nuke_dependency_installer_fixed.py --provider openai
    python nuke_dependency_installer_fixed.py --provider anthropic
"""

import sys
import subprocess
import os
import argparse
from typing import List, Dict, Optional

# AI Provider Dependencies
PROVIDER_DEPENDENCIES = {
    'openai': {
        'packages': ['openai'],
        'description': 'OpenAI GPT models (GPT-4, GPT-3.5-turbo, etc.)',
        'test_import': 'import openai; from openai import AsyncOpenAI'
    },
    'anthropic': {
        'packages': ['anthropic'],
        'description': 'Anthropic Claude models (Claude-3 Opus, Sonnet, Haiku)',
        'test_import': 'import anthropic; from anthropic import AsyncAnthropic'
    },
    'google': {
        'packages': ['google-generativeai'],
        'description': 'Google Gemini models',
        'test_import': 'import google.generativeai as genai'
    },
    'ollama': {
        'packages': ['aiohttp'],
        'description': 'Ollama local AI models',
        'test_import': 'import aiohttp'
    },
    'openrouter': {
        'packages': ['aiohttp'],
        'description': 'OpenRouter API access',
        'test_import': 'import aiohttp'
    },
    'mistral': {
        'packages': ['mistralai'],
        'description': 'Mistral AI models',
        'test_import': 'import mistralai'
    }
}

# Optional dependencies for enhanced functionality
OPTIONAL_DEPENDENCIES = {
    'cryptography': {
        'packages': ['cryptography'],
        'description': 'Secure credential storage (recommended)',
        'test_import': 'import cryptography'
    },
    'pyside6': {
        'packages': ['PySide6'],
        'description': 'Qt6 GUI framework (for standalone usage)',
        'test_import': 'import PySide6'
    }
}

def get_python_executable() -> str:
    """Get the Python executable path."""
    return sys.executable

def check_nuke_environment() -> bool:
    """Check if we're running in a Nuke environment."""
    try:
        import nuke
        return True
    except ImportError:
        return False

def test_import(import_statement: str) -> bool:
    """Test if an import statement works."""
    try:
        exec(import_statement)
        return True
    except ImportError:
        return False
    except Exception:
        return False

def install_package(package: str, python_exe: str = None) -> bool:
    """Install a package using pip."""
    if python_exe is None:
        python_exe = get_python_executable()
    
    try:
        print(f"  Installing {package}...")
        result = subprocess.run(
            [python_exe, '-m', 'pip', 'install', package],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install {package}")
        print(f"     Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"  ❌ Failed to install {package}: {e}")
        return False

def check_provider_status(provider: str, config: Dict) -> Dict:
    """Check the installation status of a provider."""
    status = {
        'provider': provider,
        'description': config['description'],
        'packages': config['packages'],
        'installed': False,
        'missing_packages': []
    }
    
    # Test the import
    if test_import(config['test_import']):
        status['installed'] = True
    else:
        # Check individual packages
        for package in config['packages']:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                status['missing_packages'].append(package)
    
    return status

def print_status_report():
    """Print a status report of all providers."""
    print("\n" + "="*60)
    print("🔍 NUKE AI PANEL DEPENDENCY STATUS")
    print("="*60)
    
    # Check if we're in Nuke
    in_nuke = check_nuke_environment()
    print(f"Environment: {'Nuke' if in_nuke else 'Standalone Python'}")
    print(f"Python: {get_python_executable()}")
    print()
    
    # Check AI providers
    print("AI PROVIDERS:")
    print("-" * 40)
    
    available_providers = []
    missing_providers = []
    
    for provider, config in PROVIDER_DEPENDENCIES.items():
        status = check_provider_status(provider, config)
        
        if status['installed']:
            print(f"✅ {provider.upper()}: {config['description']}")
            available_providers.append(provider)
        else:
            print(f"❌ {provider.upper()}: {config['description']}")
            print(f"   Missing: {', '.join(status['missing_packages'])}")
            missing_providers.append(provider)
    
    # Check optional dependencies
    print("\nOPTIONAL DEPENDENCIES:")
    print("-" * 40)
    
    for dep, config in OPTIONAL_DEPENDENCIES.items():
        status = check_provider_status(dep, config)
        
        if status['installed']:
            print(f"✅ {dep.upper()}: {config['description']}")
        else:
            print(f"⚠️  {dep.upper()}: {config['description']}")
            print(f"   Missing: {', '.join(status['missing_packages'])}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Available AI Providers: {len(available_providers)}/{len(PROVIDER_DEPENDENCIES)}")
    
    if available_providers:
        print(f"✅ Working: {', '.join(available_providers)}")
    
    if missing_providers:
        print(f"❌ Missing: {', '.join(missing_providers)}")
        print("\n💡 TIP: Use --provider <name> to install specific providers")
        print("💡 TIP: Use --all to install all providers")
    else:
        print("🎉 All AI providers are available!")

def install_provider(provider: str) -> bool:
    """Install dependencies for a specific provider."""
    if provider not in PROVIDER_DEPENDENCIES:
        print(f"❌ Unknown provider: {provider}")
        print(f"Available providers: {', '.join(PROVIDER_DEPENDENCIES.keys())}")
        return False
    
    config = PROVIDER_DEPENDENCIES[provider]
    print(f"\n🚀 Installing {provider.upper()} dependencies...")
    print(f"Description: {config['description']}")
    print(f"Packages: {', '.join(config['packages'])}")
    
    success = True
    for package in config['packages']:
        if not install_package(package):
            success = False
    
    if success:
        print(f"\n✅ {provider.upper()} installation completed!")
        
        # Test the installation
        if test_import(config['test_import']):
            print(f"✅ {provider.upper()} is working correctly!")
        else:
            print(f"⚠️  {provider.upper()} installed but import test failed")
            success = False
    else:
        print(f"\n❌ {provider.upper()} installation failed!")
    
    return success

def install_all_providers() -> bool:
    """Install all AI provider dependencies."""
    print("\n🚀 Installing ALL AI provider dependencies...")
    
    success_count = 0
    total_count = len(PROVIDER_DEPENDENCIES)
    
    for provider in PROVIDER_DEPENDENCIES.keys():
        if install_provider(provider):
            success_count += 1
        print()  # Add spacing between providers
    
    print("="*60)
    print(f"📊 INSTALLATION SUMMARY: {success_count}/{total_count} providers installed")
    
    if success_count == total_count:
        print("🎉 All AI providers installed successfully!")
        return True
    else:
        print(f"⚠️  {total_count - success_count} providers failed to install")
        return False

def install_optional_dependencies():
    """Install optional dependencies."""
    print("\n🔧 Installing optional dependencies...")
    
    for dep, config in OPTIONAL_DEPENDENCIES.items():
        print(f"\nInstalling {dep.upper()}: {config['description']}")
        
        for package in config['packages']:
            install_package(package)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Install AI provider dependencies for Nuke AI Panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nuke_dependency_installer_fixed.py                    # Show status
  python nuke_dependency_installer_fixed.py --all             # Install all providers
  python nuke_dependency_installer_fixed.py --provider openai # Install OpenAI only
  python nuke_dependency_installer_fixed.py --optional        # Install optional deps
        """
    )
    
    parser.add_argument(
        '--provider',
        choices=list(PROVIDER_DEPENDENCIES.keys()),
        help='Install dependencies for a specific provider'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Install all AI provider dependencies'
    )
    
    parser.add_argument(
        '--optional',
        action='store_true',
        help='Install optional dependencies'
    )
    
    parser.add_argument(
        '--status-only',
        action='store_true',
        help='Only show status, do not install anything'
    )
    
    args = parser.parse_args()
    
    # Always show status first
    print_status_report()
    
    if args.status_only:
        return
    
    # Perform installations
    if args.all:
        install_all_providers()
    elif args.provider:
        install_provider(args.provider)
    elif args.optional:
        install_optional_dependencies()
    else:
        print("\n💡 Use --help to see installation options")
        print("💡 Use --all to install all providers")
        print("💡 Use --provider <name> to install a specific provider")
    
    # Show final status if we installed anything
    if args.all or args.provider or args.optional:
        print("\n" + "="*60)
        print("🔄 FINAL STATUS CHECK")
        print_status_report()

if __name__ == "__main__":
    main()