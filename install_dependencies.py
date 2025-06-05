#!/usr/bin/env python3
"""
Dependency installer for Nuke AI Panel providers.

This script installs the required Python libraries for each AI provider.
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install dependencies for all providers."""
    print("Installing Nuke AI Panel dependencies...")
    
    # Core dependencies (always needed)
    core_deps = [
        "aiohttp",  # For HTTP requests
        "pyyaml",   # For configuration files
        "cryptography",  # For secure credential storage
    ]
    
    # Provider-specific dependencies
    provider_deps = {
        "OpenAI": ["openai"],
        "Anthropic": ["anthropic"],
        "Google": ["google-generativeai"],
        "Mistral": ["mistralai"],
        "OpenRouter": ["openai"],  # Uses OpenAI-compatible API
        "Ollama": [],  # No additional deps needed (uses aiohttp)
    }
    
    print("\nInstalling core dependencies...")
    for dep in core_deps:
        print(f"Installing {dep}...")
        if install_package(dep):
            print(f"✓ {dep} installed successfully")
        else:
            print(f"✗ Failed to install {dep}")
    
    print("\nInstalling provider dependencies...")
    for provider, deps in provider_deps.items():
        if deps:
            print(f"\n{provider} provider:")
            for dep in deps:
                print(f"  Installing {dep}...")
                if install_package(dep):
                    print(f"  ✓ {dep} installed successfully")
                else:
                    print(f"  ✗ Failed to install {dep}")
        else:
            print(f"\n{provider} provider: No additional dependencies needed")
    
    print("\nDependency installation complete!")
    print("\nYou can now configure your API keys in the settings dialog.")

if __name__ == "__main__":
    main()