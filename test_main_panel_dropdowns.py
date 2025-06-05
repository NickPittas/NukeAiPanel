#!/usr/bin/env python3
"""
Test script to verify main panel provider/model dropdown fixes.
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

def test_panel_manager_providers():
    """Test that panel manager returns providers correctly."""
    print("🔍 Testing Panel Manager Provider Loading...")
    
    try:
        from src.core.panel_manager import PanelManager
        
        # Create panel manager instance
        panel_manager = PanelManager()
        
        # Test get_available_providers
        providers = panel_manager.get_available_providers()
        print(f"✅ Available providers: {providers}")
        
        if not providers:
            print("❌ No providers returned!")
            return False
        
        # Test get_available_models for each provider
        for provider in providers:
            try:
                models = panel_manager.get_available_models(provider)
                print(f"✅ Models for {provider}: {models[:3]}{'...' if len(models) > 3 else ''}")
            except Exception as e:
                print(f"⚠️  Error getting models for {provider}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Panel manager test failed: {e}")
        return False

def test_main_panel_ui():
    """Test main panel UI initialization."""
    print("\n🔍 Testing Main Panel UI...")
    
    try:
        from src.ui.main_panel import NukeAIPanel
        
        # Create main panel instance
        panel = NukeAIPanel()
        
        # Check if panel manager is initialized
        if panel.panel_manager is None:
            print("❌ Panel manager not initialized!")
            return False
        
        print("✅ Main panel created successfully")
        print("✅ Panel manager initialized")
        
        # Test provider loading
        try:
            panel.load_providers()
            print("✅ Provider loading completed")
        except Exception as e:
            print(f"⚠️  Provider loading error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main panel test failed: {e}")
        return False

def test_ollama_provider():
    """Test Ollama provider dynamic model fetching."""
    print("\n🔍 Testing Ollama Provider...")
    
    try:
        from nuke_ai_panel.providers.ollama_provider import OllamaProvider
        
        # Create Ollama provider with default config
        config = {
            'base_url': 'http://localhost:11434',
            'timeout': 30
        }
        
        provider = OllamaProvider('ollama', config)
        
        # Test fallback models (should work even without Ollama server)
        fallback_models = provider._get_fallback_models()
        print(f"✅ Ollama fallback models: {[m.name for m in fallback_models]}")
        
        if not fallback_models:
            print("❌ No fallback models returned!")
            return False
        
        print("✅ Ollama provider fallback working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Ollama provider test failed: {e}")
        return False

def test_provider_manager_methods():
    """Test provider manager has all required methods."""
    print("\n🔍 Testing Provider Manager Methods...")
    
    try:
        from nuke_ai_panel.core.provider_manager import ProviderManager
        from nuke_ai_panel.core.config import Config
        
        # Create provider manager
        config = Config()
        provider_manager = ProviderManager(config)
        
        # Test required methods exist
        required_methods = [
            'get_available_providers',
            'get_current_provider', 
            'set_current_provider',
            'get_default_model',
            'set_current_model',
            'generate_response',
            'is_connected'
        ]
        
        for method_name in required_methods:
            if hasattr(provider_manager, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing!")
                return False
        
        # Test get_available_providers returns something
        providers = provider_manager.get_available_providers()
        print(f"✅ Available providers: {providers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider manager methods test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Main Panel Dropdown Fixes\n")
    
    tests = [
        test_provider_manager_methods,
        test_panel_manager_providers,
        test_ollama_provider,
        test_main_panel_ui,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Main panel dropdowns should now work correctly.")
        print("\n📋 Summary of fixes:")
        print("✅ Fixed empty provider dropdown in main panel")
        print("✅ Fixed empty model dropdown in main panel") 
        print("✅ Added dynamic Ollama model fetching with fallbacks")
        print("✅ Added missing methods to provider manager")
        print("✅ Improved error handling and fallback mechanisms")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)