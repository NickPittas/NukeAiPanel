#!/usr/bin/env python
"""
Test script for model mapping fixes.

This script tests the model mapping system to ensure that:
1. OpenRouter uses valid model IDs
2. Ollama uses available models
3. Fallback mechanisms work correctly
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("model_mapping_test")

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.core.base_provider import Message, MessageRole
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.auth import AuthManager
from nuke_ai_panel.core.exceptions import ModelNotFoundError


async def test_provider_model_mapping(provider_name: str, test_models: List[str]):
    """Test model mapping for a specific provider."""
    logger.info(f"Testing model mapping for provider: {provider_name}")
    
    # Initialize provider manager
    config = Config()
    auth_manager = AuthManager()
    provider_manager = ProviderManager(config, auth_manager)
    
    # Get provider instance
    provider = provider_manager.get_provider(provider_name)
    if not provider:
        logger.error(f"Provider '{provider_name}' not found or not loaded")
        return
    
    # Try to authenticate
    try:
        authenticated = await provider_manager.authenticate_provider(provider_name)
        logger.info(f"Authentication result for {provider_name}: {authenticated}")
    except Exception as e:
        logger.error(f"Authentication failed for {provider_name}: {e}")
        return
    
    # Get available models
    try:
        models = await provider.get_models()
        logger.info(f"Available models for {provider_name}: {len(models)}")
        if models:
            model_names = [m.name for m in models[:5]]
            logger.info(f"Sample models: {', '.join(model_names)}")
    except Exception as e:
        logger.error(f"Failed to get models for {provider_name}: {e}")
    
    # Test model mapping
    for model in test_models:
        try:
            # Map the model
            mapped_model = provider_manager._map_model_to_provider(model, provider_name)
            logger.info(f"Mapped '{model}' to '{mapped_model}' for {provider_name}")
            
            # For OpenRouter and Ollama, test their internal mapping too
            if provider_name in ['openrouter', 'ollama']:
                if hasattr(provider, '_validate_and_map_model'):
                    provider_mapped = await provider._validate_and_map_model(model)
                    logger.info(f"Provider-specific mapping: '{model}' -> '{provider_mapped}'")
                elif hasattr(provider, '_map_model_to_available'):
                    provider_mapped = await provider._map_model_to_available(model)
                    logger.info(f"Provider-specific mapping: '{model}' -> '{provider_mapped}'")
            
            # Test if the model is valid
            if hasattr(provider, 'validate_model'):
                is_valid = await provider.validate_model(mapped_model)
                logger.info(f"Model '{mapped_model}' is valid for {provider_name}: {is_valid}")
        except Exception as e:
            logger.error(f"Error testing model '{model}' for {provider_name}: {e}")


async def test_generate_with_mapped_models():
    """Test text generation with mapped models."""
    logger.info("Testing text generation with mapped models")
    
    # Initialize provider manager
    config = Config()
    auth_manager = AuthManager()
    provider_manager = ProviderManager(config, auth_manager)
    
    # Test models
    test_cases = [
        {"provider": "openrouter", "model": "google/gemini-pro"},
        {"provider": "openrouter", "model": "gpt-3.5-turbo"},
        {"provider": "ollama", "model": "llama2:70b"},
        {"provider": "ollama", "model": "mistral"},
        {"provider": "ollama", "model": "mixtral"}
    ]
    
    # Simple test message
    messages = [
        Message(role=MessageRole.USER, content="Hello, can you tell me what model you are?")
    ]
    
    for test_case in test_cases:
        provider_name = test_case["provider"]
        model = test_case["model"]
        
        logger.info(f"Testing generation with provider '{provider_name}' and model '{model}'")
        
        try:
            # Try to generate text
            response = await provider_manager.generate_text(
                messages=messages,
                model=model,
                provider=provider_name,
                retry_on_failure=True
            )
            
            logger.info(f"Generation successful with {provider_name}/{model}")
            logger.info(f"Used model: {response.model}")
            logger.info(f"Response: {response.content[:100]}...")
            
        except ModelNotFoundError as e:
            logger.error(f"Model not found: {e}")
        except Exception as e:
            logger.error(f"Generation failed: {e}")


async def main():
    """Main test function."""
    logger.info("Starting model mapping tests")
    
    # Test OpenRouter model mapping
    await test_provider_model_mapping("openrouter", [
        "google/gemini-pro",
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-opus",
        "mistral-small"
    ])
    
    # Test Ollama model mapping
    await test_provider_model_mapping("ollama", [
        "llama2:70b",
        "mistral",
        "mixtral",
        "gemini-pro",
        "gpt-4"
    ])
    
    # Test generation with mapped models
    await test_generate_with_mapped_models()
    
    logger.info("Model mapping tests completed")


if __name__ == "__main__":
    # Run the async tests
    asyncio.run(main())