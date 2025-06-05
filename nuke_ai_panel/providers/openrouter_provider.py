"""
OpenRouter provider implementation for Nuke AI Panel.

Provides integration with OpenRouter's unified API for accessing multiple AI models.
"""

import asyncio
import aiohttp
from typing import List, Optional, AsyncGenerator, Dict, Any
import json

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
            
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
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
            
            # Test authentication by fetching models
            async with session.get(f'{self.base_url}/models') as response:
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
            
            async with session.get(f'{self.base_url}/models') as response:
                if response.status == 401:
                    raise AuthenticationError(self.name, "Invalid API key")
                elif response.status != 200:
                    raise ProviderError(self.name, f"Failed to fetch models: HTTP {response.status}")
                
                data = await response.json()
                models = []
                
                for model_data in data.get('data', []):
                    model_info = ModelInfo(
                        name=model_data['id'],
                        display_name=model_data.get('name', model_data['id']),
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
                return models
                
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
            
            # Make API call
            async with session.post(f'{self.base_url}/chat/completions', json=payload) as response:
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
            
            # Make streaming API call
            async with session.post(f'{self.base_url}/chat/completions', json=payload) as response:
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
            
            async with session.get(f'{self.base_url}/models') as response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('data', []))
                    
                    return {
                        'status': 'healthy',
                        'authenticated': self._authenticated,
                        'models_available': model_count,
                        'api_version': 'v1',
                        'base_url': self.base_url,
                        'timestamp': str(asyncio.get_event_loop().time())
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status}',
                        'authenticated': self._authenticated,
                        'timestamp': str(asyncio.get_event_loop().time())
                    }
                    
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'authenticated': self._authenticated,
                'timestamp': str(asyncio.get_event_loop().time())
            }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session and not self._session.closed:
            await self._session.close()