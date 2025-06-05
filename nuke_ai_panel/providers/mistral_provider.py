"""
Mistral provider implementation for Nuke AI Panel.

Provides integration with Mistral AI's models including Mistral 7B, Mixtral, and others.
"""

import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import ChatMessage
from mistralai.exceptions import MistralException, MistralAPIException

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


class MistralProvider(BaseProvider):
    """
    Mistral provider implementation.
    
    Supports Mistral AI models including Mistral 7B, Mixtral 8x7B,
    and other models with both standard and streaming generation.
    """
    
    # Available Mistral models with their specifications
    MISTRAL_MODELS = {
        'mistral-tiny': {
            'display_name': 'Mistral Tiny',
            'description': 'Fastest Mistral model for simple tasks',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': False
        },
        'mistral-small': {
            'display_name': 'Mistral Small',
            'description': 'Balanced Mistral model for most tasks',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': True
        },
        'mistral-medium': {
            'display_name': 'Mistral Medium',
            'description': 'More capable Mistral model',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': True
        },
        'mistral-large-latest': {
            'display_name': 'Mistral Large',
            'description': 'Most capable Mistral model',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': True
        },
        'open-mistral-7b': {
            'display_name': 'Open Mistral 7B',
            'description': 'Open source Mistral 7B model',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': False
        },
        'open-mixtral-8x7b': {
            'display_name': 'Open Mixtral 8x7B',
            'description': 'Open source Mixtral 8x7B model',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': False
        }
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Mistral provider.
        
        Args:
            name: Provider name
            config: Configuration including API key
        """
        super().__init__(name, config)
        
        self.api_key = config.get('api_key')
        self.endpoint = config.get('endpoint', 'https://api.mistral.ai')
        
        if not self.api_key:
            raise ProviderError(name, "Mistral API key is required")
        
        # Initialize async client
        self.client = MistralAsyncClient(
            api_key=self.api_key,
            endpoint=self.endpoint
        )
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Mistral API.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Test authentication by listing models
            models = await self.client.list_models()
            
            self._authenticated = True
            logger.info(f"Mistral authentication successful, found {len(models.data)} models")
            return True
            
        except MistralAPIException as e:
            self._authenticated = False
            if e.http_status == 401:
                raise AuthenticationError(self.name, f"Invalid API key: {e}")
            else:
                raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except Exception as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available Mistral models.
        
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
            # Get available models from Mistral API
            models_response = await self.client.list_models()
            available_model_ids = {model.id for model in models_response.data}
            
            models = []
            
            # Filter our known models by what's actually available
            for model_id, specs in self.MISTRAL_MODELS.items():
                if model_id in available_model_ids:
                    model_info = ModelInfo(
                        name=model_id,
                        display_name=specs['display_name'],
                        description=specs['description'],
                        max_tokens=specs['max_tokens'],
                        supports_streaming=specs['supports_streaming'],
                        supports_functions=specs['supports_functions'],
                        context_window=specs['context_window'],
                        metadata={
                            'provider': 'mistral',
                            'family': 'mistral'
                        }
                    )
                    models.append(model_info)
            
            self._models_cache = models
            logger.debug(f"Retrieved {len(models)} Mistral models")
            return models
            
        except MistralAPIException as e:
            if e.http_status == 401:
                raise AuthenticationError(self.name, f"Authentication failed: {e}")
            else:
                raise ProviderError(self.name, f"Failed to fetch models: {e}")
        except Exception as e:
            raise ProviderError(self.name, f"Failed to fetch models: {e}")
    
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using Mistral API.
        
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
            # Convert messages to Mistral format
            mistral_messages = self._convert_messages(messages)
            
            # Make API call
            response = await self.client.chat(
                model=model,
                messages=mistral_messages,
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_tokens,
                stream=False,
                safe_prompt=False  # Allow all content
            )
            
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
                    'object': response.object
                }
            )
            
        except MistralAPIException as e:
            if e.http_status == 401:
                raise AuthenticationError(self.name, f"Authentication failed: {e}")
            elif e.http_status == 404:
                raise ModelNotFoundError(self.name, model)
            elif e.http_status == 429:
                raise RateLimitError(self.name)
            else:
                raise APIError(self.name, e.http_status, f"API call failed: {e}")
        except Exception as e:
            raise APIError(self.name, message=f"API call failed: {e}")
    
    async def generate_text_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using Mistral streaming API.
        
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
            # Convert messages to Mistral format
            mistral_messages = self._convert_messages(messages)
            
            # Make streaming API call
            stream = await self.client.chat_stream(
                model=model,
                messages=mistral_messages,
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_tokens,
                safe_prompt=False
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except MistralAPIException as e:
            if e.http_status == 401:
                raise AuthenticationError(self.name, f"Authentication failed: {e}")
            elif e.http_status == 404:
                raise ModelNotFoundError(self.name, model)
            elif e.http_status == 429:
                raise RateLimitError(self.name)
            else:
                raise APIError(self.name, e.http_status, f"Streaming API call failed: {e}")
        except Exception as e:
            raise APIError(self.name, message=f"Streaming API call failed: {e}")
    
    def _convert_messages(self, messages: List[Message]) -> List[ChatMessage]:
        """
        Convert internal message format to Mistral format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of Mistral ChatMessage objects
        """
        mistral_messages = []
        
        for message in messages:
            mistral_message = ChatMessage(
                role=message.role.value,
                content=message.content
            )
            mistral_messages.append(mistral_message)
        
        return mistral_messages
    
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
        Perform a health check on the Mistral provider.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Test with a simple model list call
            models = await self.client.list_models()
            
            return {
                'status': 'healthy',
                'authenticated': self._authenticated,
                'models_available': len(models.data),
                'api_version': 'v1',
                'endpoint': self.endpoint,
                'timestamp': str(asyncio.get_event_loop().time())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'authenticated': self._authenticated,
                'timestamp': str(asyncio.get_event_loop().time())
            }