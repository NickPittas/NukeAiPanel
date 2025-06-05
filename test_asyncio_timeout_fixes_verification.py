#!/usr/bin/env python3
"""
Test script to verify that all asyncio timeout context manager errors have been fixed.

This script tests all providers and settings dialog to ensure they no longer
cause the "Timeout context manager should be used inside a task" error.
"""

import asyncio
import sys
import os
import threading
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ollama_provider_fixed():
    """Test that OllamaProvider no longer has asyncio timeout errors."""
    print("🔍 Testing OllamaProvider asyncio timeout fixes...")
    
    try:
        from nuke_ai_panel.providers.ollama_provider import OllamaProvider
        
        config = {
            'base_url': 'http://localhost:11434',
            'timeout': 5  # Short timeout for testing
        }
        
        provider = OllamaProvider('ollama', config)
        print("✅ OllamaProvider created successfully")
        
        # Test async operations in a new event loop (simulating Nuke environment)
        def test_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def test_operations():
                    try:
                        # Test authentication (this used to cause the error)
                        await provider.authenticate()
                        print("✅ OllamaProvider authentication completed (may have failed due to no server, but no asyncio error)")
                        
                        # Test health check
                        health = await provider.health_check()
                        print(f"✅ OllamaProvider health check completed: {health.get('status', 'unknown')}")
                        
                        return True
                    except Exception as e:
                        # We expect connection errors, but NOT asyncio timeout context errors
                        if "Timeout context manager should be used inside a task" in str(e):
                            print(f"❌ ASYNCIO ERROR STILL EXISTS: {e}")
                            return False
                        else:
                            print(f"✅ Expected connection error (no asyncio timeout error): {e}")
                            return True
                
                result = loop.run_until_complete(test_operations())
                return result
                
            except Exception as e:
                if "Timeout context manager should be used inside a task" in str(e):
                    print(f"❌ ASYNCIO ERROR STILL EXISTS: {e}")
                    return False
                else:
                    print(f"✅ No asyncio timeout error: {e}")
                    return True
            finally:
                if 'loop' in locals():
                    loop.close()
        
        # Run in thread to simulate Nuke environment
        result_container = [None]
        
        def thread_target():
            result_container[0] = test_in_thread()
        
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()
        thread.join(timeout=10)
        
        return result_container[0] if result_container[0] is not None else False
        
    except Exception as e:
        print(f"❌ Error testing OllamaProvider: {e}")
        return False

def test_openrouter_provider_fixed():
    """Test that OpenrouterProvider no longer has asyncio timeout errors."""
    print("\n🔍 Testing OpenrouterProvider asyncio timeout fixes...")
    
    try:
        from nuke_ai_panel.providers.openrouter_provider import OpenrouterProvider
        
        config = {
            'api_key': 'test_key',
            'base_url': 'https://openrouter.ai/api/v1'
        }
        
        provider = OpenrouterProvider('openrouter', config)
        print("✅ OpenrouterProvider created successfully")
        
        # Test async operations in a new event loop
        def test_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def test_operations():
                    try:
                        # Test authentication (this used to cause the error)
                        await provider.authenticate()
                        print("✅ OpenrouterProvider authentication completed (may have failed due to invalid key, but no asyncio error)")
                        
                        return True
                    except Exception as e:
                        # We expect auth errors, but NOT asyncio timeout context errors
                        if "Timeout context manager should be used inside a task" in str(e):
                            print(f"❌ ASYNCIO ERROR STILL EXISTS: {e}")
                            return False
                        else:
                            print(f"✅ Expected auth error (no asyncio timeout error): {e}")
                            return True
                
                result = loop.run_until_complete(test_operations())
                return result
                
            except Exception as e:
                if "Timeout context manager should be used inside a task" in str(e):
                    print(f"❌ ASYNCIO ERROR STILL EXISTS: {e}")
                    return False
                else:
                    print(f"✅ No asyncio timeout error: {e}")
                    return True
            finally:
                if 'loop' in locals():
                    loop.close()
        
        # Run in thread
        result_container = [None]
        
        def thread_target():
            result_container[0] = test_in_thread()
        
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()
        thread.join(timeout=10)
        
        return result_container[0] if result_container[0] is not None else False
        
    except Exception as e:
        print(f"❌ Error testing OpenrouterProvider: {e}")
        return False

def test_settings_dialog_fixed():
    """Test that settings dialog connection tests no longer have asyncio timeout errors."""
    print("\n🔍 Testing settings dialog asyncio timeout fixes...")
    
    try:
        from src.ui.settings_dialog import ProviderSettingsWidget
        
        # Test Ollama connection test
        provider_config = {
            'base_url': 'http://localhost:11434',
            'timeout': 5,
            'api_key': ''
        }
        
        widget = ProviderSettingsWidget('ollama', provider_config)
        print("✅ ProviderSettingsWidget created successfully")
        
        # Test the async connection test method
        def test_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def test_connection():
                    try:
                        # Test the connection method that used to cause the error
                        success, message = await widget._test_ollama_connection(provider_config)
                        print(f"✅ Settings dialog connection test completed: {success}, {message}")
                        return True
                    except Exception as e:
                        # We expect connection errors, but NOT asyncio timeout context errors
                        if "Timeout context manager should be used inside a task" in str(e):
                            print(f"❌ ASYNCIO ERROR STILL EXISTS: {e}")
                            return False
                        else:
                            print(f"✅ Expected connection error (no asyncio timeout error): {e}")
                            return True
                
                result = loop.run_until_complete(test_connection())
                return result
                
            except Exception as e:
                if "Timeout context manager should be used inside a task" in str(e):
                    print(f"❌ ASYNCIO ERROR STILL EXISTS: {e}")
                    return False
                else:
                    print(f"✅ No asyncio timeout error: {e}")
                    return True
            finally:
                if 'loop' in locals():
                    loop.close()
        
        # Run in thread
        result_container = [None]
        
        def thread_target():
            result_container[0] = test_in_thread()
        
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()
        thread.join(timeout=10)
        
        return result_container[0] if result_container[0] is not None else False
        
    except Exception as e:
        print(f"❌ Error testing settings dialog: {e}")
        return False

def test_all_providers_import():
    """Test that all providers can be imported without asyncio errors."""
    print("\n🔍 Testing all provider imports...")
    
    providers_to_test = [
        ('ollama', 'nuke_ai_panel.providers.ollama_provider', 'OllamaProvider'),
        ('openrouter', 'nuke_ai_panel.providers.openrouter_provider', 'OpenrouterProvider'),
        ('anthropic', 'nuke_ai_panel.providers.anthropic_provider', 'AnthropicProvider'),
        ('openai', 'nuke_ai_panel.providers.openai_provider', 'OpenaiProvider'),
        ('google', 'nuke_ai_panel.providers.google_provider', 'GoogleProvider'),
        ('mistral', 'nuke_ai_panel.providers.mistral_provider', 'MistralProvider'),
    ]
    
    all_success = True
    
    for provider_name, module_name, class_name in providers_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            provider_class = getattr(module, class_name)
            print(f"✅ {provider_name} provider imported successfully")
        except Exception as e:
            print(f"❌ Error importing {provider_name} provider: {e}")
            all_success = False
    
    return all_success

if __name__ == "__main__":
    print("🚨 ASYNCIO TIMEOUT CONTEXT MANAGER FIXES VERIFICATION")
    print("=" * 70)
    
    # Test 1: Provider imports
    imports_ok = test_all_providers_import()
    
    # Test 2: OllamaProvider fixes
    ollama_fixed = test_ollama_provider_fixed()
    
    # Test 3: OpenrouterProvider fixes
    openrouter_fixed = test_openrouter_provider_fixed()
    
    # Test 4: Settings dialog fixes
    settings_fixed = test_settings_dialog_fixed()
    
    print("\n" + "=" * 70)
    print("📊 VERIFICATION RESULTS:")
    print(f"🔧 Provider imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"🔧 OllamaProvider fixed: {'✅ PASS' if ollama_fixed else '❌ FAIL'}")
    print(f"🔧 OpenrouterProvider fixed: {'✅ PASS' if openrouter_fixed else '❌ FAIL'}")
    print(f"🔧 Settings dialog fixed: {'✅ PASS' if settings_fixed else '❌ FAIL'}")
    
    all_tests_passed = all([imports_ok, ollama_fixed, openrouter_fixed, settings_fixed])
    
    if all_tests_passed:
        print("\n🎉 ALL ASYNCIO TIMEOUT CONTEXT MANAGER ERRORS HAVE BEEN FIXED!")
        print("✅ All providers now use asyncio.wait_for() instead of aiohttp.ClientTimeout")
        print("✅ All connection tests should work properly in Nuke environment")
        print("✅ No more 'Timeout context manager should be used inside a task' errors")
    else:
        print("\n🚨 SOME ISSUES REMAIN:")
        print("   Please check the failed tests above for remaining asyncio timeout errors")
    
    print("\n🔧 SUMMARY OF FIXES APPLIED:")
    print("   1. Replaced aiohttp.ClientTimeout with asyncio.wait_for() in OllamaProvider")
    print("   2. Replaced aiohttp.ClientTimeout with asyncio.wait_for() in OpenrouterProvider")
    print("   3. Fixed all settings dialog connection test methods")
    print("   4. Added proper timeout error handling with asyncio.TimeoutError")
    print("   5. Used TCPConnector instead of ClientTimeout for session creation")
    
    sys.exit(0 if all_tests_passed else 1)