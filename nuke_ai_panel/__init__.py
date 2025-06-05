"""
Nuke AI Panel - AI-powered panel integration for Nuke compositing software.

This package provides a comprehensive AI provider integration system with support
for multiple AI services including OpenAI, Anthropic, Google, OpenRouter, Ollama, and Mistral.
"""

__version__ = "0.1.0"
__author__ = "Nuke AI Panel Team"

from .core.provider_manager import ProviderManager
from .core.config import Config
from .core.auth import AuthManager

__all__ = [
    "ProviderManager",
    "Config", 
    "AuthManager",
    "__version__",
    "__author__",
]