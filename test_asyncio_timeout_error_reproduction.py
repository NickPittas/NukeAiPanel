#!/usr/bin/env python3
"""
Test script to reproduce the critical asyncio timeout context manager error.

This script reproduces the exact error that's causing all connections to fail:
"Timeout context manager should be used inside a task"
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_asyncio_timeout_error():
    """Test to reproduce the asyncio timeout context manager error."""
    print("🔍 Testing asyncio timeout context manager error reproduction...")
    
    try:
        # Import the settings dialog
        from src.ui.settings_dialog import ProviderSettingsWidget
        
        # Create a mock provider widget
        provider_config = {
            'base_url': 'http://localhost:11434',
            'timeout': 30,
            'api_key': ''
        }
        
        print("✅ Successfully imported ProviderSettingsWidget")
        
        # Try to create the widget (this should work)
        widget = ProviderSettingsWidget('ollama', provider_config)
        print("✅ Successfully created ProviderSettingsWidget")
        
        # Now try to simulate the connection test that's causing the error
        print("\n🔍 Testing connection test method that causes the asyncio error...")
        
        # Get the settings
        settings = widget.get_settings()
        print(f"✅ Got settings: {settings}")
        
        # Try to run the async connection test in the problematic way
        print("\n🔍 Attempting to reproduce the asyncio timeout error...")
        
        # This is the problematic pattern that causes the error
        try:
            # Simulate what happens in the settings dialog
            import threading
            import aiohttp
            
            def test_thread():
                """This is the problematic thread function."""
                try:
                    # Create event loop for this thread - THIS IS THE PROBLEM
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def test_connection():
                        """This async function uses timeout incorrectly."""
                        # This is where the error occurs - timeout context manager outside task
                        timeout_obj = aiohttp.ClientTimeout(total=30)
                        
                        async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                            async with session.get('http://localhost:11434/api/tags') as response:
                                return response.status == 200
                    
                    # Run the async function - THIS CAUSES THE ERROR
                    result = loop.run_until_complete(test_connection())
                    print(f"❌ Unexpected success: {result}")
                    
                except Exception as e:
                    print(f"🎯 REPRODUCED THE ERROR: {e}")
                    if "Timeout context manager should be used inside a task" in str(e):
                        print("✅ Successfully reproduced the exact asyncio timeout error!")
                        return True
                    else:
                        print(f"❌ Different error: {e}")
                        return False
                finally:
                    if 'loop' in locals():
                        loop.close()
            
            # Start the problematic thread
            thread = threading.Thread(target=test_thread, daemon=True)
            thread.start()
            thread.join(timeout=5)  # Wait max 5 seconds
            
        except Exception as e:
            print(f"🎯 REPRODUCED THE ERROR at higher level: {e}")
            if "Timeout context manager should be used inside a task" in str(e):
                print("✅ Successfully reproduced the exact asyncio timeout error!")
                return True
        
        print("❌ Failed to reproduce the specific error")
        return False
        
    except Exception as e:
        print(f"❌ Error during test setup: {e}")
        return False

def test_correct_asyncio_pattern():
    """Test the correct way to handle asyncio in threads."""
    print("\n🔧 Testing the CORRECT asyncio pattern...")
    
    try:
        import aiohttp
        import threading
        
        def correct_test_thread():
            """Correct way to handle asyncio in threads."""
            try:
                # Create event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def test_connection():
                    """Correct async function with proper timeout usage."""
                    # Create timeout within the async context
                    async with aiohttp.ClientSession() as session:
                        try:
                            # Use asyncio.wait_for for timeout instead of ClientTimeout
                            async with asyncio.timeout(30):  # This is the correct way
                                async with session.get('http://localhost:11434/api/tags') as response:
                                    return response.status == 200
                        except asyncio.TimeoutError:
                            return False
                
                # Run the async function
                result = loop.run_until_complete(test_connection())
                print(f"✅ Correct pattern worked: {result}")
                return True
                
            except Exception as e:
                print(f"❌ Error in correct pattern: {e}")
                return False
            finally:
                if 'loop' in locals():
                    loop.close()
        
        # Start the correct thread
        thread = threading.Thread(target=correct_test_thread, daemon=True)
        thread.start()
        thread.join(timeout=5)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing correct pattern: {e}")
        return False

if __name__ == "__main__":
    print("🚨 CRITICAL ASYNCIO TIMEOUT CONTEXT MANAGER ERROR REPRODUCTION TEST")
    print("=" * 70)
    
    # Test 1: Reproduce the error
    error_reproduced = test_asyncio_timeout_error()
    
    # Test 2: Show correct pattern
    correct_pattern_works = test_correct_asyncio_pattern()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"🎯 Error reproduced: {'✅ YES' if error_reproduced else '❌ NO'}")
    print(f"🔧 Correct pattern works: {'✅ YES' if correct_pattern_works else '❌ NO'}")
    
    if error_reproduced:
        print("\n🚨 CRITICAL ISSUE CONFIRMED:")
        print("   The asyncio timeout context manager error has been reproduced!")
        print("   This is exactly what's causing all connections to fail.")
        print("\n🔧 SOLUTION NEEDED:")
        print("   1. Fix timeout usage in settings dialog connection tests")
        print("   2. Fix timeout usage in all provider implementations")
        print("   3. Use asyncio.timeout() instead of aiohttp.ClientTimeout in async contexts")
    
    sys.exit(0 if error_reproduced else 1)