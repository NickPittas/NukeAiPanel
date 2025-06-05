#!/usr/bin/env python3
"""
Test script to verify and fix Ollama authentication issues.

This script tests:
1. Ollama provider authentication without API key
2. Connection test functionality
3. Text generation authentication
4. Base URL configuration
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_ollama_authentication():
    """Test Ollama authentication and connection functionality."""
    print("🔧 Testing Ollama Authentication Fix")
    print("=" * 50)
    
    try:
        # Import required modules
        from nuke_ai_panel.providers.ollama_provider import OllamaProvider
        from nuke_ai_panel.core.base_provider import Message, MessageRole, GenerationConfig
        
        # Test 1: Provider initialization
        print("\n1️⃣ Testing Provider Initialization...")
        config = {
            'base_url': 'http://localhost:11434',
            'timeout': 30,
            # No API key - should work without it
        }
        
        provider = OllamaProvider('ollama', config)
        print(f"✅ Provider initialized with base_url: {provider.base_url}")
        print(f"✅ API key: {'Set' if provider.api_key else 'Not set (expected for local Ollama)'}")
        
        # Test 2: Authentication without API key
        print("\n2️⃣ Testing Authentication (without API key)...")
        try:
            auth_result = await provider.authenticate()
            print(f"✅ Authentication result: {auth_result}")
            print(f"✅ Provider authenticated flag: {provider.is_authenticated}")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("   This indicates the server is not running or not accessible")
            return False
        
        # Test 3: Health check
        print("\n3️⃣ Testing Health Check...")
        try:
            health = await provider.health_check()
            print(f"✅ Health check status: {health.get('status')}")
            print(f"✅ Models available: {health.get('models_available', 0)}")
            print(f"✅ Authenticated: {health.get('authenticated')}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # Test 4: Get models
        print("\n4️⃣ Testing Get Models...")
        try:
            models = await provider.get_models()
            print(f"✅ Found {len(models)} models")
            for model in models[:3]:  # Show first 3 models
                print(f"   - {model.name}: {model.description}")
        except Exception as e:
            print(f"❌ Get models failed: {e}")
        
        # Test 5: Text generation (if authenticated)
        if provider.is_authenticated:
            print("\n5️⃣ Testing Text Generation...")
            try:
                messages = [
                    Message(role=MessageRole.USER, content="Hello, can you respond with just 'Hi there!'?")
                ]
                
                # Get available models
                models = await provider.get_models()
                if models:
                    model_name = models[0].name
                    print(f"   Using model: {model_name}")
                    
                    config = GenerationConfig(
                        temperature=0.1,
                        max_tokens=50
                    )
                    
                    response = await provider.generate_text(messages, model_name, config)
                    print(f"✅ Text generation successful!")
                    print(f"   Response: {response.content[:100]}...")
                else:
                    print("❌ No models available for text generation")
                    
            except Exception as e:
                print(f"❌ Text generation failed: {e}")
                print(f"   Error type: {type(e).__name__}")
        
        # Test 6: Connection test (simulating settings dialog)
        print("\n6️⃣ Testing Connection Test (Settings Dialog Style)...")
        try:
            # Simulate the settings dialog connection test
            settings = {
                'base_url': 'http://localhost:11434',
                'timeout': 30,
                'api_key': ''  # Empty API key
            }
            
            success, message = await test_ollama_connection_like_settings(settings)
            print(f"✅ Connection test result: {success}")
            print(f"✅ Connection test message: {message}")
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_ollama_connection_like_settings(settings):
    """Test Ollama connection like the settings dialog does."""
    try:
        import aiohttp
        
        base_url = settings.get('base_url', 'http://localhost:11434')
        timeout = settings.get('timeout', 30)
        api_key = settings.get('api_key', '').strip()
        
        headers = {'Content-Type': 'application/json'}
        # Add API key if provided (optional for Ollama)
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        
        async with aiohttp.ClientSession(headers=headers, timeout=timeout_obj) as session:
            async with session.get(f'{base_url}/api/tags') as response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('models', []))
                    auth_status = "with authentication" if api_key else "without authentication"
                    return True, f"Connected successfully {auth_status}! Found {model_count} models."
                else:
                    return False, f"Ollama server responded with HTTP {response.status}"
                    
    except aiohttp.ClientConnectorError:
        return False, f"Cannot connect to Ollama at {base_url}. Is Ollama running on the specified URL?"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def test_authentication_logic():
    """Test the authentication logic issues."""
    print("\n🔍 Analyzing Authentication Logic Issues")
    print("=" * 50)
    
    try:
        from nuke_ai_panel.core.base_provider import BaseProvider
        from nuke_ai_panel.providers.ollama_provider import OllamaProvider
        
        # Check the _ensure_authenticated method
        print("\n📋 Current Authentication Logic:")
        print("   - BaseProvider._ensure_authenticated() raises AuthenticationError if not self._authenticated")
        print("   - OllamaProvider.authenticate() sets self._authenticated = True on success")
        print("   - generate_text() calls self._ensure_authenticated() before proceeding")
        
        print("\n🔧 Issues Identified:")
        print("   1. authenticate() might not be called before generate_text()")
        print("   2. _authenticated flag might not persist between calls")
        print("   3. Connection test works but provider authentication fails")
        
        print("\n💡 Required Fixes:")
        print("   1. Auto-authenticate in generate_text() if not authenticated")
        print("   2. Ensure authentication persists properly")
        print("   3. Make authentication work without API key for local Ollama")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing authentication logic: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Ollama Authentication Fix Test")
    print("=" * 60)
    
    # Test current authentication logic
    test_authentication_logic()
    
    # Test actual Ollama functionality
    success = await test_ollama_authentication()
    
    if success:
        print("\n✅ All tests completed!")
        print("\n📝 Summary:")
        print("   - If authentication works: Ollama server is running and accessible")
        print("   - If authentication fails: Server not running or authentication logic needs fixing")
        print("   - Connection test should work independently of provider authentication")
    else:
        print("\n❌ Tests failed - check the errors above")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())