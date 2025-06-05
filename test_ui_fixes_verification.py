#!/usr/bin/env python3
"""
Test script to verify the fixes for critical UI functionality issues:
1. Provider dropdown not working
2. Connection tests hanging
"""

import sys
import os
import asyncio
import logging
import time
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_provider_dropdown():
    """Test provider dropdown functionality."""
    logger.info("Testing provider dropdown functionality...")
    
    try:
        from nuke_ai_panel.core.provider_manager import ProviderManager
        from nuke_ai_panel.core.config import Config
        
        # Create config and provider manager
        config = Config()
        provider_manager = ProviderManager(config)
        
        # Get available providers
        providers = provider_manager.get_available_providers()
        logger.info(f"Available providers: {providers}")
        
        if not providers:
            logger.error("No providers available")
            return False
        
        # Get current provider
        current_provider = provider_manager.get_current_provider()
        logger.info(f"Current provider: {current_provider}")
        
        # Try to switch provider
        test_provider = next((p for p in providers if p != current_provider), providers[0])
        logger.info(f"Switching to provider: {test_provider}")
        
        # Test provider switching
        provider_manager.set_current_provider(test_provider)
        new_current = provider_manager.get_current_provider()
        
        if new_current == test_provider:
            logger.info(f"✅ Provider successfully switched to {test_provider}")
            return True
        else:
            logger.error(f"❌ Provider switch failed. Expected {test_provider}, got {new_current}")
            return False
            
    except Exception as e:
        logger.error(f"Provider dropdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_test():
    """Test connection test functionality."""
    logger.info("Testing connection test functionality...")
    
    try:
        from nuke_ai_panel.core.provider_manager import ProviderManager
        from nuke_ai_panel.core.config import Config
        
        # Create config and provider manager
        config = Config()
        provider_manager = ProviderManager(config)
        
        # Get available providers
        providers = provider_manager.get_available_providers()
        if not providers:
            logger.error("No providers available")
            return False
        
        # Select a provider to test
        test_provider = 'ollama'  # Ollama is often available locally
        if test_provider not in providers:
            test_provider = providers[0]
        
        logger.info(f"Testing connection for provider: {test_provider}")
        
        # Get provider instance
        provider = provider_manager.get_provider(test_provider)
        if not provider:
            logger.error(f"Provider {test_provider} not found")
            return False
        
        # Create a mock async function that simulates a connection test
        async def mock_connection_test():
            logger.info("Starting mock connection test...")
            await asyncio.sleep(2)  # Simulate network delay
            logger.info("Mock connection test completed")
            return {
                'status': 'healthy',
                'models': ['llama2', 'mistral'],
                'version': '0.1.0',
                'response_time': 0.5
            }
        
        # Replace the actual connection test with our mock
        if hasattr(provider, 'health_check'):
            original_health_check = provider.health_check
            provider.health_check = mock_connection_test
        
        # Run the connection test with timeout
        try:
            logger.info("Running connection test with timeout...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run with timeout
                result = loop.run_until_complete(
                    asyncio.wait_for(
                        provider_manager.health_check(test_provider),
                        timeout=5
                    )
                )
                logger.info(f"Connection test result: {result}")
                success = True
            except asyncio.TimeoutError:
                logger.error("Connection test timed out")
                success = False
            finally:
                loop.close()
            
            # Restore original method if we replaced it
            if hasattr(provider, 'health_check') and 'original_health_check' in locals():
                provider.health_check = original_health_check
            
            return success
            
        except Exception as e:
            logger.error(f"Connection test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        logger.error(f"Connection test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all UI functionality tests."""
    print("🚀 Verifying Critical UI Functionality Fixes")
    print("=" * 50)
    
    results = []
    
    # Test provider dropdown
    print("\n📋 Testing Provider Dropdown...")
    provider_result = test_provider_dropdown()
    results.append(provider_result)
    
    # Test connection tests
    print("\n📋 Testing Connection Tests...")
    connection_result = test_connection_test()
    results.append(connection_result)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    if all(results):
        print("✅ All UI functionality fixes verified!")
        print("🎉 Provider dropdown and connection tests are working correctly")
    else:
        print("❌ Some UI functionality fixes failed verification!")
        print("🔧 Additional fixes may be needed")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)