#!/usr/bin/env python
"""
Verification script for model mapping fixes.

This script provides a simple command-line interface to test the model mapping
system with different providers and models.
"""

import asyncio
import sys
import os
import argparse
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("model_mapping_verification")

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.core.base_provider import Message, MessageRole
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.auth import AuthManager
from nuke_ai_panel.core.exceptions import ModelNotFoundError, ProviderError


async def verify_model_mapping(provider_name: str, model_name: str, verbose: bool = False):
    """
    Verify model mapping for a specific provider and model.
    
    Args:
        provider_name: Name of the provider to test
        model_name: Name of the model to test
        verbose: Whether to show verbose output
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)
    
    logger.info(f"Verifying model mapping for provider '{provider_name}' and model '{model_name}'")
    
    # Initialize provider manager
    config = Config()
    auth_manager = AuthManager()
    provider_manager = ProviderManager(config, auth_manager)
    
    # Get provider instance
    provider = provider_manager.get_provider(provider_name)
    if not provider:
        logger.error(f"Provider '{provider_name}' not found or not loaded")
        return False
    
    # Try to authenticate
    try:
        authenticated = await provider_manager.authenticate_provider(provider_name)
        logger.info(f"Authentication result for {provider_name}: {authenticated}")
        if not authenticated:
            logger.error(f"Authentication failed for {provider_name}")
            return False
    except Exception as e:
        logger.error(f"Authentication failed for {provider_name}: {e}")
        return False
    
    # Get available models
    try:
        models = await provider.get_models()
        logger.info(f"Available models for {provider_name}: {len(models)}")
        if verbose and models:
            model_names = [m.name for m in models[:10]]
            logger.info(f"Sample models: {', '.join(model_names)}")
    except Exception as e:
        logger.error(f"Failed to get models for {provider_name}: {e}")
    
    # Test model mapping
    try:
        # Map the model using provider manager
        mapped_model = provider_manager._map_model_to_provider(model_name, provider_name)
        logger.info(f"Provider manager mapped '{model_name}' to '{mapped_model}' for {provider_name}")
        
        # For OpenRouter and Ollama, test their internal mapping too
        provider_mapped = None
        if provider_name == 'openrouter' and hasattr(provider, '_validate_and_map_model'):
            provider_mapped = await provider._validate_and_map_model(model_name)
            logger.info(f"OpenRouter provider mapped: '{model_name}' -> '{provider_mapped}'")
        elif provider_name == 'ollama' and hasattr(provider, '_map_model_to_available'):
            provider_mapped = await provider._map_model_to_available(model_name)
            logger.info(f"Ollama provider mapped: '{model_name}' -> '{provider_mapped}'")
        
        # Test if the model is valid
        final_model = provider_mapped or mapped_model
        if hasattr(provider, 'validate_model'):
            is_valid = await provider.validate_model(final_model)
            logger.info(f"Model '{final_model}' is valid for {provider_name}: {is_valid}")
            if not is_valid:
                logger.warning(f"Model '{final_model}' is not valid for {provider_name}")
        
        # Try a simple generation to verify
        messages = [
            Message(role=MessageRole.USER, content="Hello, can you tell me what model you are?")
        ]
        
        try:
            logger.info(f"Testing generation with model '{final_model}'...")
            response = await provider_manager.generate_text(
                messages=messages,
                model=model_name,  # Use original model name to test mapping
                provider=provider_name,
                retry_on_failure=True
            )
            
            logger.info(f"Generation successful with {provider_name}/{model_name}")
            logger.info(f"Used model: {response.model}")
            logger.info(f"Response: {response.content[:100]}...")
            return True
            
        except ModelNotFoundError as e:
            logger.error(f"Model not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing model '{model_name}' for {provider_name}: {e}")
        return False


async def list_available_providers():
    """List all available providers."""
    # Initialize provider manager
    config = Config()
    auth_manager = AuthManager()
    provider_manager = ProviderManager(config, auth_manager)
    
    providers = provider_manager.get_available_providers()
    logger.info(f"Available providers: {', '.join(providers)}")
    return providers


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Verify model mapping fixes")
    parser.add_argument("--provider", help="Provider to test (e.g., openrouter, ollama)")
    parser.add_argument("--model", help="Model to test (e.g., gpt-3.5-turbo, mistral)")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--list-providers", action="store_true", help="List available providers")
    
    args = parser.parse_args()
    
    if args.list_providers:
        await list_available_providers()
        return
    
    if not args.provider or not args.model:
        logger.error("Both --provider and --model arguments are required")
        parser.print_help()
        return
    
    success = await verify_model_mapping(args.provider, args.model, args.verbose)
    
    if success:
        logger.info("Verification successful!")
        sys.exit(0)
    else:
        logger.error("Verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())