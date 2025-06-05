#!/usr/bin/env python
"""
Test script to verify consistent code generation across different AI providers.

This script tests the code generation functionality with different AI providers
to ensure that all models return properly formatted code when requested.
"""

import sys
import os
import asyncio
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.base_provider import Message, MessageRole, GenerationConfig
from nuke_ai_panel.utils.event_loop_manager import get_event_loop_manager, run_coroutine

# Test prompt that should trigger code generation
CODE_GENERATION_PROMPT = """
Create a simple Nuke script that adds a Blur node to the selected node and connects it.
Make sure to include proper error handling if no node is selected.
"""

# List of providers to test
PROVIDERS_TO_TEST = ["openai", "anthropic", "mistral", "ollama"]

# Test configuration
TEST_CONFIG = {
    "timeout": {
        "openai": 60,
        "anthropic": 60,
        "mistral": 60,
        "ollama": 180  # Longer timeout for local models
    },
    "skip_on_error": True  # Continue testing other providers if one fails
}

def setup_provider_manager() -> ProviderManager:
    """Set up the provider manager with configuration."""
    config = Config()
    provider_manager = ProviderManager(config)
    return provider_manager

def create_test_message(prompt: str) -> List[Message]:
    """Create a test message for the AI provider."""
    return [
        Message(role=MessageRole.SYSTEM, 
                content="You are an expert VFX compositor helping with Nuke workflows."),
        Message(role=MessageRole.USER, content=prompt)
    ]

async def test_provider(provider_manager: ProviderManager, provider_name: str) -> Dict[str, Any]:
    """Test code generation with a specific provider."""
    print(f"\nTesting provider: {provider_name}")
    
    try:
        # Authenticate provider
        provider = provider_manager.get_provider(provider_name)
        if not provider:
            print(f"  Provider {provider_name} not available, skipping...")
            return {
                "provider": provider_name,
                "status": "skipped",
                "reason": "Provider not available"
            }
        
        # Try to authenticate
        try:
            auth_result = await provider.authenticate()
            if not auth_result:
                print(f"  Authentication failed for {provider_name}, skipping...")
                return {
                    "provider": provider_name,
                    "status": "skipped",
                    "reason": "Authentication failed"
                }
        except Exception as e:
            print(f"  Authentication error for {provider_name}: {e}")
            
            # Special handling for Mistral dependency issues
            if provider_name == "mistral" and "library not properly installed" in str(e):
                print(f"  Mistral library not installed, skipping...")
                return {
                    "provider": provider_name,
                    "status": "skipped",
                    "reason": "Mistral library not properly installed. Install with: pip install mistralai"
                }
                
            return {
                "provider": provider_name,
                "status": "error",
                "reason": f"Authentication error: {e}"
            }
        
        # Get default model
        default_model = provider_manager.get_default_model(provider_name)
        if not default_model:
            # Use a fallback model based on provider
            fallback_models = {
                "openai": "gpt-3.5-turbo",
                "anthropic": "claude-3-haiku",
                "mistral": "mistral-tiny",
                "ollama": "llama2"  # Use smaller model for testing
            }
            default_model = fallback_models.get(provider_name, "")
            
        # Override with test-specific models for better reliability
        test_models = {
            "openai": "gpt-3.5-turbo",  # Faster and more reliable for testing
            "anthropic": "claude-3-haiku",  # Smaller, faster model
            "mistral": "mistral-tiny",  # Smallest Mistral model
            "ollama": "llama2"  # Smaller model to avoid timeouts
        }
        
        # Use test-specific model if available
        if provider_name in test_models:
            default_model = test_models[provider_name]
            
        # For Ollama, try to find an available model if the default isn't available
        if provider_name == "ollama":
            try:
                # Get available models
                models = await provider.get_models()
                if models and not any(m.name == default_model for m in models):
                    # Default model not available, use first available model
                    if models:
                        default_model = models[0].name
                        print(f"  Default model not found, using available model: {default_model}")
            except Exception as e:
                print(f"  Error getting Ollama models: {e}")
        
        print(f"  Using model: {default_model}")
        
        # Create test message
        messages = create_test_message(CODE_GENERATION_PROMPT)
        
        # Generate response
        config = GenerationConfig(
            temperature=0.7,
            max_tokens=1000
        )
        
        # Adjust timeout for Ollama
        if provider_name == "ollama":
            # Set a reasonable timeout for testing
            provider._adjust_timeout_for_model(default_model)
            print(f"  Using timeout: {provider.timeout}s for model {default_model}")
        
        print(f"  Generating response...")
        response = await provider_manager.generate_text(
            messages=messages,
            model=default_model,
            provider=provider_name,
            config=config
        )
        
        # Check if response contains code blocks
        content = response.content
        has_code_block = "```python" in content or "```" in content
        has_nuke_import = "import nuke" in content
        
        print(f"  Response received:")
        print(f"  - Has code block: {has_code_block}")
        print(f"  - Has nuke import: {has_nuke_import}")
        
        # Extract code blocks for analysis
        import re
        code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', content, re.DOTALL)
        
        return {
            "provider": provider_name,
            "model": default_model,
            "status": "success",
            "has_code_block": has_code_block,
            "has_nuke_import": has_nuke_import,
            "code_blocks": code_blocks,
            "full_response": content
        }
        
    except Exception as e:
        print(f"  Error testing {provider_name}: {e}")
        
        # Special handling for timeout errors
        if "timed out" in str(e).lower() and provider_name == "ollama":
            print(f"  Timeout error with Ollama model. Consider using a smaller model for testing.")
            return {
                "provider": provider_name,
                "status": "error",
                "reason": f"Timeout error: {e}. Consider using a smaller model for testing."
            }
        
        # Special handling for model not found errors
        if "model not found" in str(e).lower() and provider_name == "ollama":
            print(f"  Model not found error. No compatible models available in Ollama.")
            return {
                "provider": provider_name,
                "status": "skipped",
                "reason": "No compatible models available in Ollama. Try installing a model with 'ollama pull llama2'."
            }
            
        return {
            "provider": provider_name,
            "status": "error",
            "reason": str(e)
        }

async def run_tests():
    """Run tests for all providers."""
    provider_manager = setup_provider_manager()
    
    results = []
    for provider_name in PROVIDERS_TO_TEST:
        result = await test_provider(provider_manager, provider_name)
        results.append(result)
    
    return results

def analyze_results(results: List[Dict[str, Any]]):
    """Analyze and print test results."""
    print("\n" + "="*50)
    print("CODE GENERATION TEST RESULTS")
    print("="*50)
    
    success_count = 0
    code_block_count = 0
    nuke_import_count = 0
    
    for result in results:
        provider = result["provider"]
        status = result["status"]
        
        if status == "success":
            success_count += 1
            has_code_block = result.get("has_code_block", False)
            has_nuke_import = result.get("has_nuke_import", False)
            
            if has_code_block:
                code_block_count += 1
            if has_nuke_import:
                nuke_import_count += 1
            
            print(f"\n{provider} ({result.get('model', 'unknown')}):")
            print(f"  Status: {status}")
            print(f"  Code block: {'✅' if has_code_block else '❌'}")
            print(f"  Nuke import: {'✅' if has_nuke_import else '❌'}")
            
            if has_code_block and result.get("code_blocks"):
                print(f"  First code block sample:")
                code_sample = result["code_blocks"][0].strip()
                # Print first few lines of code
                code_lines = code_sample.split("\n")[:5]
                for line in code_lines:
                    print(f"    {line}")
                if len(code_lines) < len(code_sample.split("\n")):
                    print(f"    ...")
        else:
            print(f"\n{provider}:")
            print(f"  Status: {status}")
            print(f"  Reason: {result.get('reason', 'Unknown')}")
    
    print("\n" + "="*50)
    print(f"SUMMARY: {success_count}/{len(results)} providers tested successfully")
    print(f"Code blocks: {code_block_count}/{success_count} providers returned code blocks")
    print(f"Nuke imports: {nuke_import_count}/{success_count} providers included nuke imports")
    print("="*50)
    
    if code_block_count == success_count:
        print("\n✅ All successful providers returned code blocks!")
    else:
        print(f"\n❌ {success_count - code_block_count} providers did not return proper code blocks")

def main():
    """Main entry point."""
    print("Testing code generation consistency across AI providers...")
    
    # Run tests
    results = run_coroutine(run_tests())
    
    # Analyze results
    analyze_results(results)

if __name__ == "__main__":
    main()