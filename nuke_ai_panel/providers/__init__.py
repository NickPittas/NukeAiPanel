"""
AI Providers module for Nuke AI Panel.

Contains implementations for all supported AI providers including
OpenAI, Anthropic, Google, OpenRouter, Ollama, and Mistral.

This module uses lazy imports to avoid loading provider dependencies
unless the specific provider is actually used.
"""

# Lazy imports to avoid loading dependencies for unused providers
def get_provider_class(provider_name: str):
    """
    Get provider class by name with lazy loading.
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Provider class
        
    Raises:
        ImportError: If provider or its dependencies are not available
    """
    if provider_name.lower() == 'openai':
        from .openai_provider import OpenaiProvider
        return OpenaiProvider
    elif provider_name.lower() == 'anthropic':
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider
    elif provider_name.lower() == 'google':
        from .google_provider import GoogleProvider
        return GoogleProvider
    elif provider_name.lower() == 'openrouter':
        from .openrouter_provider import OpenrouterProvider
        return OpenrouterProvider
    elif provider_name.lower() == 'ollama':
        from .ollama_provider import OllamaProvider
        return OllamaProvider
    elif provider_name.lower() == 'mistral':
        from .mistral_provider import MistralProvider
        return MistralProvider
    else:
        raise ImportError(f"Unknown provider: {provider_name}")

__all__ = [
    "get_provider_class",
]