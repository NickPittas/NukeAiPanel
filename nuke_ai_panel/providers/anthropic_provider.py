"""
Anthropic provider implementation for Nuke AI Panel.

Provides integration with Anthropic's Claude models including Claude-3 variants.
"""

import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
import anthropic
from anthropic import AsyncAnthropic

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


class AnthropicProvider(BaseProvider):
    """
    Anthropic provider implementation.
    
    Supports Claude-3 models (Opus, Sonnet, Haiku) with
    both standard and streaming generation.
    """
    
    # Available Claude models with their specifications
    CLAUDE_MODELS = {
        'claude-3-opus-20240229': {
            'display_name': 'Claude 3 Opus',
            'description': 'Most capable Claude model for complex tasks',
            'max_tokens': 4096,
            'context_window': 200000,
            'supports_streaming': True,
            'supports_functions': False
        },
        'claude-3-sonnet-20240229': {
            'display_name': 'Claude 3 Sonnet',
            'description': 'Balanced Claude model for most tasks',
            'max_tokens': 4096,
            'context_window': 200000,
            'supports_streaming': True,
            'supports_functions': False
        },
        'claude-3-haiku-20240307': {
            'display_name': 'Claude 3 Haiku',
            'description': 'Fastest Claude model for simple tasks',
            'max_tokens': 4096,
            'context_window': 200000,
            'supports_streaming': True,
            'supports_functions': False
        },
        'claude-2.1': {
            'display_name': 'Claude 2.1',
            'description': 'Previous generation Claude model',
            'max_tokens': 4096,
            'context_window': 200000,
            'supports_streaming': True,
            'supports_functions': False
        },
        'claude-2.0': {
            'display_name': 'Claude 2.0',
            'description': 'Previous generation Claude model',
            'max_tokens': 4096,
            'context_window': 100000,
            'supports_streaming': True,
            'supports_functions': False
        }
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Anthropic provider.
        
        Args:
            name: Provider name
            config: Configuration including API key
        """
        super().__init__(name, config)
        
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.anthropic.com')
        
        if not self.api_key:
            raise ProviderError(name, "Anthropic API key is required")
        
        # Initialize async client
        self.client = AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Anthropic API.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Test authentication with a minimal request
            test_message = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            self._authenticated = True
            logger.info("Anthropic authentication successful")
            return True
            
        except anthropic.AuthenticationError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Invalid API key: {e}")
        except anthropic.PermissionDeniedError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Permission denied: {e}")
        except Exception as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available Anthropic models.
        
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
            models = []
            
            for model_id, specs in self.CLAUDE_MODELS.items():
                model_info = ModelInfo(
                    name=model_id,
                    display_name=specs['display_name'],
                    description=specs['description'],
                    max_tokens=specs['max_tokens'],
                    supports_streaming=specs['supports_streaming'],
                    supports_functions=specs['supports_functions'],
                    context_window=specs['context_window'],
                    metadata={
                        'provider': 'anthropic',
                        'family': 'claude'
                    }
                )
                models.append(model_info)
            
            self._models_cache = models
            logger.debug(f"Retrieved {len(models)} Anthropic models")
            return models
            
        except Exception as e:
            raise ProviderError(self.name, f"Failed to fetch models: {e}")
    
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using Anthropic API.
        
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
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages(messages)
            
            # Prepare request parameters
            request_params = {
                'model': model,
                'messages': anthropic_messages,
                'max_tokens': config.max_tokens or 4096,
                'temperature': config.temperature,
                'top_p': config.top_p,
                'stream': False
            }
            
            # Add system message if present
            if system_message:
                request_params['system'] = system_message
            
            # Add stop sequences if provided
            if config.stop_sequences:
                request_params['stop_sequences'] = config.stop_sequences
            
            # Make API call
            response = await self.client.messages.create(**request_params)
            
            # Extract response data
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Create usage info
            usage = {
                'prompt_tokens': response.usage.input_tokens if response.usage else 0,
                'completion_tokens': response.usage.output_tokens if response.usage else 0,
                'total_tokens': (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
            }
            
            return GenerationResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=response.stop_reason or "stop",
                metadata={
                    'id': response.id,
                    'type': response.type,
                    'role': response.role
                }
            )
            
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except anthropic.RateLimitError as e:
            raise RateLimitError(self.name, retry_after=getattr(e, 'retry_after', None))
        except anthropic.NotFoundError as e:
            raise ModelNotFoundError(self.name, model)
        except anthropic.BadRequestError as e:
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
        Generate text using Anthropic streaming API.
        
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
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages(messages)
            
            # Prepare request parameters
            request_params = {
                'model': model,
                'messages': anthropic_messages,
                'max_tokens': config.max_tokens or 4096,
                'temperature': config.temperature,
                'top_p': config.top_p,
                'stream': True
            }
            
            # Add system message if present
            if system_message:
                request_params['system'] = system_message
            
            # Add stop sequences if provided
            if config.stop_sequences:
                request_params['stop_sequences'] = config.stop_sequences
            
            # Make streaming API call
            async with self.client.messages.stream(**request_params) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield event.delta.text
            
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except anthropic.RateLimitError as e:
            raise RateLimitError(self.name, retry_after=getattr(e, 'retry_after', None))
        except anthropic.NotFoundError as e:
            raise ModelNotFoundError(self.name, model)
        except anthropic.BadRequestError as e:
            raise ProviderError(self.name, f"Invalid request: {e}")
        except Exception as e:
            raise APIError(self.name, message=f"Streaming API call failed: {e}")
    
    def _convert_messages(self, messages: List[Message]) -> tuple[List[Dict[str, str]], Optional[str]]:
        """
        Convert internal message format to Anthropic format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            Tuple of (anthropic_messages, system_message)
        """
        anthropic_messages = []
        system_message = None
        
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                # Anthropic handles system messages separately
                system_message = message.content
            else:
                anthropic_message = {
                    'role': message.role.value,
                    'content': message.content
                }
                anthropic_messages.append(anthropic_message)
        
        return anthropic_messages, system_message
    
    async def validate_model(self, model: str) -> bool:
        """
        Validate if a model is available.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is available, False otherwise
        """
        return model in self.CLAUDE_MODELS
    
    async def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            ModelInfo object if found, None otherwise
        """
        if model not in self.CLAUDE_MODELS:
            return None
        
        specs = self.CLAUDE_MODELS[model]
        return ModelInfo(
            name=model,
            display_name=specs['display_name'],
            description=specs['description'],
            max_tokens=specs['max_tokens'],
            supports_streaming=specs['supports_streaming'],
            supports_functions=specs['supports_functions'],
            context_window=specs['context_window'],
            metadata={
                'provider': 'anthropic',
                'family': 'claude'
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Anthropic provider.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Test with a minimal request
            test_message = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            return {
                'status': 'healthy',
                'authenticated': self._authenticated,
                'models_available': len(self.CLAUDE_MODELS),
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