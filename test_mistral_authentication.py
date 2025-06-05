#!/usr/bin/env python3
"""
Test script for Mistral authentication.

This script tests the Mistral authentication process to help diagnose issues
with API key validation and authentication.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.auth import AuthManager
from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.providers.mistral_provider import MistralProvider
from nuke_ai_panel.utils.logger import get_logger, setup_logging

# Set up logging
setup_logging(level="DEBUG")
logger = get_logger(__name__)


async def test_mistral_direct():
    """Test Mistral authentication directly using the provider."""
    logger.info("Testing Mistral authentication directly...")
    
    # Get API key from environment or input
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        api_key = input("Enter your Mistral API key: ")
    
    # Create provider instance
    config = {"api_key": api_key}
    provider = MistralProvider("mistral", config)
    
    try:
        # Test authentication
        authenticated = await provider.authenticate()
        if authenticated:
            logger.info("✅ Mistral authentication successful!")
            
            # Try to list models
            models = await provider.get_models()
            logger.info(f"Available models: {[m.name for m in models]}")
        else:
            logger.error("❌ Mistral authentication failed without raising an exception")
    except Exception as e:
        logger.error(f"❌ Mistral authentication failed with error: {e}")


async def test_mistral_via_manager():
    """Test Mistral authentication through the provider manager."""
    logger.info("Testing Mistral authentication via provider manager...")
    
    # Get API key from environment or input
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        api_key = input("Enter your Mistral API key: ")
    
    # Create configuration
    config = Config()
    auth_manager = AuthManager()
    
    # Store API key
    auth_manager.set_api_key("mistral", api_key)
    
    # Create provider manager
    manager = ProviderManager(config, auth_manager)
    
    try:
        # Authenticate Mistral provider
        authenticated = await manager.authenticate_provider("mistral")
        if authenticated:
            logger.info("✅ Mistral authentication successful via provider manager!")
            
            # Try to get models
            models = await manager.get_available_models("mistral")
            if "mistral" in models:
                logger.info(f"Available models: {[m.name for m in models['mistral']]}")
        else:
            logger.error("❌ Mistral authentication failed without raising an exception")
    except Exception as e:
        logger.error(f"❌ Mistral authentication failed with error: {e}")


async def test_mistral_library():
    """Test if the Mistral library is properly installed and working."""
    logger.info("Testing Mistral library installation...")
    
    try:
        # Try to import the library
        import mistralai
        logger.info(f"✅ Mistral library found: {mistralai.__name__}")
        
        # Check version
        version = getattr(mistralai, "__version__", "unknown")
        logger.info(f"Mistral library version: {version}")
        
        # Try to import client
        try:
            from mistralai.async_client import MistralAsyncClient
            logger.info("✅ MistralAsyncClient imported successfully")
        except ImportError:
            try:
                from mistralai import Mistral as MistralAsyncClient
                logger.info("✅ Mistral client imported successfully (newer structure)")
            except ImportError:
                try:
                    from mistralai.client import MistralClient as MistralAsyncClient
                    logger.info("✅ MistralClient imported successfully (alternative structure)")
                except ImportError:
                    logger.error("❌ Failed to import Mistral client")
                    return False
        
        return True
    except ImportError as e:
        logger.error(f"❌ Mistral library not installed: {e}")
        logger.info("To install the Mistral library, run: pip install mistralai")
        return False


async def main():
    """Run all tests."""
    logger.info("Starting Mistral authentication tests...")
    
    # Test library installation
    library_ok = await test_mistral_library()
    if not library_ok:
        logger.error("❌ Mistral library test failed - please install the library first")
        return
    
    # Test direct authentication
    await test_mistral_direct()
    
    # Test authentication via provider manager
    await test_mistral_via_manager()
    
    logger.info("Mistral authentication tests completed")


if __name__ == "__main__":
    asyncio.run(main())