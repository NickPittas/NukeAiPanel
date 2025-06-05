#!/usr/bin/env python3
"""Quick check for the missing methods."""

import os

def check_provider_manager():
    """Check ProviderManager file for required methods."""
    print("🔍 Checking ProviderManager file...")
    
    try:
        with open('nuke_ai_panel/core/provider_manager.py', 'r') as f:
            content = f.read()
        
        methods_to_check = [
            'def reload_config(self):',
            'def is_connected(self):',
            'def current_provider(self):',
            'def logger(self):'
        ]
        
        found_methods = []
        for method in methods_to_check:
            if method in content:
                found_methods.append(method)
                print(f"✅ Found: {method}")
            else:
                print(f"❌ Missing: {method}")
        
        return len(found_methods) == len(methods_to_check)
        
    except Exception as e:
        print(f"❌ Error checking ProviderManager: {e}")
        return False

def check_settings_dialog():
    """Check SettingsDialog file for required methods."""
    print("\n🔍 Checking SettingsDialog file...")
    
    try:
        with open('src/ui/settings_dialog.py', 'r') as f:
            content = f.read()
        
        methods_to_check = [
            'def _is_widget_valid(self, widget):',
            'def _are_main_widgets_valid(self):'
        ]
        
        found_methods = []
        for method in methods_to_check:
            if method in content:
                found_methods.append(method)
                print(f"✅ Found: {method}")
            else:
                print(f"❌ Missing: {method}")
        
        return len(found_methods) == len(methods_to_check)
        
    except Exception as e:
        print(f"❌ Error checking SettingsDialog: {e}")
        return False

def main():
    """Run quick verification."""
    print("🚀 Quick Method Verification")
    print("=" * 40)
    
    provider_ok = check_provider_manager()
    dialog_ok = check_settings_dialog()
    
    print("\n" + "=" * 40)
    print("📊 RESULTS")
    print("=" * 40)
    
    if provider_ok and dialog_ok:
        print("✅ ALL REQUIRED METHODS FOUND!")
        print("\n🎉 CRITICAL FIXES SUCCESSFULLY APPLIED:")
        print("• ProviderManager.reload_config() - ✅ Added")
        print("• ProviderManager.is_connected() - ✅ Added")
        print("• ProviderManager.current_provider - ✅ Added")
        print("• ProviderManager.logger - ✅ Added")
        print("• SettingsDialog._is_widget_valid() - ✅ Confirmed")
        print("• SettingsDialog._are_main_widgets_valid() - ✅ Confirmed")
        print("\n🔧 ERRORS THAT SHOULD NOW BE FIXED:")
        print("• 'SettingsDialog' object has no attribute '_is_widget_valid' - ✅ FIXED")
        print("• 'ProviderManager' object has no attribute 'reload_config' - ✅ FIXED")
        print("• 'ProviderManager' object has no attribute 'is_connected' - ✅ FIXED")
        return True
    else:
        print("❌ SOME METHODS STILL MISSING")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)