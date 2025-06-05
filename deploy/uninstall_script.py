#!/usr/bin/env python3
"""
Uninstallation script for Nuke AI Panel.
Safely removes all components while preserving user data if requested.
"""

import os
import sys
import shutil
import argparse
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional
import json


class NukeAIPanelUninstaller:
    """Main uninstaller class for Nuke AI Panel."""
    
    def __init__(self):
        self.system = platform.system()
        self.user_nuke_dir = self._get_user_nuke_dir()
        self.config_dir = self._get_config_dir()
        
        # Uninstallation state
        self.removed_components = []
        self.failed_removals = []
        self.preserved_data = []
        
    def _get_user_nuke_dir(self) -> Path:
        """Get user's Nuke directory."""
        return Path.home() / ".nuke"
    
    def _get_config_dir(self) -> Path:
        """Get configuration directory."""
        return Path.home() / ".nuke_ai_panel"
    
    def detect_installation(self) -> Dict[str, bool]:
        """Detect what components are currently installed."""
        components = {
            "python_package": self._is_python_package_installed(),
            "nuke_integration": self._is_nuke_integration_installed(),
            "configuration": self._is_configuration_installed(),
            "cache": self._is_cache_present(),
            "logs": self._are_logs_present(),
            "sessions": self._are_sessions_present(),
            "desktop_shortcut": self._is_desktop_shortcut_present()
        }
        
        return components
    
    def _is_python_package_installed(self) -> bool:
        """Check if Python package is installed."""
        try:
            import nuke_ai_panel
            return True
        except ImportError:
            return False
    
    def _is_nuke_integration_installed(self) -> bool:
        """Check if Nuke integration is installed."""
        nuke_plugin_dir = self.user_nuke_dir / "nuke_ai_panel"
        return nuke_plugin_dir.exists()
    
    def _is_configuration_installed(self) -> bool:
        """Check if configuration is installed."""
        return self.config_dir.exists()
    
    def _is_cache_present(self) -> bool:
        """Check if cache data is present."""
        cache_dir = self.config_dir / "cache"
        return cache_dir.exists() and any(cache_dir.iterdir())
    
    def _are_logs_present(self) -> bool:
        """Check if log files are present."""
        log_locations = [
            self.config_dir / "logs",
            self.config_dir / "nuke_ai_panel.log",
            Path.home() / "nuke_ai_panel.log"
        ]
        
        return any(loc.exists() for loc in log_locations)
    
    def _are_sessions_present(self) -> bool:
        """Check if session data is present."""
        sessions_dir = self.config_dir / "sessions"
        return sessions_dir.exists() and any(sessions_dir.iterdir())
    
    def _is_desktop_shortcut_present(self) -> bool:
        """Check if desktop shortcut is present."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            return False
        
        shortcuts = [
            desktop / "Nuke AI Panel.lnk",  # Windows
            desktop / "nuke-ai-panel.desktop"  # Linux
        ]
        
        return any(shortcut.exists() for shortcut in shortcuts)
    
    def print_installation_status(self, components: Dict[str, bool]):
        """Print current installation status."""
        print("🔍 Current installation status:")
        print("-" * 40)
        
        for component, installed in components.items():
            status = "✅ Installed" if installed else "❌ Not found"
            print(f"   {component.replace('_', ' ').title()}: {status}")
        
        print()
    
    def backup_user_data(self, backup_dir: Path) -> bool:
        """Backup user data before uninstallation."""
        print(f"💾 Backing up user data to {backup_dir}...")
        
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration
            if self.config_dir.exists():
                config_backup = backup_dir / "config"
                shutil.copytree(self.config_dir, config_backup, ignore=shutil.ignore_patterns("cache", "*.log"))
                print("✅ Configuration backed up")
                self.preserved_data.append("configuration")
            
            # Backup sessions
            sessions_dir = self.config_dir / "sessions"
            if sessions_dir.exists():
                sessions_backup = backup_dir / "sessions"
                shutil.copytree(sessions_dir, sessions_backup)
                print("✅ Sessions backed up")
                self.preserved_data.append("sessions")
            
            # Backup custom workflows/templates
            custom_dir = self.config_dir / "custom"
            if custom_dir.exists():
                custom_backup = backup_dir / "custom"
                shutil.copytree(custom_dir, custom_backup)
                print("✅ Custom data backed up")
                self.preserved_data.append("custom_data")
            
            return True
            
        except Exception as e:
            print(f"❌ Error backing up user data: {e}")
            return False
    
    def remove_python_package(self) -> bool:
        """Remove the Python package."""
        print("📦 Removing Python package...")
        
        try:
            # Try to uninstall using pip
            cmd = [sys.executable, "-m", "pip", "uninstall", "nuke-ai-panel", "-y"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Python package removed successfully")
                self.removed_components.append("python_package")
                return True
            else:
                # Package might not be installed via pip (development install)
                print("⚠️  Package not found in pip, checking for development install...")
                
                # Try to find and remove development install
                try:
                    import nuke_ai_panel
                    package_path = Path(nuke_ai_panel.__file__).parent.parent
                    if package_path.name == "nuke-ai-panel" or "nuke_ai_panel" in str(package_path):
                        print(f"Found development install at: {package_path}")
                        print("⚠️  Development install detected - manual removal may be needed")
                except ImportError:
                    print("✅ Python package already removed")
                
                self.removed_components.append("python_package")
                return True
                
        except Exception as e:
            print(f"❌ Error removing Python package: {e}")
            self.failed_removals.append("python_package")
            return False
    
    def remove_nuke_integration(self) -> bool:
        """Remove Nuke integration."""
        print("🎬 Removing Nuke integration...")
        
        try:
            # Remove plugin directory
            nuke_plugin_dir = self.user_nuke_dir / "nuke_ai_panel"
            if nuke_plugin_dir.exists():
                shutil.rmtree(nuke_plugin_dir)
                print("✅ Plugin directory removed")
            
            # Clean up menu.py
            self._cleanup_menu_integration()
            
            # Clean up init.py
            self._cleanup_init_integration()
            
            print("✅ Nuke integration removed successfully")
            self.removed_components.append("nuke_integration")
            return True
            
        except Exception as e:
            print(f"❌ Error removing Nuke integration: {e}")
            self.failed_removals.append("nuke_integration")
            return False
    
    def _cleanup_menu_integration(self):
        """Clean up menu.py integration."""
        menu_file = self.user_nuke_dir / "menu.py"
        
        if not menu_file.exists():
            return
        
        try:
            with open(menu_file, 'r') as f:
                content = f.read()
            
            # Remove AI Panel integration
            lines = content.split('\n')
            cleaned_lines = []
            skip_section = False
            
            for line in lines:
                if "=== Nuke AI Panel Integration ===" in line:
                    skip_section = True
                    continue
                elif skip_section and (line.strip() == "" or line.startswith('#')):
                    continue
                elif skip_section and not line.startswith(' ') and not line.startswith('\t'):
                    skip_section = False
                
                if not skip_section:
                    cleaned_lines.append(line)
            
            # Write cleaned content back
            with open(menu_file, 'w') as f:
                f.write('\n'.join(cleaned_lines))
            
            print("✅ Menu integration cleaned up")
            
        except Exception as e:
            print(f"⚠️  Could not clean up menu.py: {e}")
    
    def _cleanup_init_integration(self):
        """Clean up init.py integration."""
        init_file = self.user_nuke_dir / "init.py"
        
        if not init_file.exists():
            return
        
        try:
            with open(init_file, 'r') as f:
                content = f.read()
            
            # Remove AI Panel initialization
            lines = content.split('\n')
            cleaned_lines = []
            skip_section = False
            
            for line in lines:
                if "Nuke AI Panel Initialization" in line:
                    skip_section = True
                    continue
                elif skip_section and "NUKE_AI_PANEL" in line:
                    continue
                elif skip_section and line.strip() == "":
                    continue
                else:
                    skip_section = False
                
                if not skip_section:
                    cleaned_lines.append(line)
            
            # Write cleaned content back
            with open(init_file, 'w') as f:
                f.write('\n'.join(cleaned_lines))
            
            print("✅ Init integration cleaned up")
            
        except Exception as e:
            print(f"⚠️  Could not clean up init.py: {e}")
    
    def remove_configuration(self, preserve_user_data: bool = True) -> bool:
        """Remove configuration files."""
        print("⚙️  Removing configuration...")
        
        try:
            if not self.config_dir.exists():
                print("✅ Configuration already removed")
                self.removed_components.append("configuration")
                return True
            
            if preserve_user_data:
                # Remove only non-user data
                items_to_remove = ["cache", "logs", "*.log"]
                
                for item in items_to_remove:
                    if "*" in item:
                        # Handle wildcards
                        for path in self.config_dir.glob(item):
                            if path.is_file():
                                path.unlink()
                            elif path.is_dir():
                                shutil.rmtree(path)
                    else:
                        path = self.config_dir / item
                        if path.exists():
                            if path.is_file():
                                path.unlink()
                            elif path.is_dir():
                                shutil.rmtree(path)
                
                print("✅ Configuration cleaned (user data preserved)")
            else:
                # Remove entire configuration directory
                shutil.rmtree(self.config_dir)
                print("✅ Configuration removed completely")
            
            self.removed_components.append("configuration")
            return True
            
        except Exception as e:
            print(f"❌ Error removing configuration: {e}")
            self.failed_removals.append("configuration")
            return False
    
    def remove_cache(self) -> bool:
        """Remove cache data."""
        print("🗑️  Removing cache data...")
        
        try:
            cache_locations = [
                self.config_dir / "cache",
                Path.home() / ".cache" / "nuke_ai_panel"
            ]
            
            removed_any = False
            for cache_dir in cache_locations:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    print(f"✅ Removed cache: {cache_dir}")
                    removed_any = True
            
            if not removed_any:
                print("✅ No cache data found")
            
            self.removed_components.append("cache")
            return True
            
        except Exception as e:
            print(f"❌ Error removing cache: {e}")
            self.failed_removals.append("cache")
            return False
    
    def remove_logs(self) -> bool:
        """Remove log files."""
        print("📝 Removing log files...")
        
        try:
            log_locations = [
                self.config_dir / "logs",
                self.config_dir / "nuke_ai_panel.log",
                Path.home() / "nuke_ai_panel.log",
                Path("/tmp") / "nuke_ai_panel.log"
            ]
            
            removed_any = False
            for log_path in log_locations:
                if log_path.exists():
                    if log_path.is_file():
                        log_path.unlink()
                    elif log_path.is_dir():
                        shutil.rmtree(log_path)
                    print(f"✅ Removed logs: {log_path}")
                    removed_any = True
            
            if not removed_any:
                print("✅ No log files found")
            
            self.removed_components.append("logs")
            return True
            
        except Exception as e:
            print(f"❌ Error removing logs: {e}")
            self.failed_removals.append("logs")
            return False
    
    def remove_desktop_shortcut(self) -> bool:
        """Remove desktop shortcut."""
        print("🖥️  Removing desktop shortcut...")
        
        try:
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                print("✅ No desktop directory found")
                self.removed_components.append("desktop_shortcut")
                return True
            
            shortcuts = [
                desktop / "Nuke AI Panel.lnk",  # Windows
                desktop / "nuke-ai-panel.desktop"  # Linux
            ]
            
            removed_any = False
            for shortcut in shortcuts:
                if shortcut.exists():
                    shortcut.unlink()
                    print(f"✅ Removed shortcut: {shortcut.name}")
                    removed_any = True
            
            if not removed_any:
                print("✅ No desktop shortcuts found")
            
            self.removed_components.append("desktop_shortcut")
            return True
            
        except Exception as e:
            print(f"❌ Error removing desktop shortcut: {e}")
            self.failed_removals.append("desktop_shortcut")
            return False
    
    def clean_environment_variables(self) -> bool:
        """Clean up environment variables (informational)."""
        print("🌍 Environment variables cleanup...")
        
        env_vars = [
            "NUKE_AI_PANEL_CONFIG_DIR",
            "NUKE_AI_PANEL_LOG_LEVEL",
            "NUKE_AI_PANEL_CACHE_DIR"
        ]
        
        found_vars = []
        for var in env_vars:
            if var in os.environ:
                found_vars.append(var)
        
        if found_vars:
            print("⚠️  Found environment variables that should be removed manually:")
            for var in found_vars:
                print(f"   • {var}")
            print("   Remove these from your shell profile (.bashrc, .zshrc, etc.)")
        else:
            print("✅ No environment variables found")
        
        return True
    
    def print_uninstall_summary(self):
        """Print uninstallation summary."""
        print("\n" + "="*60)
        print("🗑️  UNINSTALLATION SUMMARY")
        print("="*60)
        
        if self.removed_components:
            print("\n✅ Successfully removed:")
            for component in self.removed_components:
                print(f"   • {component.replace('_', ' ').title()}")
        
        if self.failed_removals:
            print("\n❌ Failed to remove:")
            for component in self.failed_removals:
                print(f"   • {component.replace('_', ' ').title()}")
        
        if self.preserved_data:
            print("\n💾 Preserved data:")
            for data in self.preserved_data:
                print(f"   • {data.replace('_', ' ').title()}")
        
        print(f"\n📁 Manual cleanup may be needed for:")
        print(f"   • Environment variables in shell profiles")
        print(f"   • Any custom integrations or scripts")
        
        if self.failed_removals:
            print(f"\n⚠️  Some components could not be removed automatically.")
            print(f"   You may need to remove them manually.")
        else:
            print(f"\n🎉 Nuke AI Panel has been successfully uninstalled!")
    
    def uninstall(self, args):
        """Run the complete uninstallation process."""
        print("🗑️  Starting Nuke AI Panel uninstallation...")
        
        # Detect current installation
        components = self.detect_installation()
        self.print_installation_status(components)
        
        if not any(components.values()):
            print("✅ Nuke AI Panel is not installed or already removed.")
            return True
        
        # Confirm uninstallation
        if args.interactive:
            print("This will remove Nuke AI Panel from your system.")
            if args.preserve_data:
                print("User data (sessions, custom settings) will be preserved.")
            else:
                print("⚠️  ALL data including sessions and settings will be removed!")
            
            confirm = input("\nProceed with uninstallation? (y/N): ").lower().strip()
            if confirm != 'y':
                print("❌ Uninstallation cancelled.")
                return False
        
        # Backup user data if requested
        if args.backup_data:
            backup_dir = Path.home() / "nuke_ai_panel_backup"
            if not self.backup_user_data(backup_dir):
                if args.interactive:
                    continue_anyway = input("Backup failed. Continue anyway? (y/N): ").lower().strip()
                    if continue_anyway != 'y':
                        print("❌ Uninstallation cancelled.")
                        return False
        
        # Remove components
        success = True
        
        if components["python_package"] and not args.keep_python_package:
            success &= self.remove_python_package()
        
        if components["nuke_integration"]:
            success &= self.remove_nuke_integration()
        
        if components["cache"]:
            success &= self.remove_cache()
        
        if components["logs"]:
            success &= self.remove_logs()
        
        if components["desktop_shortcut"]:
            success &= self.remove_desktop_shortcut()
        
        if components["configuration"]:
            success &= self.remove_configuration(args.preserve_data)
        
        # Clean environment variables
        self.clean_environment_variables()
        
        # Print summary
        self.print_uninstall_summary()
        
        return success


def main():
    """Main uninstallation function."""
    parser = argparse.ArgumentParser(
        description="Uninstall Nuke AI Panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python uninstall_script.py                    # Interactive uninstall
  python uninstall_script.py --preserve-data   # Keep user data
  python uninstall_script.py --backup-data     # Backup before removal
  python uninstall_script.py --complete        # Remove everything
        """
    )
    
    parser.add_argument(
        "--preserve-data",
        action="store_true",
        default=True,
        help="Preserve user data (sessions, settings)"
    )
    
    parser.add_argument(
        "--complete",
        action="store_true",
        help="Complete removal including all user data"
    )
    
    parser.add_argument(
        "--backup-data",
        action="store_true",
        help="Backup user data before removal"
    )
    
    parser.add_argument(
        "--keep-python-package",
        action="store_true",
        help="Keep Python package installed"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Interactive uninstallation (default)"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive uninstallation"
    )
    
    args = parser.parse_args()
    
    # Handle argument conflicts
    if args.complete:
        args.preserve_data = False
    
    if args.non_interactive:
        args.interactive = False
    
    # Create uninstaller and run
    uninstaller = NukeAIPanelUninstaller()
    
    try:
        success = uninstaller.uninstall(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Uninstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Uninstallation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()