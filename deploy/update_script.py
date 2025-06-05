#!/usr/bin/env python3
"""
Update script for Nuke AI Panel.
Handles version updates, rollbacks, and migration of user data.
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
from datetime import datetime
import hashlib


class NukeAIPanelUpdater:
    """Main updater class for Nuke AI Panel."""
    
    def __init__(self):
        self.system = platform.system()
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parent
        
        # Paths
        self.user_nuke_dir = self._get_user_nuke_dir()
        self.config_dir = self._get_config_dir()
        self.backup_dir = self.config_dir / "backups"
        
        # Version tracking
        self.current_version = self._get_current_version()
        self.available_version = self._get_available_version()
        
        # Update state
        self.backup_created = False
        self.update_successful = False
        self.rollback_available = False
        
    def _get_user_nuke_dir(self) -> Path:
        """Get user's Nuke directory."""
        return Path.home() / ".nuke"
    
    def _get_config_dir(self) -> Path:
        """Get configuration directory."""
        return Path.home() / ".nuke_ai_panel"
    
    def _get_current_version(self) -> Optional[str]:
        """Get currently installed version."""
        try:
            import nuke_ai_panel
            return getattr(nuke_ai_panel, '__version__', None)
        except ImportError:
            return None
    
    def _get_available_version(self) -> Optional[str]:
        """Get available version from project."""
        try:
            # Try to read version from setup.py or __init__.py
            setup_file = self.project_root / "setup.py"
            if setup_file.exists():
                with open(setup_file, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
            
            # Try __init__.py
            init_file = self.project_root / "nuke_ai_panel" / "__init__.py"
            if init_file.exists():
                with open(init_file, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
            
            return "unknown"
            
        except Exception:
            return None
    
    def check_update_available(self) -> bool:
        """Check if an update is available."""
        if not self.current_version or not self.available_version:
            return True  # Assume update needed if versions unknown
        
        return self.current_version != self.available_version
    
    def create_backup(self) -> bool:
        """Create backup of current installation."""
        print("💾 Creating backup of current installation...")
        
        try:
            # Create backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{self.current_version or 'unknown'}_{timestamp}"
            current_backup_dir = self.backup_dir / backup_name
            current_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup Nuke integration
            nuke_plugin_dir = self.user_nuke_dir / "nuke_ai_panel"
            if nuke_plugin_dir.exists():
                nuke_backup = current_backup_dir / "nuke_integration"
                shutil.copytree(nuke_plugin_dir, nuke_backup)
                print("✅ Nuke integration backed up")
            
            # Backup configuration (excluding cache and logs)
            if self.config_dir.exists():
                config_backup = current_backup_dir / "config"
                config_backup.mkdir(exist_ok=True)
                
                for item in self.config_dir.iterdir():
                    if item.name not in ["cache", "logs", "backups"] and not item.name.endswith(".log"):
                        if item.is_file():
                            shutil.copy2(item, config_backup)
                        elif item.is_dir():
                            shutil.copytree(item, config_backup / item.name)
                
                print("✅ Configuration backed up")
            
            # Backup Python package info
            try:
                import nuke_ai_panel
                package_info = {
                    "version": self.current_version,
                    "install_path": str(Path(nuke_ai_panel.__file__).parent),
                    "backup_timestamp": timestamp
                }
                
                with open(current_backup_dir / "package_info.json", 'w') as f:
                    json.dump(package_info, f, indent=2)
                
                print("✅ Package info backed up")
            except ImportError:
                pass
            
            # Create backup manifest
            manifest = {
                "backup_date": datetime.now().isoformat(),
                "original_version": self.current_version,
                "system": self.system,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "components": {
                    "nuke_integration": nuke_plugin_dir.exists(),
                    "configuration": self.config_dir.exists(),
                    "python_package": self.current_version is not None
                }
            }
            
            with open(current_backup_dir / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.backup_created = True
            self.current_backup_dir = current_backup_dir
            print(f"✅ Backup created: {current_backup_dir}")
            
            # Clean up old backups (keep last 5)
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Clean up old backup directories."""
        try:
            if not self.backup_dir.exists():
                return
            
            # Get all backup directories
            backups = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Remove old backups (keep last 5)
            for old_backup in backups[5:]:
                shutil.rmtree(old_backup)
                print(f"🗑️  Removed old backup: {old_backup.name}")
                
        except Exception as e:
            print(f"⚠️  Could not clean up old backups: {e}")
    
    def update_python_package(self) -> bool:
        """Update the Python package."""
        print("📦 Updating Python package...")
        
        try:
            # Uninstall current version
            cmd = [sys.executable, "-m", "pip", "uninstall", "nuke-ai-panel", "-y"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Install new version
            cmd = [sys.executable, "-m", "pip", "install", "-e", str(self.project_root)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Python package updated successfully")
                return True
            else:
                print(f"❌ Failed to update Python package: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating Python package: {e}")
            return False
    
    def update_nuke_integration(self) -> bool:
        """Update Nuke integration files."""
        print("🎬 Updating Nuke integration...")
        
        try:
            src_dir = self.project_root / "src"
            nuke_plugin_dir = self.user_nuke_dir / "nuke_ai_panel"
            
            if not src_dir.exists():
                print("❌ Source directory not found")
                return False
            
            # Remove old integration
            if nuke_plugin_dir.exists():
                shutil.rmtree(nuke_plugin_dir)
            
            # Copy new integration
            shutil.copytree(src_dir, nuke_plugin_dir)
            
            print("✅ Nuke integration updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating Nuke integration: {e}")
            return False
    
    def migrate_configuration(self) -> bool:
        """Migrate configuration to new version if needed."""
        print("⚙️  Checking configuration migration...")
        
        try:
            config_file = self.config_dir / "config.yaml"
            if not config_file.exists():
                print("✅ No configuration to migrate")
                return True
            
            # Load current configuration
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check if migration is needed
            config_version = config.get('version', '0.1')
            target_version = '1.0'  # Current config version
            
            if config_version == target_version:
                print("✅ Configuration is up to date")
                return True
            
            print(f"🔄 Migrating configuration from {config_version} to {target_version}")
            
            # Perform migration
            migrated_config = self._migrate_config_structure(config, config_version, target_version)
            
            # Backup original config
            backup_config = config_file.with_suffix('.yaml.backup')
            shutil.copy2(config_file, backup_config)
            
            # Write migrated config
            with open(config_file, 'w') as f:
                yaml.dump(migrated_config, f, default_flow_style=False, indent=2)
            
            print("✅ Configuration migrated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error migrating configuration: {e}")
            return False
    
    def _migrate_config_structure(self, config: Dict, from_version: str, to_version: str) -> Dict:
        """Migrate configuration structure between versions."""
        migrated = config.copy()
        
        # Update version
        migrated['version'] = to_version
        
        # Add new sections if they don't exist
        if 'security' not in migrated:
            migrated['security'] = {
                'encrypt_cache': True,
                'api_key_rotation_days': 90,
                'max_failed_auth_attempts': 5,
                'session_timeout_minutes': 60
            }
        
        if 'performance' not in migrated:
            migrated['performance'] = {
                'connection_pool_size': 10,
                'connection_timeout': 30,
                'read_timeout': 60,
                'max_concurrent_requests': 5
            }
        
        # Migrate provider configurations
        if 'providers' in migrated:
            for provider_name, provider_config in migrated['providers'].items():
                # Add new provider settings
                if 'cost_tracking' not in provider_config:
                    provider_config['cost_tracking'] = True
                
                if 'daily_cost_limit' not in provider_config:
                    provider_config['daily_cost_limit'] = None
        
        return migrated
    
    def update_dependencies(self) -> bool:
        """Update dependencies."""
        print("📚 Updating dependencies...")
        
        try:
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--upgrade"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Dependencies updated successfully")
                    return True
                else:
                    print(f"❌ Failed to update dependencies: {result.stderr}")
                    return False
            else:
                print("⚠️  requirements.txt not found, skipping dependency update")
                return True
                
        except Exception as e:
            print(f"❌ Error updating dependencies: {e}")
            return False
    
    def verify_update(self) -> bool:
        """Verify that the update was successful."""
        print("🔍 Verifying update...")
        
        try:
            # Test Python package import
            import importlib
            import nuke_ai_panel
            importlib.reload(nuke_ai_panel)
            
            new_version = getattr(nuke_ai_panel, '__version__', 'unknown')
            print(f"✅ New version: {new_version}")
            
            # Test configuration loading
            from nuke_ai_panel.core.config import Config
            config = Config()
            print("✅ Configuration loading successful")
            
            # Test provider manager
            from nuke_ai_panel.core.provider_manager import ProviderManager
            provider_manager = ProviderManager(config=config)
            print("✅ Provider manager initialization successful")
            
            self.update_successful = True
            print("✅ Update verification successful")
            return True
            
        except Exception as e:
            print(f"❌ Update verification failed: {e}")
            return False
    
    def rollback(self, backup_name: Optional[str] = None) -> bool:
        """Rollback to a previous version."""
        print("🔄 Rolling back to previous version...")
        
        try:
            # Find backup to restore
            if backup_name:
                backup_path = self.backup_dir / backup_name
            else:
                # Use most recent backup
                backups = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
                if not backups:
                    print("❌ No backups found for rollback")
                    return False
                
                backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
                backup_path = backups[0]
            
            if not backup_path.exists():
                print(f"❌ Backup not found: {backup_path}")
                return False
            
            print(f"📦 Restoring from backup: {backup_path.name}")
            
            # Load backup manifest
            manifest_file = backup_path / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                print(f"🔄 Rolling back to version: {manifest.get('original_version', 'unknown')}")
            
            # Restore Nuke integration
            nuke_backup = backup_path / "nuke_integration"
            if nuke_backup.exists():
                nuke_plugin_dir = self.user_nuke_dir / "nuke_ai_panel"
                if nuke_plugin_dir.exists():
                    shutil.rmtree(nuke_plugin_dir)
                shutil.copytree(nuke_backup, nuke_plugin_dir)
                print("✅ Nuke integration restored")
            
            # Restore configuration
            config_backup = backup_path / "config"
            if config_backup.exists():
                # Backup current config first
                current_config = self.config_dir / "config.yaml"
                if current_config.exists():
                    shutil.copy2(current_config, current_config.with_suffix('.yaml.rollback'))
                
                # Restore backed up config
                for item in config_backup.iterdir():
                    dest = self.config_dir / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                
                print("✅ Configuration restored")
            
            # Note: Python package rollback would require specific version installation
            print("⚠️  Python package rollback requires manual intervention")
            print("   Run: pip install nuke-ai-panel==<version>")
            
            print("✅ Rollback completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during rollback: {e}")
            return False
    
    def list_backups(self):
        """List available backups."""
        print("📋 Available backups:")
        
        if not self.backup_dir.exists():
            print("   No backups found")
            return
        
        backups = [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
        
        if not backups:
            print("   No backups found")
            return
        
        backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        
        for backup in backups:
            manifest_file = backup / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    
                    backup_date = manifest.get('backup_date', 'unknown')
                    version = manifest.get('original_version', 'unknown')
                    
                    print(f"   • {backup.name}")
                    print(f"     Version: {version}")
                    print(f"     Date: {backup_date}")
                    print()
                except Exception:
                    print(f"   • {backup.name} (manifest corrupted)")
            else:
                print(f"   • {backup.name} (no manifest)")
    
    def print_update_summary(self):
        """Print update summary."""
        print("\n" + "="*60)
        print("🔄 UPDATE SUMMARY")
        print("="*60)
        
        print(f"\n📊 Version Information:")
        print(f"   Previous version: {self.current_version or 'unknown'}")
        print(f"   New version: {self.available_version or 'unknown'}")
        
        if self.backup_created:
            print(f"\n💾 Backup Information:")
            print(f"   Backup created: ✅")
            print(f"   Backup location: {self.current_backup_dir}")
        
        if self.update_successful:
            print(f"\n✅ Update Status: SUCCESS")
            print(f"   All components updated successfully")
            print(f"   Verification passed")
        else:
            print(f"\n❌ Update Status: FAILED")
            print(f"   Some components may not have updated correctly")
            if self.backup_created:
                print(f"   Rollback available using: python update_script.py --rollback")
        
        print(f"\n🚀 Next Steps:")
        if self.update_successful:
            print("   1. Restart Nuke to use the updated panel")
            print("   2. Check that all features work as expected")
            print("   3. Review any new configuration options")
        else:
            print("   1. Check the error messages above")
            print("   2. Consider rolling back if issues persist")
            print("   3. Check the troubleshooting guide")
    
    def update(self, args):
        """Run the complete update process."""
        print("🔄 Starting Nuke AI Panel update...")
        print(f"   Current version: {self.current_version or 'unknown'}")
        print(f"   Available version: {self.available_version or 'unknown'}")
        
        # Check if update is needed
        if not args.force and not self.check_update_available():
            print("✅ Already up to date!")
            return True
        
        # Confirm update
        if args.interactive:
            print(f"\nThis will update Nuke AI Panel to version {self.available_version}")
            confirm = input("Proceed with update? (Y/n): ").lower().strip()
            if confirm == 'n':
                print("❌ Update cancelled.")
                return False
        
        # Create backup
        if not args.no_backup:
            if not self.create_backup():
                if args.interactive:
                    continue_anyway = input("Backup failed. Continue anyway? (y/N): ").lower().strip()
                    if continue_anyway != 'y':
                        print("❌ Update cancelled.")
                        return False
        
        # Perform update
        success = True
        
        if not args.no_python_package:
            success &= self.update_python_package()
        
        if not args.no_dependencies:
            success &= self.update_dependencies()
        
        if not args.no_nuke_integration:
            success &= self.update_nuke_integration()
        
        if not args.no_config_migration:
            success &= self.migrate_configuration()
        
        # Verify update
        if success:
            success &= self.verify_update()
        
        # Print summary
        self.print_update_summary()
        
        return success


def main():
    """Main update function."""
    parser = argparse.ArgumentParser(
        description="Update Nuke AI Panel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_script.py                    # Standard update
  python update_script.py --force           # Force update even if up to date
  python update_script.py --rollback        # Rollback to previous version
  python update_script.py --list-backups    # List available backups
        """
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update even if already up to date"
    )
    
    parser.add_argument(
        "--rollback",
        nargs="?",
        const=True,
        help="Rollback to previous version (optionally specify backup name)"
    )
    
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List available backups"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before update"
    )
    
    parser.add_argument(
        "--no-python-package",
        action="store_true",
        help="Skip Python package update"
    )
    
    parser.add_argument(
        "--no-dependencies",
        action="store_true",
        help="Skip dependency updates"
    )
    
    parser.add_argument(
        "--no-nuke-integration",
        action="store_true",
        help="Skip Nuke integration update"
    )
    
    parser.add_argument(
        "--no-config-migration",
        action="store_true",
        help="Skip configuration migration"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Interactive update (default)"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Non-interactive update"
    )
    
    args = parser.parse_args()
    
    if args.non_interactive:
        args.interactive = False
    
    # Create updater
    updater = NukeAIPanelUpdater()
    
    try:
        # Handle special commands
        if args.list_backups:
            updater.list_backups()
            sys.exit(0)
        
        if args.rollback:
            backup_name = args.rollback if isinstance(args.rollback, str) else None
            success = updater.rollback(backup_name)
            sys.exit(0 if success else 1)
        
        # Perform update
        success = updater.update(args)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n❌ Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Update failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()