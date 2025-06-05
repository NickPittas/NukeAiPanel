"""
Mistral provider implementation for Nuke AI Panel.

Provides integration with Mistral AI's models including Mistral 7B, Mixtral, and others.
"""

import asyncio
import sys
from typing import List, Optional, AsyncGenerator, Dict, Any

# Handle different versions of mistralai library
try:
    from mistralai.async_client import MistralAsyncClient
    from mistralai.models.chat_completion import ChatMessage
    from mistralai.exceptions import MistralException, MistralAPIException
except ImportError:
    try:
        # Try newer mistralai library structure
        from mistralai import Mistral as MistralAsyncClient
        from mistralai.models import ChatMessage
        from mistralai.exceptions import MistralException, MistralAPIException
    except ImportError:
        try:
            # Try alternative import structure
            from mistralai.client import MistralClient as MistralAsyncClient
            from mistralai.models import ChatMessage
            from mistralai.exceptions import MistralException, MistralAPIException
        except ImportError:
            # Final fallback - create minimal classes
            class MistralAsyncClient:
                def __init__(self, api_key, endpoint=None):
                    self.api_key = api_key
                    self.endpoint = endpoint
                async def list_models(self):
                    raise ImportError("Mistral library not properly installed")
                async def chat(self, **kwargs):
                    raise ImportError("Mistral library not properly installed")
                async def chat_stream(self, **kwargs):
                    raise ImportError("Mistral library not properly installed")
            
            class ChatMessage:
                def __init__(self, role, content):
                    self.role = role
                    self.content = content
            
            class MistralException(Exception):
                pass
            
            class MistralAPIException(Exception):
                def __init__(self, message, http_status=None):
                    super().__init__(message)
                    self.http_status = http_status

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
        
        # Log configuration (without sensitive data)
        logger.debug(f"Initializing Mistral provider with endpoint: {self.endpoint}")
        logger.debug(f"API key present: {bool(self.api_key)}")
        
        if not self.api_key:
            logger.error(f"Mistral API key is missing in configuration")
            raise ProviderError(name, "Mistral API key is required")
        
        # Validate API key format
        if len(self.api_key.strip()) < 10:
            logger.error(f"Mistral API key appears to be invalid (too short)")
            raise ProviderError(name, "Mistral API key appears to be invalid (too short)")
        
        try:
            # Initialize async client
            self.client = MistralAsyncClient(
                api_key=self.api_key,
                endpoint=self.endpoint
            )
            logger.debug(f"Mistral client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral client: {e}")
            raise ProviderError(name, f"Failed to initialize Mistral client: {e}")
        
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
            # Improved check for Mistral library and client
            try:
                import mistralai
                logger.debug(f"Mistral library found: {mistralai.__name__}")
                
                # Verify client can be imported
                try:
                    from mistralai.async_client import MistralAsyncClient as TestClient
                    logger.debug("MistralAsyncClient imported successfully")
                except ImportError:
                    try:
                        from mistralai import Mistral as TestClient
                        logger.debug("Mistral client imported successfully (newer structure)")
                    except ImportError:
                        try:
                            from mistralai.client import MistralClient as TestClient
                            logger.debug("MistralClient imported successfully (alternative structure)")
                        except ImportError:
                            self._authenticated = False
                            logger.error("Failed to import Mistral client classes")
                            logger.warning("Please run: python install_mistral_library.py")
                            return False
            except ImportError:
                self._authenticated = False
                logger.warning(f"Mistral library not properly installed. Install with: python install_mistral_library.py")
                return False
            
            # Validate API key format before attempting API call
            if not self.api_key or len(self.api_key.strip()) < 10:
                self._authenticated = False
                logger.error(f"Invalid Mistral API key format: key is missing or too short")
                raise AuthenticationError(self.name, "Invalid API key format: key is missing or too short")
                
            logger.debug(f"Attempting Mistral authentication with endpoint: {self.endpoint}")
            logger.debug(f"API key length: {len(self.api_key)}, first 4 chars: {self.api_key[:4]}...")
            
            # Test authentication by listing models with retry logic
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Create a new client instance for each retry to avoid stale connections
                    if attempt > 0:
                        logger.info(f"Retrying Mistral authentication (attempt {attempt+1}/{max_retries})")
                        self.client = MistralAsyncClient(
                            api_key=self.api_key,
                            endpoint=self.endpoint
                        )
                    
                    models = await self.client.list_models()
                    
                    self._authenticated = True
                    logger.info(f"Mistral authentication successful, found {len(models.data)} models")
                    return True
                    
                except AttributeError as attr_err:
                    # This can happen if the client is not properly initialized
                    logger.warning(f"Mistral client initialization issue on attempt {attempt+1}: {attr_err}")
                    if attempt == max_retries - 1:
                        self._authenticated = False
                        logger.error(f"Mistral client initialization failed after {max_retries} attempts")
                        logger.warning("Please reinstall the Mistral library with: python install_mistral_library.py")
                        return False
                    await asyncio.sleep(retry_delay)
                    
                except MistralAPIException as api_err:
                    # Don't retry on API errors like authentication failures
                    raise
                    
                except Exception as retry_err:
                    logger.warning(f"Unexpected error during authentication attempt {attempt+1}: {retry_err}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(retry_delay)
            
        except ImportError as e:
            self._authenticated = False
            logger.warning(f"Mistral library not properly installed: {e}")
            return False
        except MistralAPIException as e:
            self._authenticated = False
            if e.http_status == 401:
                logger.error(f"Mistral authentication failed with 401 error: {e}")
                raise AuthenticationError(self.name, f"Invalid API key: {e}")
            else:
                logger.error(f"Mistral API exception during authentication: {e}")
                raise AuthenticationError(self.name, f"Authentication failed: {e}")
        except Exception as e:
            self._authenticated = False
            # Check if the error message indicates missing library
            if "Mistral library not properly installed" in str(e):
                logger.warning(f"Mistral library not properly installed: {e}")
                return False
            
            # Log the full exception for debugging
            logger.error(f"Mistral authentication failed with unexpected error: {e}", exc_info=True)
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
            
    async def diagnose_authentication(self) -> Dict[str, Any]:
        """
        Diagnose authentication issues with detailed information.
        
        Returns:
            Dictionary with diagnostic information
        """
        results = {
            'provider': self.name,
            'api_key_present': bool(self.api_key),
            'api_key_valid_format': False,
            'endpoint': self.endpoint,
            'library_installed': False,
            'authentication_result': False,
            'errors': [],
            'models_available': 0
        }
        
        # Check API key format
        if self.api_key:
            results['api_key_valid_format'] = len(self.api_key.strip()) > 30
            results['api_key_length'] = len(self.api_key)
            # Show first and last few characters for debugging
            if len(self.api_key) > 10:
                results['api_key_preview'] = f"{self.api_key[:5]}...{self.api_key[-5:]}"
        
        # Check library installation
        try:
            import mistralai
            results['library_installed'] = True
            results['library_version'] = getattr(mistralai, "__version__", "unknown")
        except ImportError as e:
            results['errors'].append(f"Mistral library not installed: {e}")
        
        # Try authentication
        try:
            auth_result = await self.authenticate()
            results['authentication_result'] = auth_result
            
            if auth_result:
                # Try to get models
                try:
                    models = await self.get_models()
                    results['models_available'] = len(models)
                    results['model_names'] = [m.name for m in models]
                except Exception as model_error:
                    results['errors'].append(f"Failed to get models: {model_error}")
        except Exception as auth_error:
            results['errors'].append(f"Authentication failed: {auth_error}")
        
        return results