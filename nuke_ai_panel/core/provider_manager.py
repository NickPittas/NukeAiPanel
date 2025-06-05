"""
Provider manager for coordinating AI providers.

This module manages the lifecycle of AI providers, handles provider selection,
load balancing, and provides a unified interface for AI operations.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import importlib

from .base_provider import BaseProvider, Message, ModelInfo, GenerationConfig, GenerationResponse
from .config import Config, ProviderConfig
from .auth import AuthManager
from .exceptions import (
    ProviderError,
    ConfigurationError,
    AuthenticationError,
    ModelNotFoundError
)
from ..utils.logger import get_logger
from ..utils.rate_limiter import ProviderRateLimiter, RateLimit
from ..utils.cache import CacheManager
from ..utils.retry import RetryManager, RetryConfig

logger = get_logger(__name__)


@dataclass
class ProviderStatus:
    """Status information for a provider."""
    name: str
    enabled: bool
    authenticated: bool
    available: bool
    last_check: datetime
    error_message: Optional[str] = None
    model_count: int = 0
    response_time: Optional[float] = None


class ProviderManager:
    """
    Manages multiple AI providers and provides a unified interface.
    
    Features:
    - Provider lifecycle management
    - Automatic provider selection
    - Load balancing
    - Health monitoring
    - Rate limiting
    - Caching
    - Retry logic
    """
    
    PROVIDER_MODULES = {
        'openai': 'nuke_ai_panel.providers.openai_provider',
        'anthropic': 'nuke_ai_panel.providers.anthropic_provider',
        'google': 'nuke_ai_panel.providers.google_provider',
        'openrouter': 'nuke_ai_panel.providers.openrouter_provider',
        'ollama': 'nuke_ai_panel.providers.ollama_provider',
        'mistral': 'nuke_ai_panel.providers.mistral_provider',
    }
    
    def __init__(
        self,
        config: Optional[Config] = None,
        auth_manager: Optional[AuthManager] = None,
        cache_manager: Optional[CacheManager] = None,
        rate_limiter: Optional[ProviderRateLimiter] = None,
        retry_manager: Optional[RetryManager] = None
    ):
        """
        Initialize the provider manager.
        
        Args:
            config: Configuration manager
            auth_manager: Authentication manager
            cache_manager: Cache manager
            rate_limiter: Rate limiter
            retry_manager: Retry manager
        """
        self.config = config or Config()
        self.auth_manager = auth_manager or AuthManager()
        self.cache_manager = cache_manager or CacheManager()
        self.rate_limiter = rate_limiter or ProviderRateLimiter()
        self.retry_manager = retry_manager or RetryManager()
        
        # Provider instances
        self._providers: Dict[str, BaseProvider] = {}
        self._provider_status: Dict[str, ProviderStatus] = {}
        
        # Load balancing
        self._provider_usage: Dict[str, int] = {}
        self._provider_errors: Dict[str, int] = {}
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers."""
        logger.info("Initializing AI providers...")
        
        for provider_name in self.config.list_providers():
            if self.config.is_provider_enabled(provider_name):
                try:
                    self._load_provider(provider_name)
                except Exception as e:
                    logger.error(f"Failed to load provider {provider_name}: {e}")
                    self._provider_status[provider_name] = ProviderStatus(
                        name=provider_name,
                        enabled=True,
                        authenticated=False,
                        available=False,
                        last_check=datetime.now(),
                        error_message=str(e)
                    )
        
        # Set up rate limiters
        self._setup_rate_limiters()
        
        logger.info(f"Initialized {len(self._providers)} providers")
    
    def _load_provider(self, provider_name: str):
        """Load a specific provider."""
        if provider_name not in self.PROVIDER_MODULES:
            raise ConfigurationError(
                f"provider.{provider_name}",
                f"Unknown provider: {provider_name}"
            )
        
        try:
            # Use lazy loading to avoid importing dependencies for unused providers
            from ..providers import get_provider_class
            provider_class = get_provider_class(provider_name)
            
            # Get provider configuration
            provider_config = self.config.get_provider_config(provider_name)
            auth_config = self.auth_manager.get_provider_config(provider_name)
            
            # Merge configurations with proper API key handling
            # API key loading fix applied
            full_config = {**provider_config.__dict__, **auth_config}
            
            # Ensure API key is properly loaded from config
            if not full_config.get('api_key') and hasattr(provider_config, 'api_key') and provider_config.api_key:
                full_config['api_key'] = provider_config.api_key
            
            # Also check for base_url mapping
            if hasattr(provider_config, 'base_url') and provider_config.base_url:
                full_config['base_url'] = provider_config.base_url
            elif hasattr(provider_config, 'custom_endpoint') and provider_config.custom_endpoint:
                full_config['base_url'] = provider_config.custom_endpoint
            
            # Create provider instance
            provider = provider_class(provider_name, full_config)
            self._providers[provider_name] = provider
            
            # Initialize status
            self._provider_status[provider_name] = ProviderStatus(
                name=provider_name,
                enabled=True,
                authenticated=False,
                available=False,
                last_check=datetime.now()
            )
            
            # Initialize usage tracking
            self._provider_usage[provider_name] = 0
            self._provider_errors[provider_name] = 0
            
            logger.info(f"Loaded provider: {provider_name}")
            
        except Exception as e:
            logger.error(f"Failed to load provider {provider_name}: {e}")
            raise ProviderError(provider_name, f"Failed to load provider: {e}")
    
    def _setup_rate_limiters(self):
        """Set up rate limiters for all providers."""
        for provider_name, provider in self._providers.items():
            provider_config = self.config.get_provider_config(provider_name)
            
            if provider_config.rate_limit:
                rate_limit = RateLimit(
                    requests_per_minute=provider_config.rate_limit,
                    burst_limit=provider_config.rate_limit // 2
                )
                self.rate_limiter.add_provider(provider_name, rate_limit)
                logger.debug(f"Set up rate limiter for {provider_name}: {provider_config.rate_limit} req/min")
    
    async def authenticate_provider(self, provider_name: str) -> bool:
        """
        Authenticate a specific provider.
        
        Args:
            provider_name: Provider name
            
        Returns:
            True if authentication successful
            
        Raises:
            ProviderError: If provider not found
            AuthenticationError: If authentication fails
        """
        if provider_name not in self._providers:
            raise ProviderError(provider_name, "Provider not loaded")
        
        provider = self._providers[provider_name]
        
        try:
            success = await provider.authenticate()
            
            # Update status
            self._provider_status[provider_name].authenticated = success
            self._provider_status[provider_name].available = success
            self._provider_status[provider_name].last_check = datetime.now()
            self._provider_status[provider_name].error_message = None
            
            if success:
                logger.info(f"Successfully authenticated provider: {provider_name}")
            else:
                logger.warning(f"Failed to authenticate provider: {provider_name}")
            
            return success
            
        except Exception as e:
            self._provider_status[provider_name].authenticated = False
            self._provider_status[provider_name].available = False
            self._provider_status[provider_name].error_message = str(e)
            logger.error(f"Authentication failed for {provider_name}: {e}")
            raise AuthenticationError(provider_name, str(e))
    
    async def authenticate_all_providers(self) -> Dict[str, bool]:
        """
        Authenticate all providers.
        
        Returns:
            Dictionary mapping provider names to authentication success
        """
        results = {}
        
        for provider_name in self._providers:
            try:
                results[provider_name] = await self.authenticate_provider(provider_name)
            except Exception as e:
                results[provider_name] = False
                logger.error(f"Failed to authenticate {provider_name}: {e}")
        
        authenticated_count = sum(results.values())
        logger.info(f"Authenticated {authenticated_count}/{len(results)} providers")
        
        return results
    
    async def get_available_models(self, provider_name: Optional[str] = None) -> Dict[str, List[ModelInfo]]:
        """
        Get available models from providers.
        
        Args:
            provider_name: Specific provider name or None for all
            
        Returns:
            Dictionary mapping provider names to model lists
        """
        results = {}
        
        providers_to_check = [provider_name] if provider_name else list(self._providers.keys())
        
        for name in providers_to_check:
            if name not in self._providers:
                continue
            
            provider = self._providers[name]
            status = self._provider_status[name]
            
            try:
                # Try to authenticate if not already authenticated
                if not status.authenticated:
                    try:
                        await self.authenticate_provider(name)
                    except Exception as auth_error:
                        logger.warning(f"Provider {name} authentication failed: {auth_error}")
                        # Continue anyway to try getting models
                
                models = await provider.get_models()
                results[name] = models
                
                # Update status
                status.model_count = len(models)
                status.last_check = datetime.now()
                status.error_message = None
                
                logger.debug(f"Retrieved {len(models)} models from {name}")
                
            except Exception as e:
                logger.error(f"Failed to get models from {name}: {e}")
                status.error_message = str(e)
                results[name] = []
        
        return results
    
    def get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        """
        Get a provider instance.
        
        Args:
            provider_name: Provider name
            
        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available providers (including those with loading errors).
        
        Returns:
            List of provider names
        """
        # Return all loaded providers, regardless of authentication status
        # This allows the UI to show all providers for configuration
        available = list(self._providers.keys())
        
        # If no providers are loaded, return all configured provider names
        if not available:
            available = list(self.PROVIDER_MODULES.keys())
        
        return available
    
    def select_provider(
        self,
        model: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        exclude_providers: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Select the best provider for a request.
        
        Args:
            model: Specific model name
            preferred_provider: Preferred provider name
            exclude_providers: Providers to exclude
            
        Returns:
            Selected provider name or None if none available
        """
        exclude_providers = exclude_providers or []
        available_providers = self.get_available_providers()
        
        # Filter out excluded providers
        candidates = [p for p in available_providers if p not in exclude_providers]
        
        if not candidates:
            return None
        
        # If preferred provider is available, use it
        if preferred_provider and preferred_provider in candidates:
            return preferred_provider
        
        # If model is specified, filter by providers that support it
        if model:
            model_providers = []
            for provider_name in candidates:
                # This would require caching model info or checking synchronously
                # For now, we'll use a simple heuristic based on model name
                if self._provider_supports_model(provider_name, model):
                    model_providers.append(provider_name)
            
            if model_providers:
                candidates = model_providers
        
        # Load balancing: select provider with least usage
        if candidates:
            return min(candidates, key=lambda p: self._provider_usage.get(p, 0))
        
        return None
    
    def _provider_supports_model(self, provider_name: str, model: str) -> bool:
        """
        Check if a provider supports a model (heuristic).
        
        Args:
            provider_name: Provider name
            model: Model name
            
        Returns:
            True if provider likely supports the model
        """
        # Simple heuristic based on model name patterns
        model_patterns = {
            'openai': ['gpt-', 'text-', 'davinci', 'curie', 'babbage', 'ada'],
            'anthropic': ['claude-', 'claude'],
            'google': ['gemini-', 'palm-', 'bison'],
            'openrouter': ['openai/', 'anthropic/', 'google/', 'meta/'],
            'ollama': ['llama', 'mistral', 'codellama', 'vicuna'],
            'mistral': ['mistral-', 'mixtral-']
        }
        
        patterns = model_patterns.get(provider_name, [])
        return any(pattern in model.lower() for pattern in patterns)
    
    async def generate_text(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        use_cache: bool = True,
        retry_on_failure: bool = True
    ) -> GenerationResponse:
        """
        Generate text using the best available provider.
        
        Args:
            messages: List of conversation messages
            model: Model name
            provider: Specific provider to use
            config: Generation configuration
            use_cache: Whether to use caching
            retry_on_failure: Whether to retry with other providers on failure
            
        Returns:
            GenerationResponse
            
        Raises:
            ProviderError: If no providers available or all fail
        """
        # Generate cache key
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(messages, model, config)
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug("Returning cached result")
                return cached_result
        
        # Select provider
        if not provider:
            provider = self.select_provider(model)
        
        if not provider:
            raise ProviderError("selection", "No available providers")
        
        # Try primary provider
        try:
            result = await self._generate_with_provider(provider, messages, model, config)
            
            # Cache result
            if use_cache and cache_key:
                self.cache_manager.set(cache_key, result, ttl=3600)
            
            # Update usage stats
            self._provider_usage[provider] = self._provider_usage.get(provider, 0) + 1
            
            return result
            
        except Exception as e:
            logger.error(f"Generation failed with provider {provider}: {e}")
            self._provider_errors[provider] = self._provider_errors.get(provider, 0) + 1
            
            # Try fallback providers if retry is enabled
            if retry_on_failure:
                available_providers = self.get_available_providers()
                fallback_providers = [p for p in available_providers if p != provider]
                
                for fallback_provider in fallback_providers:
                    try:
                        logger.info(f"Trying fallback provider: {fallback_provider}")
                        result = await self._generate_with_provider(
                            fallback_provider, messages, model, config
                        )
                        
                        # Cache result
                        if use_cache and cache_key:
                            self.cache_manager.set(cache_key, result, ttl=3600)
                        
                        # Update usage stats
                        self._provider_usage[fallback_provider] = (
                            self._provider_usage.get(fallback_provider, 0) + 1
                        )
                        
                        return result
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback provider {fallback_provider} also failed: {fallback_error}")
                        self._provider_errors[fallback_provider] = (
                            self._provider_errors.get(fallback_provider, 0) + 1
                        )
                        continue
            
            # All providers failed
            raise ProviderError("generation", f"All providers failed. Last error: {e}")
    
    async def generate_text_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using streaming.
        
        Args:
            messages: List of conversation messages
            model: Model name
            provider: Specific provider to use
            config: Generation configuration
            
        Yields:
            Text chunks
            
        Raises:
            ProviderError: If no providers available or generation fails
        """
        # Select provider
        if not provider:
            provider = self.select_provider(model)
        
        if not provider:
            raise ProviderError("selection", "No available providers")
        
        # Check rate limit
        if not await self.rate_limiter.acquire_async(provider, timeout=30):
            raise ProviderError(provider, "Rate limit exceeded")
        
        provider_instance = self._providers[provider]
        
        try:
            async for chunk in provider_instance.generate_text_stream(messages, model, config):
                yield chunk
            
            # Update usage stats
            self._provider_usage[provider] = self._provider_usage.get(provider, 0) + 1
            
        except Exception as e:
            logger.error(f"Streaming generation failed with provider {provider}: {e}")
            self._provider_errors[provider] = self._provider_errors.get(provider, 0) + 1
            raise ProviderError(provider, f"Streaming generation failed: {e}")
    
    async def _generate_with_provider(
        self,
        provider_name: str,
        messages: List[Message],
        model: Optional[str],
        config: Optional[GenerationConfig]
    ) -> GenerationResponse:
        """Generate text with a specific provider."""
        # Check rate limit
        if not await self.rate_limiter.acquire_async(provider_name, timeout=30):
            raise ProviderError(provider_name, "Rate limit exceeded")
        
        provider = self._providers[provider_name]
        
        # Use default model if none specified
        if not model:
            provider_config = self.config.get_provider_config(provider_name)
            model = provider_config.default_model
        
        if not model:
            raise ProviderError(provider_name, "No model specified and no default model configured")
        
        # Execute with retry logic
        return await self.retry_manager.execute_async(
            provider.generate_text,
            messages,
            model,
            config
        )
    
    def _generate_cache_key(
        self,
        messages: List[Message],
        model: Optional[str],
        config: Optional[GenerationConfig]
    ) -> str:
        """Generate cache key for a request."""
        import hashlib
        import json
        
        # Create a deterministic representation
        cache_data = {
            'messages': [(m.role.value, m.content) for m in messages],
            'model': model,
            'config': config.__dict__ if config else None
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    async def health_check(self, provider_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on providers.
        
        Args:
            provider_name: Specific provider or None for all
            
        Returns:
            Health check results
        """
        results = {}
        
        providers_to_check = [provider_name] if provider_name else list(self._providers.keys())
        
        for name in providers_to_check:
            if name not in self._providers:
                continue
            
            provider = self._providers[name]
            
            try:
                start_time = datetime.now()
                health_info = await provider.health_check()
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Update status
                status = self._provider_status[name]
                status.available = health_info.get('status') == 'healthy'
                status.response_time = response_time
                status.last_check = datetime.now()
                status.error_message = health_info.get('error')
                
                results[name] = {
                    **health_info,
                    'response_time': response_time,
                    'usage_count': self._provider_usage.get(name, 0),
                    'error_count': self._provider_errors.get(name, 0)
                }
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                
                # Update status
                status = self._provider_status[name]
                status.available = False
                status.error_message = str(e)
                status.last_check = datetime.now()
                
                results[name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'usage_count': self._provider_usage.get(name, 0),
                    'error_count': self._provider_errors.get(name, 0)
                }
        
        return results
    
    def get_provider_status(self, provider_name: Optional[str] = None) -> Dict[str, ProviderStatus]:
        """
        Get status of providers.
        
        Args:
            provider_name: Specific provider or None for all
            
        Returns:
            Provider status information
        """
        if provider_name:
            return {provider_name: self._provider_status.get(provider_name)}
        return self._provider_status.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider manager statistics."""
        total_usage = sum(self._provider_usage.values())
        total_errors = sum(self._provider_errors.values())
        
        return {
            'total_providers': len(self._providers),
            'available_providers': len(self.get_available_providers()),
            'total_usage': total_usage,
            'total_errors': total_errors,
            'error_rate': total_errors / total_usage if total_usage > 0 else 0,
            'provider_usage': self._provider_usage.copy(),
            'provider_errors': self._provider_errors.copy(),
            'cache_stats': self.cache_manager.get_stats(),
            'rate_limiter_stats': self.rate_limiter.get_stats(),
            'retry_stats': self.retry_manager.get_stats()
        }
    
    def reload_config(self):
        """Reload configuration and reinitialize providers."""
        try:
            self.logger.info("Reloading provider configuration...")
            
            # Reload the configuration
            if hasattr(self.config, 'load'):
                self.config.load()
            
            # Clear existing providers
            self._providers.clear()
            self._provider_status.clear()
            self._provider_usage.clear()
            self._provider_errors.clear()
            
            # Reinitialize providers with new config
            self._initialize_providers()
            
            self.logger.info("Provider configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload config: {e}")
            raise ProviderError("config_reload", f"Failed to reload configuration: {e}")
    
    def is_connected(self):
        """Check if the current provider is connected and ready."""
        try:
            # Check if we have any available providers
            available_providers = self.get_available_providers()
            if not available_providers:
                return False
            
            # Check if at least one provider has valid configuration
            for provider_name in available_providers:
                provider_config = self.config.get_provider_config(provider_name)
                
                # For Ollama, check server availability instead of API key
                if provider_name == 'ollama':
                    # Ollama is considered connected if it's enabled and potentially reachable
                    if self.config.is_provider_enabled(provider_name):
                        # Check if we have a provider instance and it's been authenticated
                        if provider_name in self._providers:
                            provider_status = self._provider_status.get(provider_name)
                            if provider_status and provider_status.available:
                                return True
                        # If no status yet, consider it potentially connected if enabled
                        return True
                # For providers that need API keys, check if they have one
                elif provider_name in ['openai', 'anthropic', 'google', 'mistral', 'openrouter']:
                    if hasattr(provider_config, 'api_key') and provider_config.api_key:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking connection status: {e}")
            return False
    
    @property
    def current_provider(self):
        """Get the current/default provider instance."""
        try:
            # Try to get the default provider from config
            default_provider = getattr(self.config, 'default_provider', None)
            if default_provider and default_provider in self._providers:
                return self._providers[default_provider]
            
            # Fall back to first available provider
            available_providers = self.get_available_providers()
            if available_providers:
                return self._providers[available_providers[0]]
            
            return None
            
        except Exception:
            return None
    
    @property
    def logger(self):
        """Get the logger instance."""
        return logger
    
    def cleanup(self):
        """Clean up provider manager resources (synchronous version of shutdown)."""
        try:
            logger.info("Cleaning up provider manager...")
            
            # Save cache
            if hasattr(self, 'cache_manager') and self.cache_manager:
                self.cache_manager.save()
            
            # Clear providers
            if hasattr(self, '_providers'):
                self._providers.clear()
            if hasattr(self, '_provider_status'):
                self._provider_status.clear()
            
            logger.info("Provider manager cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during provider manager cleanup: {e}")

    async def shutdown(self):
        """Shutdown the provider manager."""
        logger.info("Shutting down provider manager...")
        
        # Save cache
        self.cache_manager.save()
        
        # Clear providers
        self._providers.clear()
        self._provider_status.clear()
        
        logger.info("Provider manager shutdown complete")
    
    def get_current_provider(self) -> Optional[str]:
        """Get the name of the current/default provider."""
        try:
            # Try to get the default provider from config
            default_provider = getattr(self.config, 'default_provider', None)
            if default_provider and default_provider in self._providers:
                return default_provider
            
            # Fall back to first available provider
            available_providers = self.get_available_providers()
            if available_providers:
                return available_providers[0]
            
            return None
            
        except Exception:
            return None
    
    def set_current_provider(self, provider_name: str):
        """Set the current provider."""
        try:
            if provider_name in self._providers:
                # Update config with new default provider
                if hasattr(self.config, 'set'):
                    self.config.set('default_provider', provider_name)
                else:
                    # Fallback: set attribute directly
                    setattr(self.config, 'default_provider', provider_name)
                logger.info(f"Set current provider to: {provider_name}")
            else:
                raise ProviderError(provider_name, "Provider not found")
        except Exception as e:
            logger.error(f"Failed to set current provider: {e}")
            raise
    
    def get_default_model(self, provider_name: str) -> str:
        """Get the default model for a provider."""
        try:
            provider_config = self.config.get_provider_config(provider_name)
            return getattr(provider_config, 'default_model', '')
        except Exception:
            # Return a reasonable default based on provider
            defaults = {
                'openai': 'gpt-3.5-turbo',
                'anthropic': 'claude-3-sonnet',
                'google': 'gemini-pro',
                'ollama': 'llama2',
                'mistral': 'mistral-tiny',
                'openrouter': 'openai/gpt-3.5-turbo'
            }
            return defaults.get(provider_name.lower(), '')
    
    def set_current_model(self, model_name: str):
        """Set the current model for the active provider."""
        try:
            current_provider = self.get_current_provider()
            if current_provider:
                # Update provider config with new default model
                if hasattr(self.config, 'set'):
                    self.config.set(f'providers.{current_provider}.default_model', model_name)
                logger.info(f"Set current model to: {model_name} for provider: {current_provider}")
            else:
                raise ProviderError("selection", "No current provider set")
        except Exception as e:
            logger.error(f"Failed to set current model: {e}")
            raise
    
    def generate_response(self, prompt: str) -> str:
        """Generate a response using the current provider (synchronous wrapper)."""
        try:
            import asyncio
            
            # Get current provider
            current_provider = self.get_current_provider()
            if not current_provider:
                raise ProviderError("selection", "No current provider available")
            
            # Get default model for provider
            default_model = self.get_default_model(current_provider)
            if not default_model:
                raise ProviderError(current_provider, "No default model configured")
            
            # Create message
            from .base_provider import Message, MessageRole
            messages = [Message(role=MessageRole.USER, content=prompt)]
            
            # Run async generation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    self.generate_text(messages, default_model, current_provider)
                )
                return response.content
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise ProviderError("generation", f"Response generation failed: {e}")