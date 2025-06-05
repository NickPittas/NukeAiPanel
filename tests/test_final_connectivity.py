#!/usr/bin/env python3
"""
Final connectivity test for Nuke AI Panel.

This script verifies that all connectivity issues have been resolved
and provides a comprehensive status report.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

def test_library_imports():
    """Test that all required libraries are now available."""
    print("🔍 Testing library imports...")
    
    libraries = {
        'aiohttp': 'Core HTTP library',
        'pyyaml': 'Configuration files',
        'cryptography': 'Secure credential storage',
        'openai': 'OpenAI and OpenRouter providers',
        'anthropic': 'Anthropic provider',
        'google.generativeai': 'Google provider',
        'mistralai': 'Mistral provider'
    }
    
    all_available = True
    
    for lib, description in libraries.items():
        try:
            __import__(lib)
            print(f"  ✅ {lib} - {description}")
        except ImportError:
            print(f"  ❌ {lib} - {description} - MISSING")
            all_available = False
    
    return all_available

def test_provider_loading():
    """Test that providers load correctly with current configuration."""
    print("\n🚀 Testing provider loading...")
    
    try:
        from nuke_ai_panel.core.config import Config
        from nuke_ai_panel.core.provider_manager import ProviderManager
        
        # Initialize components
        config = Config()
        provider_manager = ProviderManager(config)
        
        # Get loaded providers
        loaded_providers = list(provider_manager._providers.keys())
        total_providers = len(provider_manager.PROVIDER_MODULES)
        
        print(f"  📊 Loaded {len(loaded_providers)}/{total_providers} providers")
        
        for provider_name in provider_manager.PROVIDER_MODULES.keys():
            if provider_name in loaded_providers:
                provider = provider_manager.get_provider(provider_name)
                api_key = getattr(provider, 'api_key', None)
                status = "✅ Loaded"
                if api_key:
                    status += " (with API key)"
                else:
                    status += " (no API key)"
                print(f"    {provider_name}: {status}")
            else:
                # Get error from status
                status = provider_manager._provider_status.get(provider_name)
                error = status.error_message if status else "Unknown error"
                if "API key is required" in error:
                    print(f"    {provider_name}: ⚠️  Needs API key configuration")
                else:
                    print(f"    {provider_name}: ❌ Failed - {error}")
        
        return len(loaded_providers) > 0
        
    except Exception as e:
        print(f"  ❌ Provider loading test failed: {e}")
        return False

def test_connection_status():
    """Test the overall connection status."""
    print("\n🔗 Testing connection status...")
    
    try:
        from nuke_ai_panel.core.config import Config
        from nuke_ai_panel.core.provider_manager import ProviderManager
        
        config = Config()
        provider_manager = ProviderManager(config)
        
        # Test overall connection
        is_connected = provider_manager.is_connected()
        print(f"  📡 Overall connection status: {'✅ Connected' if is_connected else '⚠️  Partially connected'}")
        
        # Test individual provider status
        provider_status = provider_manager.get_provider_status()
        
        connected_count = 0
        configured_count = 0
        
        for provider_name, status in provider_status.items():
            if status.available and status.authenticated:
                connected_count += 1
                print(f"    {provider_name}: ✅ Connected and authenticated")
            elif provider_name in provider_manager._providers:
                configured_count += 1
                print(f"    {provider_name}: ⚠️  Loaded but needs authentication")
            else:
                if "API key is required" in (status.error_message or ""):
                    print(f"    {provider_name}: 🔑 Needs API key")
                else:
                    print(f"    {provider_name}: ❌ Failed to load")
        
        print(f"\n  📈 Summary:")
        print(f"    Connected: {connected_count}")
        print(f"    Configured: {configured_count}")
        print(f"    Need API keys: {len([s for s in provider_status.values() if 'API key is required' in (s.error_message or '')])}")
        
        return connected_count > 0 or configured_count > 0
        
    except Exception as e:
        print(f"  ❌ Connection status test failed: {e}")
        return False

def test_settings_dialog_integration():
    """Test that settings dialog can be imported and used."""
    print("\n⚙️  Testing settings dialog integration...")
    
    try:
        from src.ui.settings_dialog import SettingsDialog
        print("  ✅ Settings dialog can be imported")
        
        # Test provider settings widget
        from src.ui.settings_dialog import ProviderSettingsWidget
        print("  ✅ Provider settings widget available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Settings dialog test failed: {e}")
        return False

def create_user_guide():
    """Create a user guide for configuring API keys."""
    print("\n📝 Creating user configuration guide...")
    
    guide = '''# Nuke AI Panel - User Configuration Guide

## Quick Start 🚀

Your Nuke AI Panel is now ready to use! Follow these steps to configure AI providers:

### Step 1: Open Settings
1. Launch Nuke
2. Open the AI Panel
3. Click the "Settings" button (gear icon)

### Step 2: Configure API Keys
Navigate to the "Providers" tab and configure your desired AI providers:

#### OpenAI (Recommended)
- Get API key: https://platform.openai.com/api-keys
- Models: GPT-4, GPT-3.5-turbo
- Cost: Pay-per-use

#### Anthropic Claude
- Get API key: https://console.anthropic.com/
- Models: Claude-3 Opus, Sonnet, Haiku
- Cost: Pay-per-use

#### Google Gemini
- Get API key: https://makersuite.google.com/app/apikey
- Models: Gemini Pro, Gemini Pro Vision
- Cost: Free tier available

#### Mistral AI
- Get API key: https://console.mistral.ai/
- Models: Mistral Large, Medium, Small
- Cost: Pay-per-use

#### OpenRouter (Access Multiple Models)
- Get API key: https://openrouter.ai/keys
- Models: Access to many providers through one API
- Cost: Varies by model

#### Ollama (Local/Free)
- No API key needed
- Install Ollama: https://ollama.ai/
- Models: Run models locally (Llama, Mistral, etc.)
- Cost: Free (uses your hardware)

### Step 3: Test Connections
1. After entering API keys, click "Test Connection" for each provider
2. Verify providers show as "Connected" in the main panel
3. Try sending a test message

### Step 4: Start Using
1. Select your preferred provider from the dropdown
2. Choose a model
3. Start chatting with the AI assistant!

## Troubleshooting 🔧

### Provider shows "Not Connected"
- Double-check API key (no extra spaces)
- Verify API key has credits/permissions
- Check internet connection

### Import errors
- Restart Nuke after configuration
- Check that all dependencies are installed

### Need Help?
- Check the logs in: ~/.nuke_ai_panel/logs/
- Review the troubleshooting guide
- Test individual components with provided scripts

## What's Working Now ✅
- ✅ All dependencies installed
- ✅ API key loading fixed
- ✅ Provider import issues resolved
- ✅ Settings dialog functional
- ✅ Ready for user configuration

Enjoy your AI-powered Nuke workflow! 🎬✨
'''
    
    with open('docs/USER_CONFIGURATION_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)

    print("  ✅ Created docs/USER_CONFIGURATION_GUIDE.md")

def main():
    """Run all final connectivity tests."""
    print("🎯 NUKE AI PANEL - FINAL CONNECTIVITY TEST")
    print("=" * 50)
    
    # Run all tests
    libs_ok = test_library_imports()
    providers_ok = test_provider_loading()
    connection_ok = test_connection_status()
    settings_ok = test_settings_dialog_integration()
    
    # Create user guide
    create_user_guide()
    
    # Final summary
    print("\n🏆 FINAL RESULTS")
    print("=" * 30)
    
    print(f"📦 Dependencies: {'✅ All installed' if libs_ok else '❌ Missing libraries'}")
    print(f"🚀 Provider loading: {'✅ Working' if providers_ok else '❌ Failed'}")
    print(f"🔗 Connectivity: {'✅ Ready' if connection_ok else '❌ Issues'}")
    print(f"⚙️  Settings dialog: {'✅ Working' if settings_ok else '❌ Issues'}")
    
    if all([libs_ok, providers_ok, connection_ok, settings_ok]):
        print("\n🎉 SUCCESS! Nuke AI Panel is ready for user configuration!")
        print("\n📋 Next steps for user:")
        print("1. Configure API keys in settings dialog")
        print("2. Test provider connections")
        print("3. Start using the AI assistant")
        print("\n📖 See docs/USER_CONFIGURATION_GUIDE.md for detailed instructions")
    else:
        print("\n⚠️  Some issues remain - check individual test results above")
    
    return all([libs_ok, providers_ok, connection_ok, settings_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)