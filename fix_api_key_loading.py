#!/usr/bin/env python3
"""
Fix for API key loading issue in Nuke AI Panel.

This script fixes the issue where API keys saved in the settings dialog
are not being properly loaded by the provider manager.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

def fix_provider_manager_api_key_loading():
    """Fix the provider manager to properly load API keys from configuration."""
    
    print("Fixing provider manager API key loading...")
    
    # Read the current provider manager
    provider_manager_path = Path("nuke_ai_panel/core/provider_manager.py")
    
    if not provider_manager_path.exists():
        print("❌ Provider manager file not found")
        return False
    
    with open(provider_manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if "# API key loading fix applied" in content:
        print("✅ API key loading fix already applied")
        return True
    
    # Find the _load_provider method and fix the configuration merging
    old_merge_code = """            # Merge configurations
            full_config = {**provider_config.__dict__, **auth_config}"""
    
    new_merge_code = """            # Merge configurations with proper API key handling
            # API key loading fix applied
            full_config = {**provider_config.__dict__, **auth_config}
            
            # Ensure API key is properly loaded from config
            if not full_config.get('api_key') and hasattr(provider_config, 'api_key') and provider_config.api_key:
                full_config['api_key'] = provider_config.api_key
            
            # Also check for base_url mapping
            if hasattr(provider_config, 'base_url') and provider_config.base_url:
                full_config['base_url'] = provider_config.base_url
            elif hasattr(provider_config, 'custom_endpoint') and provider_config.custom_endpoint:
                full_config['base_url'] = provider_config.custom_endpoint"""
    
    if old_merge_code in content:
        content = content.replace(old_merge_code, new_merge_code)
        
        # Write the fixed content back
        with open(provider_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed provider manager API key loading")
        return True
    else:
        print("⚠️  Could not find the exact code to replace in provider manager")
        return False

def fix_config_api_key_support():
    """Ensure the configuration properly supports API keys in provider configs."""
    
    print("Checking configuration API key support...")
    
    config_path = Path("nuke_ai_panel/core/config.py")
    
    if not config_path.exists():
        print("❌ Config file not found")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if API key support is already there
    if "api_key: Optional[str] = None" in content:
        print("✅ Configuration already supports API keys")
        return True
    else:
        print("⚠️  Configuration API key support needs to be added manually")
        return False

def create_api_key_test_script():
    """Create a script to test API key loading."""
    
    test_script = '''#!/usr/bin/env python3
"""
Test script to verify API key loading is working correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

def test_api_key_loading():
    """Test that API keys are properly loaded from configuration."""
    
    try:
        from nuke_ai_panel.core.config import Config
        from nuke_ai_panel.core.provider_manager import ProviderManager
        
        print("Testing API key loading...")
        
        # Initialize config
        config = Config()
        
        # Check if we have any API keys configured
        providers_with_keys = []
        for provider in ['openai', 'anthropic', 'google', 'mistral', 'ollama', 'openrouter']:
            provider_config = config.get_provider_config(provider)
            if provider_config.api_key:
                providers_with_keys.append(provider)
                print(f"✅ {provider}: API key found in config")
            else:
                print(f"❌ {provider}: No API key in config")
        
        if not providers_with_keys:
            print("\\n⚠️  No API keys found in configuration.")
            print("Please configure API keys in the settings dialog first.")
            return False
        
        # Test provider manager initialization
        try:
            provider_manager = ProviderManager(config)
            print(f"\\n✅ Provider manager initialized with {len(provider_manager._providers)} providers")
            
            # Check which providers loaded successfully
            for provider_name in providers_with_keys:
                provider = provider_manager.get_provider(provider_name)
                if provider:
                    api_key = getattr(provider, 'api_key', None)
                    if api_key:
                        print(f"✅ {provider_name}: Provider loaded with API key")
                    else:
                        print(f"❌ {provider_name}: Provider loaded but no API key")
                else:
                    print(f"❌ {provider_name}: Provider failed to load")
            
            return True
            
        except Exception as e:
            print(f"❌ Provider manager initialization failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key_loading()
    if success:
        print("\\n🎉 API key loading test completed successfully!")
    else:
        print("\\n❌ API key loading test failed!")
'''
    
    with open('tests/test_api_key_loading.py', 'w', encoding='utf-8') as f:
        f.write(test_script)

    print("✅ Created tests/test_api_key_loading.py")

def main():
    """Apply all API key loading fixes."""
    
    print("🔧 FIXING API KEY LOADING ISSUES")
    print("=" * 40)
    
    # Apply fixes
    fix1 = fix_provider_manager_api_key_loading()
    fix2 = fix_config_api_key_support()
    
    # Create test script
    create_api_key_test_script()
    
    print("\\n📋 SUMMARY:")
    print(f"Provider manager fix: {'✅ Applied' if fix1 else '❌ Failed'}")
    print(f"Config API key support: {'✅ OK' if fix2 else '⚠️  Manual check needed'}")
    
    print("\\n🎯 NEXT STEPS:")
    print("1. Install dependencies: python install_dependencies.py")
    print("2. Test API key loading: python tests/test_api_key_loading.py")
    print("3. Configure API keys in settings dialog")
    print("4. Test provider connections")

if __name__ == "__main__":
    main()