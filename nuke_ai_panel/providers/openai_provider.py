"""
OpenAI provider implementation for Nuke AI Panel.

Provides integration with OpenAI's GPT models including GPT-4, GPT-3.5, and others.
"""

import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any

try:
    import openai
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    # Create minimal fallback classes
    class AsyncOpenAI:
        def __init__(self, *args, **kwargs):
            pass
    
    class openai:
        class AuthenticationError(Exception):
            pass
        class PermissionDeniedError(Exception):
            pass
        class RateLimitError(Exception):
            pass
        class NotFoundError(Exception):
            pass
        class BadRequestError(Exception):
            pass

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


class OpenaiProvider(BaseProvider):
    """
    OpenAI provider implementation.
    
    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models with
    both standard and streaming generation.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.
        
        Args:
            name: Provider name
            config: Configuration including API key
        """
        super().__init__(name, config)
        
        # Check if OpenAI library is available
        if not HAS_OPENAI:
            raise ProviderError(name, "OpenAI library not installed. Install with: pip install openai")
        
        self.api_key = config.get('api_key')
        self.organization = config.get('organization')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        
        if not self.api_key:
            raise ProviderError(name, "OpenAI API key is required")
        
        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization,
            base_url=self.base_url
        )
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with OpenAI API.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Test authentication by listing models
            models = await self.client.models.list()
            self._authenticated = True
            logger.info(f"OpenAI authentication successful, found {len(models.data)} models")
            return True
            
        except openai.AuthenticationError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Invalid API key: {e}")
        except openai.PermissionDeniedError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Permission denied: {e}")
        except Exception as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available OpenAI models.
        
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
            models_response = await self.client.models.list()
            models = []
            
            for model in models_response.data:
                # Filter for chat models and text generation models
                if any(prefix in model.id for prefix in ['gpt-', 'text-', 'davinci', 'curie']):
                    model_info = ModelInfo(
                        name=model.id,
                        display_name=model.id.replace('-', ' ').title(),
                        description=f"OpenAI {model.id} model",
                        max_tokens=self._get_model_max_tokens(model.id),
                        supports_streaming=True,
                        supports_functions=model.id.startswith('gpt-'),
                        context_window=self._get_model_context_window(model.id),
                        metadata={
                            'created': model.created,
                            'owned_by': model.owned_by,
                            'object': model.object
                        }
                    )
                    models.append(model_info)
            
            self._models_cache = models
            logger.debug(f"Retrieved {len(models)} OpenAI models")
            return models
            
        except openai.AuthenticationError as e:
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except Exception as e:
            raise ProviderError(self.name, f"Failed to fetch models: {e}")
    
    def _get_model_max_tokens(self, model_id: str) -> int:
        """Get maximum tokens for a model."""
        token_limits = {
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-turbo': 128000,
            'gpt-4-turbo-preview': 128000,
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
            'text-davinci-003': 4097,
            'text-davinci-002': 4097,
            'text-curie-001': 2049,
            'text-babbage-001': 2049,
            'text-ada-001': 2049,
        }
        
        # Check for exact match first
        if model_id in token_limits:
            return token_limits[model_id]
        
        # Check for partial matches
        for model_prefix, limit in token_limits.items():
            if model_id.startswith(model_prefix):
                return limit
        
        # Default fallback
        return 4096
    
    def _get_model_context_window(self, model_id: str) -> int:
        """Get context window size for a model."""
        # Context window is typically the same as max tokens for OpenAI models
        return self._get_model_max_tokens(model_id)
    
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using OpenAI API.
        
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
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request parameters
            request_params = {
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
                request_params['stop'] = config.stop_sequences
            
            # Make API call
            response = await self.client.chat.completions.create(**request_params)
            
            # Extract response data
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # Create usage info
            usage = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            }
            
            return GenerationResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=choice.finish_reason or "stop",
                metadata={
                    'id': response.id,
                    'created': response.created,
                    'system_fingerprint': getattr(response, 'system_fingerprint', None)
                }
            )
            
        except openai.AuthenticationError as e:
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except openai.RateLimitError as e:
            raise RateLimitError(self.name, retry_after=getattr(e, 'retry_after', None))
        except openai.NotFoundError as e:
            raise ModelNotFoundError(self.name, model)
        except openai.BadRequestError as e:
            raise ProviderError(self.name, f"Invalid request: {e}")
        except Exception as e:
            raise APIError(self.name, message=f"API call failed: {e}")
    
    async def generate_text_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using OpenAI streaming API.
        
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
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request parameters
            request_params = {
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
                request_params['stop'] = config.stop_sequences
            
            # Make streaming API call
            stream = await self.client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except openai.AuthenticationError as e:
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except openai.RateLimitError as e:
            raise RateLimitError(self.name, retry_after=getattr(e, 'retry_after', None))
        except openai.NotFoundError as e:
            raise ModelNotFoundError(self.name, model)
        except openai.BadRequestError as e:
            raise ProviderError(self.name, f"Invalid request: {e}")
        except Exception as e:
            raise APIError(self.name, message=f"Streaming API call failed: {e}")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Convert internal message format to OpenAI format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of OpenAI message dictionaries
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
        Perform a health check on the OpenAI provider.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Test with a simple API call
            models = await self.client.models.list()
            
            return {
                'status': 'healthy',
                'authenticated': self._authenticated,
                'models_available': len(models.data),
                'api_version': 'v1',
                'base_url': self.base_url,
                'timestamp': str(asyncio.get_event_loop().time())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'authenticated': self._authenticated,
                'timestamp': str(asyncio.get_event_loop().time())
            }