#!/usr/bin/env python3
"""
Automated installation script for Nuke AI Panel.
Handles installation across different environments and Nuke versions.
"""

import os
import sys
import shutil
import argparse
import subprocess
import platform
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import urllib.request
import zipfile


class NukeAIPanelInstaller:
    """Main installer class for Nuke AI Panel."""
    
    def __init__(self):
        self.system = platform.system()
        self.python_version = sys.version_info
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parent
        
        # Installation paths
        self.nuke_paths = self._detect_nuke_installations()
        self.user_nuke_dir = self._get_user_nuke_dir()
        self.config_dir = self._get_config_dir()
        
        # Installation state
        self.installed_components = []
        self.failed_components = []
        
    def _detect_nuke_installations(self) -> Dict[str, Path]:
        """Detect installed Nuke versions."""
        nuke_installations = {}
        
        if self.system == "Windows":
            # Common Windows installation paths
            program_files = [
                Path("C:/Program Files/Nuke*"),
                Path("C:/Program Files (x86)/Nuke*")
            ]
            
            for pf in program_files:
                for nuke_dir in pf.parent.glob(pf.name):
                    if nuke_dir.is_dir():
                        version = self._extract_nuke_version(nuke_dir.name)
                        if version:
                            nuke_installations[version] = nuke_dir
                            
        elif self.system == "Darwin":  # macOS
            # Common macOS installation paths
            apps_dir = Path("/Applications")
            for nuke_app in apps_dir.glob("Nuke*.app"):
                version = self._extract_nuke_version(nuke_app.name)
                if version:
                    nuke_installations[version] = nuke_app
                    
        else:  # Linux
            # Common Linux installation paths
            opt_dirs = [Path("/opt"), Path("/usr/local")]
            for opt_dir in opt_dirs:
                if opt_dir.exists():
                    for nuke_dir in opt_dir.glob("Nuke*"):
                        if nuke_dir.is_dir():
                            version = self._extract_nuke_version(nuke_dir.name)
                            if version:
                                nuke_installations[version] = nuke_dir
        
        return nuke_installations
    
    def _extract_nuke_version(self, name: str) -> Optional[str]:
        """Extract Nuke version from directory/app name."""
        import re
        match = re.search(r'(\d+\.\d+)', name)
        return match.group(1) if match else None
    
    def _get_user_nuke_dir(self) -> Path:
        """Get user's Nuke directory."""
        home = Path.home()
        return home / ".nuke"
    
    def _get_config_dir(self) -> Path:
        """Get configuration directory."""
        home = Path.home()
        return home / ".nuke_ai_panel"
    
    def check_prerequisites(self) -> bool:
        """Check installation prerequisites."""
        print("Checking prerequisites...")
        
        # Check Python version
        if self.python_version < (3, 8):
            print(f"❌ Python 3.8+ required, found {self.python_version.major}.{self.python_version.minor}")
            return False
        print(f"✅ Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        
        # Check if Nuke is installed
        if not self.nuke_paths:
            print("⚠️  No Nuke installations detected")
            print("   You can still install the Python package and integrate manually")
        else:
            print(f"✅ Found Nuke installations: {list(self.nuke_paths.keys())}")
        
        # Check required Python packages
        required_packages = [
            'aiohttp', 'cryptography', 'pyyaml', 'pydantic'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} (will be installed)")
        
        return True
    
    def install_python_package(self) -> bool:
        """Install the Python package."""
        print("\n📦 Installing Python package...")
        
        try:
            # Install in development mode
            cmd = [sys.executable, "-m", "pip", "install", "-e", str(self.project_root)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Python package installed successfully")
                self.installed_components.append("python_package")
                return True
            else:
                print(f"❌ Failed to install Python package: {result.stderr}")
                self.failed_components.append("python_package")
                return False
                
        except Exception as e:
            print(f"❌ Error installing Python package: {e}")
            self.failed_components.append("python_package")
            return False
    
    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        print("\n📚 Installing dependencies...")
        
        try:
            requirements_file = self.project_root / "requirements.txt"
            if not requirements_file.exists():
                print("⚠️  requirements.txt not found, skipping dependency installation")
                return True
            
            # Check if we're on Python 3.13+ for special numpy handling
            is_py313_plus = sys.version_info >= (3, 13)
            if is_py313_plus:
                print("⚠️  Detected Python 3.13+ - using special installation method for numpy")
                
                # Install dependencies excluding numpy
                with open(requirements_file, 'r') as f:
                    requirements = f.readlines()
                
                temp_requirements = []
                has_numpy = False
                
                for req in requirements:
                    req = req.strip()
                    if req and not req.startswith('#'):
                        if req.startswith('numpy'):
                            has_numpy = True
                        else:
                            temp_requirements.append(req)
                
                # Create temporary requirements file without numpy
                temp_req_file = self.project_root / "temp_requirements.txt"
                with open(temp_req_file, 'w') as f:
                    f.write('\n'.join(temp_requirements))
                
                # Install other dependencies
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(temp_req_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Clean up temp file
                temp_req_file.unlink()
                
                if result.returncode != 0:
                    print(f"❌ Failed to install dependencies: {result.stderr}")
                    self.failed_components.append("dependencies")
                    return False
                
                # Install numpy using special method if needed
                if has_numpy:
                    print("📦 Installing numpy with special handling...")
                    
                    # Try to use fix_numpy_installation.py if available
                    fix_script_path = self.project_root / "fix_numpy_installation.py"
                    if fix_script_path.exists():
                        print("🔧 Using fix_numpy_installation.py script")
                        cmd = [sys.executable, str(fix_script_path), "--version", "1.24.4"]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            print(f"⚠️  Numpy installation with fix script failed: {result.stderr}")
                            print("🔄 Trying alternative methods...")
                    
                    # Try binary installation
                    try:
                        print("🔍 Trying binary installation of numpy...")
                        cmd = [sys.executable, "-m", "pip", "install", "--only-binary=:all:", "numpy==1.24.4"]
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            # Try different numpy versions
                            for version in ["1.26.4", "1.25.2", "1.24.4", "1.23.5"]:
                                print(f"🔍 Trying numpy=={version}...")
                                cmd = [sys.executable, "-m", "pip", "install", "--only-binary=:all:", f"numpy=={version}"]
                                result = subprocess.run(cmd, capture_output=True, text=True)
                                
                                if result.returncode == 0:
                                    print(f"✅ numpy=={version} installed successfully")
                                    break
                    except Exception as e:
                        print(f"⚠️  Error during numpy installation: {e}")
            else:
                # Standard installation for Python < 3.13
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ Failed to install dependencies: {result.stderr}")
                    self.failed_components.append("dependencies")
                    return False
            
            print("✅ Dependencies installed successfully")
            self.installed_components.append("dependencies")
            return True
                
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            self.failed_components.append("dependencies")
            return False
    
    def setup_nuke_integration(self, nuke_version: Optional[str] = None) -> bool:
        """Set up Nuke integration."""
        print("\n🎬 Setting up Nuke integration...")
        
        if not self.user_nuke_dir.exists():
            print("Creating Nuke user directory...")
            self.user_nuke_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy source files to Nuke directory
            src_dir = self.project_root / "src"
            nuke_plugin_dir = self.user_nuke_dir / "nuke_ai_panel"
            
            if nuke_plugin_dir.exists():
                print("Removing existing installation...")
                shutil.rmtree(nuke_plugin_dir)
            
            print("Copying source files...")
            shutil.copytree(src_dir, nuke_plugin_dir)
            
            # Set up menu integration
            self._setup_menu_integration()
            
            # Set up init.py if needed
            self._setup_init_integration()
            
            print("✅ Nuke integration set up successfully")
            self.installed_components.append("nuke_integration")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Nuke integration: {e}")
            self.failed_components.append("nuke_integration")
            return False
    
    def _setup_menu_integration(self):
        """Set up menu integration."""
        menu_file = self.user_nuke_dir / "menu.py"
        
        menu_code = '''
# Nuke AI Panel Menu Integration
import sys
import os

# Add AI Panel to Python path
ai_panel_path = os.path.join(os.path.expanduser("~/.nuke"), "nuke_ai_panel")
if ai_panel_path not in sys.path:
    sys.path.insert(0, ai_panel_path)

try:
    import nuke
    from src.ui.main_panel import NukeAIPanel
    
    def show_ai_panel():
        """Show the AI Panel."""
        try:
            panel = NukeAIPanel()
            panel.show()
        except Exception as e:
            nuke.message(f"Error opening AI Panel: {e}")
    
    # Add menu item
    menubar = nuke.menu("Nuke")
    ai_menu = menubar.addMenu("AI Panel")
    ai_menu.addCommand("Show AI Panel", show_ai_panel)
    ai_menu.addSeparator()
    ai_menu.addCommand("Settings", lambda: show_ai_panel() and panel.show_settings())
    
except ImportError as e:
    print(f"Nuke AI Panel not available: {e}")
'''
        
        if menu_file.exists():
            # Append to existing menu.py
            with open(menu_file, 'a') as f:
                f.write(f"\n\n# === Nuke AI Panel Integration ===\n{menu_code}")
        else:
            # Create new menu.py
            with open(menu_file, 'w') as f:
                f.write(menu_code)
        
        print("✅ Menu integration set up")
    
    def _setup_init_integration(self):
        """Set up init.py integration if needed."""
        init_file = self.user_nuke_dir / "init.py"
        
        init_code = '''
# Nuke AI Panel Initialization
import sys
import os

# Add AI Panel to Python path
ai_panel_path = os.path.join(os.path.expanduser("~/.nuke"), "nuke_ai_panel")
if ai_panel_path not in sys.path:
    sys.path.insert(0, ai_panel_path)

# Set environment variables
os.environ["NUKE_AI_PANEL_NUKE_INTEGRATION"] = "true"
'''
        
        if not init_file.exists():
            with open(init_file, 'w') as f:
                f.write(init_code)
            print("✅ Init integration set up")
    
    def setup_configuration(self, environment: str = "production") -> bool:
        """Set up configuration files."""
        print(f"\n⚙️  Setting up {environment} configuration...")
        
        try:
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy appropriate config file
            config_source = self.project_root / "config" / f"{environment}_config.yaml"
            config_dest = self.config_dir / "config.yaml"
            
            if config_source.exists():
                shutil.copy2(config_source, config_dest)
                print(f"✅ Configuration copied from {config_source.name}")
            else:
                # Use default config
                default_config = self.project_root / "config" / "default_config.yaml"
                if default_config.exists():
                    shutil.copy2(default_config, config_dest)
                    print("✅ Default configuration copied")
                else:
                    print("⚠️  No configuration file found, will use built-in defaults")
            
            # Create other directories
            (self.config_dir / "cache").mkdir(exist_ok=True)
            (self.config_dir / "logs").mkdir(exist_ok=True)
            (self.config_dir / "sessions").mkdir(exist_ok=True)
            
            # Set secure permissions
            if self.system != "Windows":
                os.chmod(self.config_dir, 0o700)
                if config_dest.exists():
                    os.chmod(config_dest, 0o600)
            
            print("✅ Configuration set up successfully")
            self.installed_components.append("configuration")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up configuration: {e}")
            self.failed_components.append("configuration")
            return False
    
    def setup_authentication(self) -> bool:
        """Set up authentication wizard."""
        print("\n🔐 Setting up authentication...")
        
        try:
            from nuke_ai_panel.core.auth import AuthManager
            
            auth_manager = AuthManager()
            
            print("\nAPI Key Setup:")
            print("You can set up API keys now or later through the UI.")
            
            setup_now = input("Set up API keys now? (y/N): ").lower().strip()
            
            if setup_now == 'y':
                providers = ['openai', 'anthropic', 'google', 'mistral']
                
                for provider in providers:
                    api_key = input(f"Enter {provider.upper()} API key (or press Enter to skip): ").strip()
                    if api_key:
                        auth_manager.set_api_key(provider, api_key)
                        print(f"✅ {provider.upper()} API key saved")
            
            print("✅ Authentication set up successfully")
            self.installed_components.append("authentication")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up authentication: {e}")
            self.failed_components.append("authentication")
            return False
    
    def run_tests(self) -> bool:
        """Run basic tests to verify installation."""
        print("\n🧪 Running installation tests...")
        
        try:
            # Test Python package import
            import nuke_ai_panel
            print("✅ Python package import successful")
            
            # Test configuration loading
            from nuke_ai_panel.core.config import Config
            config = Config()
            print("✅ Configuration loading successful")
            
            # Test provider manager
            from nuke_ai_panel.core.provider_manager import ProviderManager
            provider_manager = ProviderManager(config=config)
            print("✅ Provider manager initialization successful")
            
            print("✅ All tests passed")
            self.installed_components.append("tests")
            return True
            
        except Exception as e:
            print(f"❌ Tests failed: {e}")
            self.failed_components.append("tests")
            return False
    
    def create_desktop_shortcut(self) -> bool:
        """Create desktop shortcut (optional)."""
        print("\n🖥️  Creating desktop shortcut...")
        
        try:
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                return True  # Skip if no desktop
            
            if self.system == "Windows":
                # Create Windows shortcut
                shortcut_path = desktop / "Nuke AI Panel.lnk"
                # This would require pywin32 for full implementation
                print("⚠️  Windows shortcut creation requires additional setup")
                
            elif self.system == "Darwin":  # macOS
                # Create macOS alias/shortcut
                print("⚠️  macOS shortcut creation not implemented")
                
            else:  # Linux
                # Create .desktop file
                desktop_file = desktop / "nuke-ai-panel.desktop"
                desktop_content = f"""[Desktop Entry]
Name=Nuke AI Panel
Comment=AI-powered panel for Nuke
Exec={sys.executable} -c "from nuke_ai_panel.ui.standalone import main; main()"
Icon={self.project_root}/assets/icon.png
Terminal=false
Type=Application
Categories=Graphics;
"""
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                
                os.chmod(desktop_file, 0o755)
                print("✅ Desktop shortcut created")
            
            self.installed_components.append("desktop_shortcut")
            return True
            
        except Exception as e:
            print(f"❌ Error creating desktop shortcut: {e}")
            self.failed_components.append("desktop_shortcut")
            return False
    
    def print_installation_summary(self):
        """Print installation summary."""
        print("\n" + "="*60)
        print("🎉 INSTALLATION SUMMARY")
        print("="*60)
        
        if self.installed_components:
            print("\n✅ Successfully installed:")
            for component in self.installed_components:
                print(f"   • {component.replace('_', ' ').title()}")
        
        if self.failed_components:
            print("\n❌ Failed to install:")
            for component in self.failed_components:
                print(f"   • {component.replace('_', ' ').title()}")
        
        print(f"\n📁 Installation locations:")
        print(f"   • Configuration: {self.config_dir}")
        print(f"   • Nuke integration: {self.user_nuke_dir / 'nuke_ai_panel'}")
        
        print(f"\n🚀 Next steps:")
        if "nuke_integration" in self.installed_components:
            print("   1. Start Nuke")
            print("   2. Look for 'AI Panel' in the menu bar")
            print("   3. Configure your API keys in Settings")
        else:
            print("   1. Set up Nuke integration manually")
            print("   2. Configure API keys")
        
        print("\n📖 Documentation:")
        print("   • Installation guide: docs/INSTALLATION.md")
        print("   • API reference: docs/API_REFERENCE.md")
        print("   • Troubleshooting: docs/TROUBLESHOOTING.md")
        
        if self.failed_components:
            print(f"\n⚠️  Some components failed to install.")
            print(f"   Check the troubleshooting guide for help.")
    
    def install(self, args):
        """Run the complete installation process."""
        print("🚀 Starting Nuke AI Panel installation...")
        print(f"   System: {self.system}")
        print(f"   Python: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print(f"   Environment: {args.environment}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("❌ Prerequisites not met. Please fix the issues above and try again.")
            return False
        
        # Install components
        success = True
        
        if not args.no_python_package:
            success &= self.install_python_package()
        
        if not args.no_dependencies:
            success &= self.install_dependencies()
        
        if not args.no_nuke_integration:
            success &= self.setup_nuke_integration(args.nuke_version)
        
        if not args.no_config:
            success &= self.setup_configuration(args.environment)
        
        if not args.no_auth and args.interactive:
            success &= self.setup_authentication()
        
        if args.run_tests:
            success &= self.run_tests()
        
        if args.create_shortcut:
            success &= self.create_desktop_shortcut()
        
        # Print summary
        self.print_installation_summary()
        
        return success


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(
        description="Install Nuke AI Panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install_script.py                          # Basic installation
  python install_script.py --environment development # Development setup
  python install_script.py --environment studio     # Studio setup
  python install_script.py --no-nuke-integration    # Python package only
  python install_script.py --nuke-version 14.0      # Specific Nuke version
        """
    )
    
    parser.add_argument(
        "--environment",
        choices=["production", "development", "studio"],
        default="production",
        help="Installation environment"
    )
    
    parser.add_argument(
        "--nuke-version",
        help="Target Nuke version (e.g., 14.0)"
    )
    
    parser.add_argument(
        "--nuke-path",
        help="Custom Nuke installation path"
    )
    
    parser.add_argument(
        "--no-python-package",
        action="store_true",
        help="Skip Python package installation"
    )
    
    parser.add_argument(
        "--no-dependencies",
        action="store_true",
        help="Skip dependency installation"
    )
    
    parser.add_argument(
        "--no-nuke-integration",
        action="store_true",
        help="Skip Nuke integration setup"
    )
    
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Skip configuration setup"
    )
    
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Skip authentication setup"
    )
    
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run tests after installation"
    )
    
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Create desktop shortcut"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Interactive installation (default)"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive installation"
    )
    
    args = parser.parse_args()
    
    if args.non_interactive:
        args.interactive = False
    
    # Create installer and run
    installer = NukeAIPanelInstaller()
    
    try:
        success = installer.install(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Installation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()