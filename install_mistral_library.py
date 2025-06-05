#!/usr/bin/env python3
"""
Script to install the Mistral library.

This script ensures the Mistral library is properly installed
and can be imported correctly.
"""

import subprocess
import sys
import importlib
import os
from pathlib import Path

def print_status(message, success=True):
    """Print a status message with color."""
    if success:
        print(f"\033[92m✓ {message}\033[0m")  # Green
    else:
        print(f"\033[91m✗ {message}\033[0m")  # Red

def install_mistral():
    """Install the Mistral library."""
    print("Installing Mistral library...")
    
    # First, try to uninstall any existing installation
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "mistralai"],
            check=False,
            capture_output=True,
            text=True
        )
        print_status("Removed any existing Mistral library")
    except Exception as e:
        print_status(f"Error removing existing Mistral library: {e}", False)
    
    # Install the latest version
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "mistralai"],
            check=True,
            capture_output=True,
            text=True
        )
        print_status("Installed Mistral library")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Failed to install Mistral library: {e.stderr}", False)
        return False
    except Exception as e:
        print_status(f"Error installing Mistral library: {e}", False)
        return False

def verify_installation():
    """Verify that the Mistral library is correctly installed."""
    print("\nVerifying Mistral library installation...")
    
    # Reload modules to ensure we get the latest version
    importlib.invalidate_caches()
    
    # Try to import the library
    try:
        import mistralai
        version = getattr(mistralai, "__version__", "unknown")
        print_status(f"Mistral library imported successfully (version: {version})")
        
        # Try to import the client
        try:
            from mistralai.async_client import MistralAsyncClient
            print_status("MistralAsyncClient imported successfully")
            return True
        except ImportError:
            try:
                from mistralai import Mistral
                print_status("Mistral client imported successfully (newer structure)")
                return True
            except ImportError:
                try:
                    from mistralai.client import MistralClient
                    print_status("MistralClient imported successfully (alternative structure)")
                    return True
                except ImportError:
                    print_status("Failed to import Mistral client", False)
                    return False
    except ImportError as e:
        print_status(f"Failed to import Mistral library: {e}", False)
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("Mistral Library Installer")
    print("=" * 60)
    print("This script will install the Mistral library required for authentication.")
    print()
    
    # Install the library
    install_success = install_mistral()
    if not install_success:
        print("\nFailed to install the Mistral library.")
        print("Please try installing manually with:")
        print("  pip install --upgrade mistralai")
        return
    
    # Verify the installation
    verify_success = verify_installation()
    if not verify_success:
        print("\nMistral library was installed but verification failed.")
        print("You may need to restart your Python environment.")
        return
    
    print("\n" + "=" * 60)
    print("✅ Mistral library installed successfully!")
    print("You can now use the Mistral provider in the Nuke AI Panel.")
    print("Note: You may need to restart the application for changes to take effect.")
    print("=" * 60)

if __name__ == "__main__":
    main()