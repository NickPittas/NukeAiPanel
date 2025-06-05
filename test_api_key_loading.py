#!/usr/bin/env python3
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
            print("\n⚠️  No API keys found in configuration.")
            print("Please configure API keys in the settings dialog first.")
            return False
        
        # Test provider manager initialization
        try:
            provider_manager = ProviderManager(config)
            print(f"\n✅ Provider manager initialized with {len(provider_manager._providers)} providers")
            
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
        print("\n🎉 API key loading test completed successfully!")
    else:
        print("\n❌ API key loading test failed!")
