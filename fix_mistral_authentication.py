#!/usr/bin/env python3
"""
Utility script to fix Mistral authentication issues.

This script helps diagnose and fix common issues with Mistral authentication
in the Nuke AI Panel application.
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
from nuke_ai_panel.providers.mistral_provider import MistralProvider
from nuke_ai_panel.utils.logger import get_logger, setup_logging

# Set up logging
setup_logging(level="DEBUG")
logger = get_logger(__name__)


async def check_mistral_library():
    """Check if the Mistral library is properly installed."""
    logger.info("Checking Mistral library installation...")
    
    try:
        import mistralai
        version = getattr(mistralai, "__version__", "unknown")
        logger.info(f"✅ Mistral library is installed (version: {version})")
        
        # Verify the client can be imported
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
                    logger.error("❌ Failed to import Mistral client - library may be incomplete")
                    logger.info("Reinstalling Mistral library...")
                    import subprocess
                    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "mistralai"], 
                                  capture_output=True, text=True)
                    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "mistralai"], 
                                  capture_output=True, text=True)
                    logger.info("Please restart the application after reinstalling the library")
                    return False
        
        return True
    except ImportError:
        logger.error("❌ Mistral library is not installed")
        logger.info("Installing Mistral library...")
        
        try:
            import subprocess
            # Force reinstall to ensure we get the correct version
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "mistralai"], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Successfully installed Mistral library")
                logger.info("Please restart the application after installing the library")
                
                # Try importing again to verify
                try:
                    import importlib
                    importlib.invalidate_caches()
                    
                    import mistralai
                    from mistralai.async_client import MistralAsyncClient
                    logger.info("✅ Verified Mistral library installation")
                    return True
                except ImportError:
                    logger.warning("⚠️ Mistral library installed but import still failing")
                    logger.info("Please restart the application and try again")
                    return False
            else:
                logger.error(f"❌ Failed to install Mistral library: {result.stderr}")
                logger.info("Please install manually with: pip install --upgrade mistralai")
                return False
        except Exception as e:
            logger.error(f"❌ Error installing Mistral library: {e}")
            logger.info("Please install manually with: pip install --upgrade mistralai")
            return False


async def fix_mistral_api_key():
    """Fix Mistral API key configuration."""
    logger.info("Checking Mistral API key configuration...")
    
    # Load existing configuration
    config = Config()
    auth_manager = AuthManager()
    
    # Check if API key exists
    existing_key = auth_manager.get_api_key("mistral")
    if existing_key:
        logger.info(f"Found existing Mistral API key (length: {len(existing_key)})")
        valid_format = auth_manager.validate_api_key("mistral", existing_key)
        if not valid_format:
            logger.warning("⚠️ Existing API key may have invalid format")
    else:
        logger.warning("⚠️ No Mistral API key found in configuration")
    
    # Ask user for API key
    print("\nTo use Mistral AI, you need a valid API key.")
    print("You can get one from: https://console.mistral.ai/api-keys/")
    
    new_key = input("\nEnter your Mistral API key (press Enter to keep existing): ").strip()
    
    if not new_key:
        if not existing_key:
            logger.error("❌ No API key provided and no existing key found")
            return False
        logger.info("Using existing API key")
        new_key = existing_key
    
    # Validate and save the API key
    if auth_manager.validate_api_key("mistral", new_key):
        auth_manager.set_api_key("mistral", new_key)
        logger.info("✅ Saved valid Mistral API key")
        
        # Enable the provider in config
        provider_config = config.get_provider_config("mistral")
        provider_config.enabled = True
        config.set_provider_config("mistral", provider_config)
        config.save()
        logger.info("✅ Enabled Mistral provider in configuration")
        
        return True
    else:
        logger.error("❌ The provided API key appears to be invalid")
        return False


async def test_mistral_authentication():
    """Test Mistral authentication with the configured API key."""
    logger.info("Testing Mistral authentication...")
    
    # Load configuration
    auth_manager = AuthManager()
    api_key = auth_manager.get_api_key("mistral")
    
    if not api_key:
        logger.error("❌ No Mistral API key found in configuration")
        return False
    
    # Create provider instance
    config = {"api_key": api_key}
    provider = MistralProvider("mistral", config)
    
    try:
        # Run diagnostic
        logger.info("Running authentication diagnostics...")
        diagnostics = await provider.diagnose_authentication()
        
        # Log diagnostic information
        for key, value in diagnostics.items():
            if key != "errors":
                logger.info(f"{key}: {value}")
        
        if diagnostics.get("errors"):
            for error in diagnostics["errors"]:
                logger.error(f"Error: {error}")
        
        # Test authentication
        authenticated = await provider.authenticate()
        if authenticated:
            logger.info("✅ Mistral authentication successful!")
            
            # Try to list models
            models = await provider.get_models()
            logger.info(f"Available models: {[m.name for m in models]}")
            return True
        else:
            logger.error("❌ Mistral authentication failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Mistral authentication failed with error: {e}")
        return False


async def main():
    """Run the Mistral authentication fix utility."""
    print("=" * 60)
    print("Mistral Authentication Fix Utility")
    print("=" * 60)
    print("This utility will help diagnose and fix Mistral authentication issues.")
    print()
    
    # Check Mistral library
    library_ok = await check_mistral_library()
    if not library_ok:
        print("\nPlease install the Mistral library and run this script again.")
        return
    
    # Fix API key
    api_key_ok = await fix_mistral_api_key()
    if not api_key_ok:
        print("\nPlease provide a valid Mistral API key and run this script again.")
        return
    
    # Test authentication
    auth_ok = await test_mistral_authentication()
    
    print("\n" + "=" * 60)
    if auth_ok:
        print("✅ Mistral authentication is now working correctly!")
        print("You can now use Mistral AI in the Nuke AI Panel.")
    else:
        print("⚠️ Mistral authentication is still not working.")
        print("Please check the logs for more information.")
        print("You may need to:")
        print("1. Verify your API key is correct")
        print("2. Check your internet connection")
        print("3. Ensure the Mistral API service is available")
        print("4. Restart the application after installing the library")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())