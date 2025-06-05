#!/usr/bin/env python3
"""
Test script to verify the final minor fixes:
1. Ollama provider config issue (api_key parameter)
2. Missing WorkflowDatabase get_all_workflows method
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_provider_config_api_key():
    """Test that ProviderConfig now accepts api_key parameter"""
    print("🔧 Testing ProviderConfig api_key parameter fix...")
    
    try:
        from nuke_ai_panel.core.config import ProviderConfig
        
        # Test creating ProviderConfig with api_key
        config = ProviderConfig(
            name="ollama",
            enabled=True,
            api_key="test_key_123"
        )
        
        assert config.api_key == "test_key_123", "api_key not set correctly"
        assert config.name == "ollama", "name not set correctly"
        assert config.enabled == True, "enabled not set correctly"
        
        print("✅ ProviderConfig now accepts api_key parameter")
        return True
        
    except Exception as e:
        print(f"❌ ProviderConfig api_key test failed: {e}")
        return False

def test_provider_config_additional_params():
    """Test that ProviderConfig now accepts additional parameters"""
    print("🔧 Testing ProviderConfig additional parameters...")
    
    try:
        from nuke_ai_panel.core.config import ProviderConfig
        
        # Test creating ProviderConfig with additional parameters
        config = ProviderConfig(
            name="ollama",
            enabled=True,
            api_key="test_key_123",
            temperature=0.8,
            max_tokens=4000,
            base_url="http://localhost:11434"
        )
        
        assert config.api_key == "test_key_123", "api_key not set correctly"
        assert config.temperature == 0.8, "temperature not set correctly"
        assert config.max_tokens == 4000, "max_tokens not set correctly"
        assert config.base_url == "http://localhost:11434", "base_url not set correctly"
        
        print("✅ ProviderConfig now accepts additional parameters (temperature, max_tokens, base_url)")
        return True
        
    except Exception as e:
        print(f"❌ ProviderConfig additional parameters test failed: {e}")
        return False

def test_workflow_database_get_all_workflows():
    """Test that WorkflowDatabase has get_all_workflows method"""
    print("🔧 Testing WorkflowDatabase get_all_workflows method...")
    
    try:
        from src.vfx_knowledge.workflow_database import WorkflowDatabase
        
        # Create workflow database instance
        db = WorkflowDatabase()
        
        # Test get_all_workflows method
        workflows = db.get_all_workflows()
        
        assert hasattr(db, 'get_all_workflows'), "get_all_workflows method not found"
        assert isinstance(workflows, list), "get_all_workflows should return a list"
        
        print(f"✅ WorkflowDatabase.get_all_workflows() works - found {len(workflows)} workflows")
        
        # Print some workflow names for verification
        if workflows:
            workflow_names = [w.name for w in workflows[:3]]  # First 3
            print(f"   Sample workflows: {', '.join(workflow_names)}")
        
        return True
        
    except Exception as e:
        print(f"❌ WorkflowDatabase get_all_workflows test failed: {e}")
        return False

def test_ollama_config_loading():
    """Test that Ollama config can be loaded from file without errors"""
    print("🔧 Testing Ollama config loading from file...")
    
    try:
        from nuke_ai_panel.core.config import Config
        
        # Create config and try to get ollama provider config
        config = Config()
        ollama_config = config.get_provider_config("ollama")
        
        print(f"✅ Ollama config loaded successfully: {ollama_config.name}")
        print(f"   api_key: {'***' if ollama_config.api_key else 'None'}")
        print(f"   temperature: {ollama_config.temperature}")
        print(f"   max_tokens: {ollama_config.max_tokens}")
        print(f"   base_url: {ollama_config.base_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ollama config loading test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Final Minor Fixes")
    print("=" * 50)
    
    tests = [
        test_provider_config_api_key,
        test_provider_config_additional_params,
        test_workflow_database_get_all_workflows,
        test_ollama_config_loading,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
            print()
    
    # Summary
    print("=" * 50)
    print("📊 FINAL MINOR FIXES TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print()
        print("🎉 FINAL MINOR FIXES COMPLETE!")
        print("   • Ollama provider api_key parameter issue: FIXED")
        print("   • ProviderConfig additional parameters: ADDED")
        print("   • WorkflowDatabase get_all_workflows method: ADDED")
        print("   • Both error messages should no longer appear")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("   Please check the individual test results above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)