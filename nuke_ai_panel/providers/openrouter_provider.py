"""
OpenRouter provider implementation for Nuke AI Panel.

Provides integration with OpenRouter's unified API for accessing multiple AI models.
"""

import asyncio
import aiohttp
from typing import List, Optional, AsyncGenerator, Dict, Any
import json

from ..utils.event_loop_manager import get_event_loop_manager

from ..core.base_provider import (
    BaseProvider,
    Message,
    MessageRole,
    ModelInfo,
    GenerationConfig,
    GenerationResponse
)
from ..core.exceptions import (
    ProviderError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ModelNotFoundError
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OpenrouterProvider(BaseProvider):
    """
    OpenRouter provider implementation.
    
    Provides access to multiple AI models through OpenRouter's unified API
    including models from OpenAI, Anthropic, Google, Meta, and others.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize OpenRouter provider.
        
        Args:
            name: Provider name
            config: Configuration including API key
        """
        super().__init__(name, config)
        
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://openrouter.ai/api/v1')
        self.app_name = config.get('app_name', 'Nuke AI Panel')
        self.site_url = config.get('site_url', 'https://github.com/your-repo/nuke-ai-panel')
        
        if not self.api_key:
            raise ProviderError(name, "OpenRouter API key is required")
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
        
        # Provider information cache
        self._providers_info: Dict[str, Dict[str, Any]] = {}
        
        # HTTP session for reuse
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': self.site_url,
                'X-Title': self.app_name
            }
            
            # Use connector with proper cleanup settings
            # Note: keepalive_timeout cannot be used with force_close=True
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                enable_cleanup_closed=True,
                force_close=True
            )
            self._session = aiohttp.ClientSession(
                headers=headers,
                connector=connector
            )
            
            # Add provider name attribute for better tracking
            self._session._provider_name = self.name
            
            # Register the session with the event loop manager
            from ..utils.event_loop_manager import register_session
            register_session(self._session, self.name)
        
        return self._session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with OpenRouter API.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            session = await self._get_session()
            
            # Test authentication by fetching models with timeout
            # Use the managed event loop for timeout
            response = await asyncio.wait_for(
                session.get(f'{self.base_url}/models'),
                timeout=60
            )
            async with response:
                if response.status == 401:
                    self._authenticated = False
                    raise AuthenticationError(self.name, "Invalid API key")
                elif response.status == 403:
                    self._authenticated = False
                    raise AuthenticationError(self.name, "Access forbidden")
                elif response.status != 200:
                    self._authenticated = False
                    raise AuthenticationError(self.name, f"Authentication failed with status {response.status}")
                
                data = await response.json()
                model_count = len(data.get('data', []))
                
                self._authenticated = True
                logger.info(f"OpenRouter authentication successful, found {model_count} models")
                return True
                
        except asyncio.TimeoutError:
            self._authenticated = False
            raise AuthenticationError(self.name, "Authentication timed out after 60 seconds")
        except aiohttp.ClientError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Network error during authentication: {e}")
        except Exception as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available OpenRouter models.
        
        Returns:
            List of ModelInfo objects
            
        Raises:
            ProviderError: If unable to fetch models
            AuthenticationError: If not authenticated
        """
        self._ensure_authenticated()
        
        if self._models_cache:
            return self._models_cache
        
        try:
            session = await self._get_session()
            
            # Fetch models with timeout
            # Use the managed event loop for timeout
            response = await asyncio.wait_for(
                session.get(f'{self.base_url}/models'),
                timeout=60
            )
            async with response:
                if response.status == 401:
                    raise AuthenticationError(self.name, "Invalid API key")
                elif response.status != 200:
                    raise ProviderError(self.name, f"Failed to fetch models: HTTP {response.status}")
                
                data = await response.json()
                models = []
                
                # Also store model IDs for mapping
                self._model_ids = []
                
                # Store provider information
                self._providers_info = {}
                
                for model_data in data.get('data', []):
                    model_id = model_data['id']
                    self._model_ids.append(model_id)
                    
                    # Extract provider information from model ID
                    if '/' in model_id:
                        provider_name = model_id.split('/')[0]
                        if provider_name not in self._providers_info:
                            self._providers_info[provider_name] = {
                                'name': provider_name,
                                'models': [],
                                'model_count': 0
                            }
                        self._providers_info[provider_name]['models'].append(model_id)
                        self._providers_info[provider_name]['model_count'] += 1
                    
                    model_info = ModelInfo(
                        name=model_id,
                        display_name=model_data.get('name', model_id),
                        description=model_data.get('description', ''),
                        max_tokens=model_data.get('context_length', 4096),
                        supports_streaming=True,  # Most OpenRouter models support streaming
                        supports_functions=model_data.get('function_calling', False),
                        context_window=model_data.get('context_length', 4096),
                        cost_per_token=model_data.get('pricing', {}).get('prompt'),
                        metadata={
                            'provider': 'openrouter',
                            'top_provider': model_data.get('top_provider', {}),
                            'per_request_limits': model_data.get('per_request_limits'),
                            'architecture': model_data.get('architecture', {})
                        }
                    )
                    models.append(model_info)
                
                self._models_cache = models
                logger.debug(f"Retrieved {len(models)} OpenRouter models")
                logger.debug(f"Available OpenRouter model IDs: {', '.join(self._model_ids[:10])}...")
                logger.debug(f"Identified {len(self._providers_info)} unique providers through OpenRouter")
                return models
                
        except asyncio.TimeoutError:
            raise ProviderError(self.name, "Request timed out after 60 seconds while fetching models")
        except aiohttp.ClientError as e:
            raise ProviderError(self.name, f"Network error fetching models: {e}")
        except Exception as e:
            raise ProviderError(self.name, f"Failed to fetch models: {e}")
    
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using OpenRouter API.
        
        Args:
            messages: List of conversation messages
            model: Model name to use
            config: Generation configuration
            
        Returns:
            GenerationResponse object
            
        Raises:
            ProviderError: If generation fails
            AuthenticationError: If not authenticated
            APIError: If API call fails
        """
        self._ensure_authenticated()
        self._validate_messages(messages)
        config = self._validate_config(config)
        
        # Validate and map model if needed
        model = await self._validate_and_map_model(model)
        
        try:
            session = await self._get_session()
            
            # Convert messages to OpenAI-compatible format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request payload
            payload = {
                'model': model,
                'messages': openai_messages,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
                'top_p': config.top_p,
                'frequency_penalty': config.frequency_penalty,
                'presence_penalty': config.presence_penalty,
                'stream': False
            }
            
            # Add stop sequences if provided
            if config.stop_sequences:
                payload['stop'] = config.stop_sequences
            
            # Make API call with timeout
            # Use the managed event loop for timeout
            response = await asyncio.wait_for(
                session.post(f'{self.base_url}/chat/completions', json=payload),
                timeout=60
            )
            async with response:
                if response.status == 401:
                    raise AuthenticationError(self.name, "Invalid API key")
                elif response.status == 404:
                    raise ModelNotFoundError(self.name, model)
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After')
                    raise RateLimitError(self.name, retry_after=int(retry_after) if retry_after else None)
                elif response.status != 200:
                    error_text = await response.text()
                    raise APIError(self.name, response.status, f"API call failed: {error_text}")
                
                data = await response.json()
                
                # Extract response data
                choice = data['choices'][0]
                content = choice['message']['content'] or ""
                
                # Create usage info
                usage = data.get('usage', {})
                usage_info = {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
                
                return GenerationResponse(
                    content=content,
                    model=model,
                    usage=usage_info,
                    finish_reason=choice.get('finish_reason', 'stop'),
                    metadata={
                        'id': data.get('id'),
                        'created': data.get('created'),
                        'provider': data.get('provider'),
                        'model_used': data.get('model')
                    }
                )
                
        except asyncio.TimeoutError:
            raise APIError(self.name, message="Request timed out after 60 seconds")
        except aiohttp.ClientError as e:
            raise APIError(self.name, message=f"Network error: {e}")
        except (AuthenticationError, ModelNotFoundError, RateLimitError, APIError):
            raise
        except Exception as e:
            raise APIError(self.name, message=f"API call failed: {e}")
    
    async def generate_text_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using OpenRouter streaming API.
        
        Args:
            messages: List of conversation messages
            model: Model name to use
            config: Generation configuration
            
        Yields:
            Text chunks as they are generated
            
        Raises:
            ProviderError: If generation fails
            AuthenticationError: If not authenticated
            APIError: If API call fails
        """
        self._ensure_authenticated()
        self._validate_messages(messages)
        config = self._validate_config(config)
        
        # Validate and map model if needed
        model = await self._validate_and_map_model(model)
        
        try:
            session = await self._get_session()
            
            # Convert messages to OpenAI-compatible format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request payload
            payload = {
                'model': model,
                'messages': openai_messages,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
                'top_p': config.top_p,
                'frequency_penalty': config.frequency_penalty,
                'presence_penalty': config.presence_penalty,
                'stream': True
            }
            
            # Add stop sequences if provided
            if config.stop_sequences:
                payload['stop'] = config.stop_sequences
            
            # Make streaming API call with timeout
            # Use the managed event loop for timeout
            response = await asyncio.wait_for(
                session.post(f'{self.base_url}/chat/completions', json=payload),
                timeout=60
            )
            async with response:
                if response.status == 401:
                    raise AuthenticationError(self.name, "Invalid API key")
                elif response.status == 404:
                    raise ModelNotFoundError(self.name, model)
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After')
                    raise RateLimitError(self.name, retry_after=int(retry_after) if retry_after else None)
                elif response.status != 200:
                    error_text = await response.text()
                    raise APIError(self.name, response.status, f"Streaming API call failed: {error_text}")
                
                # Process streaming response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content')
                                
                                if content:
                                    yield content
                                    
                        except json.JSONDecodeError:
                            continue  # Skip malformed JSON
                
        except asyncio.TimeoutError:
            raise APIError(self.name, message="Streaming request timed out after 60 seconds")
        except aiohttp.ClientError as e:
            raise APIError(self.name, message=f"Network error: {e}")
        except (AuthenticationError, ModelNotFoundError, RateLimitError, APIError):
            raise
        except Exception as e:
            raise APIError(self.name, message=f"Streaming API call failed: {e}")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Convert internal message format to OpenAI-compatible format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of OpenAI-compatible message dictionaries
        """
        openai_messages = []
        
        for message in messages:
            openai_message = {
                'role': message.role.value,
                'content': message.content
            }
            openai_messages.append(openai_message)
        
        return openai_messages
    
    async def validate_model(self, model: str) -> bool:
        """
        Validate if a model is available.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is available, False otherwise
        """
        try:
            models = await self.get_models()
            return any(m.name == model for m in models)
        except Exception:
            return False
    
    async def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            ModelInfo object if found, None otherwise
        """
        try:
            models = await self.get_models()
            return next((m for m in models if m.name == model), None)
        except Exception:
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the OpenRouter provider.
        
        Returns:
            Dictionary with health status information
        """
        try:
            session = await self._get_session()
            
            # Health check with timeout
            # Use the managed event loop for timeout
            response = await asyncio.wait_for(
                session.get(f'{self.base_url}/models'),
                timeout=60
            )
            async with response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('data', []))
                    
                    return {
                        'status': 'healthy',
                        'authenticated': self._authenticated,
                        'models_available': model_count,
                        'api_version': 'v1',
                        'base_url': self.base_url,
                        'timestamp': str((get_event_loop_manager().get_loop() or asyncio.get_event_loop()).time())
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status}',
                        'authenticated': self._authenticated,
                        'timestamp': str((get_event_loop_manager().get_loop() or asyncio.get_event_loop()).time())
                    }
                    
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Health check timed out after 60 seconds',
                'authenticated': self._authenticated,
                'timestamp': str((get_event_loop_manager().get_loop() or asyncio.get_event_loop()).time())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'authenticated': self._authenticated,
                'timestamp': str((get_event_loop_manager().get_loop() or asyncio.get_event_loop()).time())
            }
    
    async def close(self):
        """Close the provider and clean up resources."""
        if self._session and not self._session.closed:
            try:
                logger.debug(f"Closing session for {self.name} provider")
                await self._session.close()
                self._session = None
                logger.debug(f"Session closed for {self.name} provider")
            except Exception as e:
                logger.warning(f"Error closing session for {self.name} provider: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def _validate_and_map_model(self, model: str) -> str:
        """
        Validate the model and map it to a valid OpenRouter model ID if needed.
        
        Args:
            model: The model name to validate and map
            
        Returns:
            A valid OpenRouter model ID
            
        Raises:
            ModelNotFoundError: If the model cannot be mapped to a valid ID
        """
        # If we don't have model IDs yet, fetch them
        if not hasattr(self, '_model_ids') or not self._model_ids:
            try:
                await self.get_models()
            except Exception as e:
                logger.warning(f"Failed to fetch model IDs for validation: {e}")
                # Continue with the original model name
                return model
        
        # If the model is already a valid OpenRouter ID, use it directly
        if hasattr(self, '_model_ids') and model in self._model_ids:
            return model
            
        # Map common model names to OpenRouter IDs
        model_mapping = {
            # OpenAI models
            'gpt-3.5-turbo': 'openai/gpt-3.5-turbo',
            'gpt-4': 'openai/gpt-4',
            'gpt-4-turbo': 'openai/gpt-4-turbo',
            
            # Anthropic models
            'claude-3-opus': 'anthropic/claude-3-opus',
            'claude-3-sonnet': 'anthropic/claude-3-sonnet',
            'claude-3-haiku': 'anthropic/claude-3-haiku',
            'claude-instant': 'anthropic/claude-instant-1.2',
            
            # Mistral models
            'mistral-tiny': 'mistralai/mistral-tiny',
            'mistral-small': 'mistralai/mistral-small',
            'mistral-medium': 'mistralai/mistral-medium',
            'mistral-large': 'mistralai/mistral-large-latest',
            'mixtral': 'mistralai/mixtral-8x7b',
            
            # Google models - not available on OpenRouter
            'gemini-pro': 'anthropic/claude-3-haiku',  # Fallback to Claude Haiku
        }
        
        # Try to map the model
        if model in model_mapping:
            mapped_model = model_mapping[model]
            logger.info(f"Mapped model '{model}' to OpenRouter ID '{mapped_model}'")
            return mapped_model
            
        # If we have model IDs, try to find a partial match
        if hasattr(self, '_model_ids') and self._model_ids:
            # Try to find a model ID that contains the requested model name
            for model_id in self._model_ids:
                if model.lower() in model_id.lower():
                    logger.info(f"Found partial match for '{model}': '{model_id}'")
                    return model_id
            
            # If no match found, use a default model
            default_model = 'openai/gpt-3.5-turbo'
            logger.warning(f"Model '{model}' not found in OpenRouter. Using default model '{default_model}'")
            return default_model
        
        # If we don't have model IDs, just return the original model and let the API handle it
        return model
        
    async def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all providers available through OpenRouter.
        
        This method extracts provider information from the model metadata
        returned by OpenRouter's API. It organizes providers and their
        associated models into a structured format.
        
        Returns:
            Dictionary mapping provider names to provider information
            
        Raises:
            ProviderError: If unable to fetch providers
            AuthenticationError: If not authenticated
        """
        # Ensure we have model data with provider information
        if not self._providers_info:
            # This will populate self._providers_info
            await self.get_models()
            
        if not self._providers_info:
            logger.warning("No provider information available from OpenRouter")
            return {}
            
        # Enhance provider information with additional details
        providers = {}
        for provider_name, info in self._providers_info.items():
            # Get model details for this provider
            provider_models = []
            for model_id in info['models']:
                model_info = next((m for m in self._models_cache if m.name == model_id), None)
                if model_info:
                    provider_models.append({
                        'id': model_id,
                        'name': model_info.display_name,
                        'description': model_info.description,
                        'context_window': model_info.context_window,
                        'cost_per_token': model_info.cost_per_token
                    })
            
            # Create enhanced provider info
            providers[provider_name] = {
                'name': provider_name,
                'display_name': provider_name.capitalize(),
                'model_count': info['model_count'],
                'models': provider_models,
                'capabilities': self._determine_provider_capabilities(provider_name, provider_models)
            }
            
        logger.info(f"Retrieved information for {len(providers)} providers from OpenRouter")
        return providers
        
    def _determine_provider_capabilities(self, provider_name: str, models: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Determine the capabilities of a provider based on its models.
        
        Args:
            provider_name: Provider name
            models: List of model information dictionaries
            
        Returns:
            Dictionary of capability flags
        """
        # Default capabilities
        capabilities = {
            'text_generation': True,  # All providers support basic text generation
            'streaming': True,        # Assume streaming support by default
            'function_calling': False,
            'vision': False,
            'embedding': False,
            'high_context': False     # Support for very large context windows
        }
        
        # Check for specific capabilities based on model properties
        for model in models:
            model_id = model['id']
            
            # Check for function calling support
            if 'gpt-4' in model_id or 'claude-3' in model_id:
                capabilities['function_calling'] = True
                
            # Check for vision support
            if 'vision' in model_id or '-vision' in model_id or 'gpt-4-vision' in model_id:
                capabilities['vision'] = True
                
            # Check for high context support
            if model.get('context_window', 0) > 16000:
                capabilities['high_context'] = True
                
        # Provider-specific capability adjustments
        if provider_name == 'anthropic':
            capabilities['function_calling'] = True  # Claude 3 models support function calling
            
        elif provider_name == 'openai':
            capabilities['function_calling'] = True  # Most OpenAI models support function calling
            capabilities['embedding'] = True         # OpenAI provides embedding models
            
        elif provider_name == 'google':
            capabilities['function_calling'] = True  # Gemini models support function calling
            
        return capabilities