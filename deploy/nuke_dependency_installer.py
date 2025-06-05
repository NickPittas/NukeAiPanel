#!/usr/bin/env python3
"""
Nuke Dependency Installer for Nuke AI Panel.
Installs required Python packages in Nuke's Python environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class NukeDependencyInstaller:
    """Installer for Nuke AI Panel dependencies in Nuke's Python environment."""
    
    def __init__(self):
        self.system = platform.system()
        self.nuke_installations = self._detect_nuke_installations()
        self.required_packages = [
            "pyyaml>=6.0",
            "aiohttp>=3.8.0",
            "cryptography>=41.0.0",
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0",
            "tenacity>=8.2.0",
            "cachetools>=5.3.0",
            "colorlog>=6.7.0"
        ]
        
    def _detect_nuke_installations(self) -> Dict[str, Path]:
        """Detect installed Nuke versions and their Python executables."""
        installations = {}
        
        if self.system == "Windows":
            # Common Windows installation paths
            program_files = [
                Path("C:/Program Files/Nuke*"),
                Path("C:/Program Files (x86)/Nuke*")
            ]
            
            for pf in program_files:
                for nuke_dir in pf.parent.glob(pf.name):
                    if nuke_dir.is_dir():
                        python_exe = nuke_dir / "python.exe"
                        if python_exe.exists():
                            version = self._extract_nuke_version(nuke_dir.name)
                            if version:
                                installations[version] = python_exe
                                
        elif self.system == "Darwin":  # macOS
            # Common macOS installation paths
            apps_dir = Path("/Applications")
            for nuke_app in apps_dir.glob("Nuke*.app"):
                python_exe = nuke_app / "Contents" / "MacOS" / "python"
                if python_exe.exists():
                    version = self._extract_nuke_version(nuke_app.name)
                    if version:
                        installations[version] = python_exe
                        
        else:  # Linux
            # Common Linux installation paths
            opt_dirs = [Path("/opt"), Path("/usr/local")]
            for opt_dir in opt_dirs:
                if opt_dir.exists():
                    for nuke_dir in opt_dir.glob("Nuke*"):
                        if nuke_dir.is_dir():
                            python_exe = nuke_dir / "python"
                            if python_exe.exists():
                                version = self._extract_nuke_version(nuke_dir.name)
                                if version:
                                    installations[version] = python_exe
        
        return installations
    
    def _extract_nuke_version(self, name: str) -> Optional[str]:
        """Extract Nuke version from directory/app name."""
        import re
        match = re.search(r'(\d+\.\d+)', name)
        return match.group(1) if match else None
    
    def list_nuke_installations(self):
        """List detected Nuke installations."""
        print("Detected Nuke installations:")
        if not self.nuke_installations:
            print("   No Nuke installations found")
            return
        
        for version, python_path in self.nuke_installations.items():
            print(f"   * Nuke {version}: {python_path}")
    
    def check_python_environment(self, python_exe: Path) -> Dict[str, any]:
        """Check Python environment and installed packages."""
        try:
            # Get Python version
            result = subprocess.run(
                [str(python_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {"error": "Failed to get Python version"}
            
            python_version = result.stdout.strip()
            
            # Check pip availability
            pip_result = subprocess.run(
                [str(python_exe), "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            has_pip = pip_result.returncode == 0
            
            # Check installed packages
            installed_packages = {}
            if has_pip:
                list_result = subprocess.run(
                    [str(python_exe), "-m", "pip", "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if list_result.returncode == 0:
                    import json
                    try:
                        packages = json.loads(list_result.stdout)
                        installed_packages = {pkg["name"].lower(): pkg["version"] for pkg in packages}
                    except json.JSONDecodeError:
                        pass
            
            return {
                "python_version": python_version,
                "has_pip": has_pip,
                "installed_packages": installed_packages
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def check_required_packages(self, python_exe: Path) -> Dict[str, bool]:
        """Check which required packages are installed."""
        env_info = self.check_python_environment(python_exe)
        
        if "error" in env_info:
            return {}
        
        installed = env_info.get("installed_packages", {})
        package_status = {}
        
        for package_spec in self.required_packages:
            package_name = package_spec.split(">=")[0].split("==")[0]
            package_status[package_name] = package_name.lower() in installed
        
        return package_status
    
    def install_package(self, python_exe: Path, package: str) -> bool:
        """Install a single package."""
        try:
            print(f"   Installing {package}...")
            result = subprocess.run(
                [str(python_exe), "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"   ✅ {package} installed successfully")
                return True
            else:
                print(f"   ❌ Failed to install {package}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout installing {package}")
            return False
        except Exception as e:
            print(f"   ❌ Error installing {package}: {e}")
            return False
    
    def install_dependencies(self, nuke_version: str = None) -> bool:
        """Install all required dependencies."""
        if not self.nuke_installations:
            print("❌ No Nuke installations found")
            return False
        
        # Select Nuke version
        if nuke_version and nuke_version in self.nuke_installations:
            python_exe = self.nuke_installations[nuke_version]
            print(f"📦 Installing dependencies for Nuke {nuke_version}")
        else:
            # Use the latest version
            latest_version = max(self.nuke_installations.keys())
            python_exe = self.nuke_installations[latest_version]
            print(f"📦 Installing dependencies for Nuke {latest_version} (latest found)")
        
        # Check environment
        env_info = self.check_python_environment(python_exe)
        if "error" in env_info:
            print(f"❌ Error checking Python environment: {env_info['error']}")
            return False
        
        print(f"🐍 Python version: {env_info['python_version']}")
        
        if not env_info["has_pip"]:
            print("❌ pip is not available in this Python environment")
            return False
        
        # Check current package status
        package_status = self.check_required_packages(python_exe)
        
        print("\n📋 Package status:")
        for package_spec in self.required_packages:
            package_name = package_spec.split(">=")[0].split("==")[0]
            status = "✅ Installed" if package_status.get(package_name, False) else "❌ Missing"
            print(f"   {package_name}: {status}")
        
        # Install missing packages
        missing_packages = [
            pkg for pkg in self.required_packages
            if not package_status.get(pkg.split(">=")[0].split("==")[0], False)
        ]
        
        if not missing_packages:
            print("\n✅ All required packages are already installed!")
            return True
        
        print(f"\n📥 Installing {len(missing_packages)} missing packages...")
        
        success_count = 0
        for package in missing_packages:
            if self.install_package(python_exe, package):
                success_count += 1
        
        print(f"\n📊 Installation summary:")
        print(f"   Successfully installed: {success_count}/{len(missing_packages)}")
        
        if success_count == len(missing_packages):
            print("✅ All dependencies installed successfully!")
            return True
        else:
            print("⚠️  Some dependencies failed to install")
            return False
    
    def create_test_script(self) -> Path:
        """Create a test script to verify the installation."""
        test_script = Path("test_nuke_ai_panel.py")
        
        test_code = '''#!/usr/bin/env python
"""
Test script to verify Nuke AI Panel dependencies.
Run this script in Nuke's Script Editor to test the installation.
"""

def test_imports():
    """Test importing required modules."""
    print("🧪 Testing Nuke AI Panel dependencies...")
    
    tests = [
        ("yaml", "PyYAML"),
        ("aiohttp", "aiohttp"),
        ("cryptography", "cryptography"),
        ("pydantic", "pydantic"),
        ("dotenv", "python-dotenv"),
        ("tenacity", "tenacity"),
        ("cachetools", "cachetools"),
        ("colorlog", "colorlog")
    ]
    
    results = []
    for module, package in tests:
        try:
            __import__(module)
            print(f"   ✅ {package}")
            results.append(True)
        except ImportError as e:
            print(f"   ❌ {package}: {e}")
            results.append(False)
    
    # Test Nuke AI Panel import
    try:
        import sys
        import os
        
        # Add the AI Panel to Python path (adjust path as needed)
        ai_panel_path = os.path.expanduser("~/.nuke/nuke_ai_panel")
        if ai_panel_path not in sys.path:
            sys.path.insert(0, ai_panel_path)
        
        from nuke_ai_panel.core.config import Config
        config = Config()
        print("   ✅ Nuke AI Panel configuration")
        results.append(True)
        
    except Exception as e:
        print(f"   ❌ Nuke AI Panel: {e}")
        results.append(False)
    
    success_rate = sum(results) / len(results)
    print(f"\\n📊 Test Results: {sum(results)}/{len(results)} passed ({success_rate:.1%})")
    
    if success_rate == 1.0:
        print("🎉 All tests passed! Nuke AI Panel should work correctly.")
    elif success_rate >= 0.8:
        print("⚠️  Most tests passed. Some optional features may not work.")
    else:
        print("❌ Many tests failed. Please check the installation.")
    
    return success_rate

if __name__ == "__main__":
    test_imports()
'''
        
        with open(test_script, 'w') as f:
            f.write(test_code)
        
        print(f"📝 Created test script: {test_script}")
        print("   Run this script in Nuke's Script Editor to verify the installation")
        
        return test_script
    
    def print_installation_instructions(self):
        """Print manual installation instructions."""
        print("\n📖 Manual Installation Instructions:")
        print("="*50)
        
        print("\n1. Find your Nuke installation:")
        for version, python_path in self.nuke_installations.items():
            print(f"   Nuke {version}: {python_path.parent}")
        
        print("\n2. Install packages manually:")
        print("   Open a command prompt/terminal as administrator and run:")
        
        for version, python_path in self.nuke_installations.items():
            print(f"\n   For Nuke {version}:")
            for package in self.required_packages:
                print(f'   "{python_path}" -m pip install {package}')
        
        print("\n3. Alternative: Use Nuke's Python directly:")
        print("   In Nuke's Script Editor, run:")
        print("   import subprocess")
        print("   import sys")
        for package in self.required_packages:
            print(f'   subprocess.check_call([sys.executable, "-m", "pip", "install", "{package}"])')
        
        print("\n4. Verify installation:")
        print("   Run the generated test script in Nuke's Script Editor")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Install Nuke AI Panel dependencies in Nuke's Python environment",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List detected Nuke installations"
    )
    
    parser.add_argument(
        "--version",
        help="Target specific Nuke version (e.g., 14.0)"
    )
    
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only create test script, don't install packages"
    )
    
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Show manual installation instructions"
    )
    
    args = parser.parse_args()
    
    installer = NukeDependencyInstaller()
    
    print("🚀 Nuke AI Panel Dependency Installer")
    print("="*40)
    
    if args.list:
        installer.list_nuke_installations()
        return
    
    if args.manual:
        installer.list_nuke_installations()
        installer.print_installation_instructions()
        return
    
    if args.test_only:
        installer.create_test_script()
        return
    
    # Main installation process
    installer.list_nuke_installations()
    
    if not installer.nuke_installations:
        print("\n❌ No Nuke installations found!")
        print("Please ensure Nuke is installed and try again.")
        return
    
    try:
        success = installer.install_dependencies(args.version)
        
        if success:
            print("\n🎉 Installation completed successfully!")
            installer.create_test_script()
        else:
            print("\n⚠️  Installation completed with some errors.")
            print("Check the output above for details.")
            installer.print_installation_instructions()
    
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Installation failed: {e}")
        installer.print_installation_instructions()


if __name__ == "__main__":
    main()