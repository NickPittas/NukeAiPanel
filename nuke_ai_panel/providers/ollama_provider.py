"""
Ollama provider implementation for Nuke AI Panel.

Provides integration with Ollama for running local AI models.
"""

import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
import json

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    # Create minimal fallback classes
    class aiohttp:
        class ClientConnectorError(Exception):
            pass
        class ClientError(Exception):
            pass
        class ClientTimeout:
            def __init__(self, total=None):
                pass
        class ClientSession:
            def __init__(self, *args, **kwargs):
                pass
            def __aenter__(self):
                return self
            def __aexit__(self, *args):
                pass
            def get(self, url):
                return self
            def post(self, url, json=None):
                return self
            async def json(self):
                return {}
            async def text(self):
                return ""
            @property
            def status(self):
                return 404
            @property
            def content(self):
                return []
            @property
            def closed(self):
                return True
            async def close(self):
                pass

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
    ModelNotFoundError
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseProvider):
    """
    Ollama provider implementation.
    
    Provides access to locally running AI models through Ollama,
    including Llama, Mistral, CodeLlama, and other open-source models.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Ollama provider.
        
        Args:
            name: Provider name
            config: Configuration including endpoint URL
        """
        super().__init__(name, config)
        
        # Check if aiohttp library is available
        if not HAS_AIOHTTP:
            raise ProviderError(name, "aiohttp library not installed. Install with: pip install aiohttp")
        
        self.base_url = config.get('base_url', 'http://localhost:11434')
        
        # Set timeout based on configuration or use model-specific defaults
        self.default_timeout = config.get('timeout', 120)  # Default timeout for most models
        self.large_model_timeout = config.get('large_model_timeout', 300)  # 5 minutes for large models
        self.timeout = self.default_timeout  # Initial timeout value
        
        # Ollama typically doesn't require API keys for local usage
        self.api_key = config.get('api_key')  # Optional
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
        
        # HTTP session for reuse
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper resource management."""
        if self._session is None or self._session.closed:
            headers = {'Content-Type': 'application/json'}
            
            # Add API key if provided (optional for Ollama)
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
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
    
    async def _create_temp_session(self) -> aiohttp.ClientSession:
        """Create a temporary session for one-time use."""
        headers = {'Content-Type': 'application/json'}
        
        # Add API key if provided (optional for Ollama)
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Use connector with proper cleanup settings
        # Note: keepalive_timeout cannot be used with force_close=True
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            enable_cleanup_closed=True,
            force_close=True
        )
        session = aiohttp.ClientSession(
            headers=headers,
            connector=connector
        )
        
        # Add provider name attribute for better tracking
        session._provider_name = f"{self.name}-temp"
        
        # Register the session with the event loop manager
        from ..utils.event_loop_manager import register_session
        register_session(session, f"{self.name}-temp")
        
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Ollama API.
        
        For Ollama, this checks if the service is running and accessible.
        No API key is required for local Ollama instances.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        session = None
        try:
            # Create temporary session with proper cleanup
            session = await self._create_temp_session()
            
            # Use asyncio.wait_for for timeout instead of ClientTimeout
            response = await asyncio.wait_for(
                session.get(f'{self.base_url}/api/tags'),
                timeout=self.timeout
            )
            async with response:
                if response.status == 200:
                    self._authenticated = True
                    logger.info(f"Ollama connection successful at {self.base_url}")
                    return True
                else:
                    self._authenticated = False
                    raise AuthenticationError(self.name, f"Ollama server not accessible: HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Connection timed out after {self.timeout} seconds")
        except aiohttp.ClientConnectorError:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        except aiohttp.ClientError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Network error connecting to Ollama: {e}")
        except Exception as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Ollama connection failed: {e}")
        finally:
            # Ensure session is properly closed
            if session and not session.closed:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of ModelInfo objects
            
        Raises:
            ProviderError: If unable to fetch models
            AuthenticationError: If not authenticated
        """
        # Try to authenticate if not already authenticated
        if not self._authenticated:
            try:
                await self.authenticate()
            except Exception as auth_error:
                logger.warning(f"Ollama authentication failed: {auth_error}")
                # Return fallback models if authentication fails
                return self._get_fallback_models()
        
        if self._models_cache:
            return self._models_cache
        
        session = None
        try:
            # Create temporary session with proper cleanup
            session = await self._create_temp_session()
            
            response = await asyncio.wait_for(
                session.get(f'{self.base_url}/api/tags'),
                timeout=self.timeout
            )
            async with response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch Ollama models: HTTP {response.status}")
                    return self._get_fallback_models()
                
                data = await response.json()
                models = []
                
                # Store model names for mapping
                self._available_model_names = []
                
                for model_data in data.get('models', []):
                    # Extract model information
                    model_name = model_data.get('name', '')
                    model_size = model_data.get('size', 0)
                    modified_at = model_data.get('modified_at', '')
                    
                    # Add to available models list
                    self._available_model_names.append(model_name)
                    
                    # Skip embedding models that don't support text generation
                    if self._is_embedding_model(model_name):
                        logger.debug(f"Skipping embedding model: {model_name}")
                        continue
                    
                    # Estimate context window and max tokens based on model name
                    context_window, max_tokens = self._estimate_model_limits(model_name)
                    
                    model_info = ModelInfo(
                        name=model_name,
                        display_name=model_name.replace(':', ' ').title(),
                        description=f"Local Ollama model: {model_name}",
                        max_tokens=max_tokens,
                        supports_streaming=True,
                        supports_functions=False,  # Most Ollama models don't support function calling
                        context_window=context_window,
                        metadata={
                            'provider': 'ollama',
                            'size': model_size,
                            'modified_at': modified_at,
                            'digest': model_data.get('digest', ''),
                            'details': model_data.get('details', {})
                        }
                    )
                    models.append(model_info)
                
                if models:
                    self._models_cache = models
                    logger.debug(f"Retrieved {len(models)} Ollama models")
                    logger.info(f"Available Ollama models: {', '.join(self._available_model_names[:10])}...")
                    return models
                else:
                    logger.warning("No models returned from Ollama API, using fallback models")
                    return self._get_fallback_models()
                    
        except asyncio.TimeoutError:
            logger.warning(f"Request timed out after {self.timeout} seconds, using fallback models")
            return self._get_fallback_models()
        except aiohttp.ClientConnectorError:
            logger.warning("Cannot connect to Ollama server, using fallback models")
            return self._get_fallback_models()
        except aiohttp.ClientError as e:
            logger.warning(f"Network error fetching Ollama models: {e}, using fallback models")
            return self._get_fallback_models()
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}, using fallback models")
            return self._get_fallback_models()
        finally:
            # Ensure session is properly closed
            if session and not session.closed:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
    
    def _get_fallback_models(self) -> List[ModelInfo]:
        """Get fallback models when Ollama server is not available."""
        # Common models that are likely to be available
        fallback_models = [
            ModelInfo(
                name="llama2",
                display_name="Llama 2",
                description="Meta's Llama 2 model (fallback)",
                max_tokens=2048,
                supports_streaming=True,
                supports_functions=False,
                context_window=4096,
                metadata={'provider': 'ollama', 'fallback': True}
            ),
            ModelInfo(
                name="mistral",
                display_name="Mistral",
                description="Mistral AI model (fallback)",
                max_tokens=4096,
                supports_streaming=True,
                supports_functions=False,
                context_window=8192,
                metadata={'provider': 'ollama', 'fallback': True}
            ),
            ModelInfo(
                name="phi",
                display_name="Phi",
                description="Microsoft Phi model (fallback)",
                max_tokens=2048,
                supports_streaming=True,
                supports_functions=False,
                context_window=4096,
                metadata={'provider': 'ollama', 'fallback': True}
            ),
            ModelInfo(
                name="neural-chat",
                display_name="Neural Chat",
                description="Intel Neural Chat model (fallback)",
                max_tokens=2048,
                supports_streaming=True,
                supports_functions=False,
                context_window=4096,
                metadata={'provider': 'ollama', 'fallback': True}
            )
        ]
        
        logger.info(f"Using {len(fallback_models)} fallback Ollama models")
        return fallback_models
    
    def _estimate_model_limits(self, model_name: str) -> tuple[int, int]:
        """
        Estimate context window and max tokens based on model name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Tuple of (context_window, max_tokens)
        """
        model_name_lower = model_name.lower()
        
        # Common model patterns and their typical limits
        if 'llama2' in model_name_lower:
            if '70b' in model_name_lower:
                return 4096, 2048
            elif '13b' in model_name_lower:
                return 4096, 2048
            else:  # 7b and smaller
                return 4096, 2048
        elif 'llama' in model_name_lower:
            if '70b' in model_name_lower:
                return 8192, 4096
            elif '13b' in model_name_lower:
                return 8192, 4096
            else:
                return 8192, 4096
        elif 'mistral' in model_name_lower:
            return 8192, 4096
        elif 'codellama' in model_name_lower:
            return 16384, 8192
        elif 'vicuna' in model_name_lower:
            return 4096, 2048
        elif 'orca' in model_name_lower:
            return 4096, 2048
        else:
            # Default fallback
            return 4096, 2048
    
    def _is_embedding_model(self, model_name: str) -> bool:
        """
        Check if a model is an embedding model that doesn't support text generation.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if it's an embedding model, False otherwise
        """
        model_name_lower = model_name.lower()
        
        # Common embedding model patterns
        embedding_patterns = [
            'embed',
            'embedding',
            'sentence-transformer',
            'nomic-embed',
            'all-minilm',
            'bge-',
            'e5-'
        ]
        
        return any(pattern in model_name_lower for pattern in embedding_patterns)
    
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using Ollama API.
        
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
        # Auto-authenticate if not already authenticated
        if not self._authenticated:
            try:
                await self.authenticate()
            except Exception as e:
                raise AuthenticationError(self.name, f"Failed to authenticate: {e}")
        
        self._validate_messages(messages)
        config = self._validate_config(config)
        
        # Map model to available model if needed
        model = await self._map_model_to_available(model)
        
        # Adjust timeout based on model size
        self._adjust_timeout_for_model(model)
        
        try:
            session = await self._get_session()
            
            # Convert messages to Ollama format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare request payload
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': config.temperature,
                    'top_p': config.top_p,
                    'num_predict': config.max_tokens or -1,  # -1 means no limit
                }
            }
            
            # Add stop sequences if provided
            if config.stop_sequences:
                payload['options']['stop'] = config.stop_sequences
            
            # Make API call with timeout
            response = await asyncio.wait_for(
                session.post(f'{self.base_url}/api/generate', json=payload),
                timeout=self.timeout
            )
            async with response:
                if response.status == 404:
                    raise ModelNotFoundError(self.name, model)
                elif response.status != 200:
                    error_text = await response.text()
                    raise APIError(self.name, response.status, f"API call failed: {error_text}")
                
                data = await response.json()
                
                # Extract response data
                content = data.get('response', '')
                
                # Create usage info (Ollama doesn't provide detailed token counts)
                usage = {
                    'prompt_tokens': 0,  # Not available from Ollama
                    'completion_tokens': 0,  # Not available from Ollama
                    'total_tokens': 0  # Not available from Ollama
                }
                
                return GenerationResponse(
                    content=content,
                    model=model,
                    usage=usage,
                    finish_reason="stop" if data.get('done', False) else "length",
                    metadata={
                        'created_at': data.get('created_at'),
                        'total_duration': data.get('total_duration'),
                        'load_duration': data.get('load_duration'),
                        'prompt_eval_count': data.get('prompt_eval_count'),
                        'prompt_eval_duration': data.get('prompt_eval_duration'),
                        'eval_count': data.get('eval_count'),
                        'eval_duration': data.get('eval_duration')
                    }
                )
                
        except asyncio.TimeoutError:
            raise APIError(self.name, message=f"Request timed out after {self.timeout} seconds")
        except aiohttp.ClientError as e:
            raise APIError(self.name, message=f"Network error: {e}")
        except (ModelNotFoundError, APIError):
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
        Generate text using Ollama streaming API.
        
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
        # Auto-authenticate if not already authenticated
        if not self._authenticated:
            try:
                await self.authenticate()
            except Exception as e:
                raise AuthenticationError(self.name, f"Failed to authenticate: {e}")
        
        self._validate_messages(messages)
        config = self._validate_config(config)
        
        # Map model to available model if needed
        model = await self._map_model_to_available(model)
        
        # Adjust timeout based on model size
        self._adjust_timeout_for_model(model)
        
        try:
            session = await self._get_session()
            
            # Convert messages to Ollama format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare request payload
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': True,
                'options': {
                    'temperature': config.temperature,
                    'top_p': config.top_p,
                    'num_predict': config.max_tokens or -1,
                }
            }
            
            # Add stop sequences if provided
            if config.stop_sequences:
                payload['options']['stop'] = config.stop_sequences
            
            # Make streaming API call with timeout
            response = await asyncio.wait_for(
                session.post(f'{self.base_url}/api/generate', json=payload),
                timeout=self.timeout
            )
            async with response:
                if response.status == 404:
                    raise ModelNotFoundError(self.name, model)
                elif response.status != 200:
                    error_text = await response.text()
                    raise APIError(self.name, response.status, f"Streaming API call failed: {error_text}")
                
                # Process streaming response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line:
                        try:
                            data = json.loads(line)
                            
                            if 'response' in data:
                                content = data['response']
                                if content:
                                    yield content
                            
                            # Check if generation is done
                            if data.get('done', False):
                                break
                                
                        except json.JSONDecodeError:
                            continue  # Skip malformed JSON
                
        except asyncio.TimeoutError:
            raise APIError(self.name, message=f"Streaming request timed out after {self.timeout} seconds")
        except aiohttp.ClientError as e:
            raise APIError(self.name, message=f"Network error: {e}")
        except (ModelNotFoundError, APIError):
            raise
        except Exception as e:
            raise APIError(self.name, message=f"Streaming API call failed: {e}")
    
    def _convert_messages_to_prompt(self, messages: List[Message]) -> str:
        """
        Convert internal message format to Ollama prompt format.
        
        Args:
            messages: List of Message objects
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                prompt_parts.append(f"System: {message.content}")
            elif message.role == MessageRole.USER:
                prompt_parts.append(f"Human: {message.content}")
            elif message.role == MessageRole.ASSISTANT:
                prompt_parts.append(f"Assistant: {message.content}")
        
        # Add a final prompt for the assistant to respond
        if not prompt_parts or not prompt_parts[-1].startswith("Human:"):
            prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
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
        Perform a health check on the Ollama provider.
        
        Returns:
            Dictionary with health status information
        """
        session = None
        try:
            # Create temporary session with proper cleanup
            session = await self._create_temp_session()
            
            # Use the managed event loop for timeout
            response = await asyncio.wait_for(
                session.get(f'{self.base_url}/api/tags'),
                timeout=self.timeout
            )
            async with response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('models', []))
                    
                    return {
                        'status': 'healthy',
                        'authenticated': self._authenticated,
                        'models_available': model_count,
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
                'error': f'Health check timed out after {self.timeout} seconds',
                'authenticated': self._authenticated,
                'timestamp': str((get_event_loop_manager().get_loop() or asyncio.get_event_loop()).time())
            }
        except aiohttp.ClientConnectorError:
            return {
                'status': 'unhealthy',
                'error': 'Cannot connect to Ollama. Is Ollama running?',
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
        finally:
            # Ensure session is properly closed
            if session and not session.closed:
                try:
                    await session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {e}")
    
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
        
    def _adjust_timeout_for_model(self, model: str):
        """
        Adjust timeout based on model size and complexity.
        
        Args:
            model: Model name
        """
        model_lower = model.lower()
        
        # Large models that need longer timeouts
        large_models = [
            'deepseek-coder',
            '33b',
            '70b',
            'llama3-70b',
            'mixtral-8x7b',
            'llama2-70b',
            'codellama-70b',
            'wizardcoder',
            'dolphin-mixtral'
        ]
        
        # Check if the model is a large model
        if any(large_model in model_lower for large_model in large_models):
            logger.info(f"Using extended timeout ({self.large_model_timeout}s) for large model: {model}")
            self.timeout = self.large_model_timeout
        else:
            # Reset to default timeout for smaller models
            self.timeout = self.default_timeout
            logger.debug(f"Using standard timeout ({self.default_timeout}s) for model: {model}")
            
    async def _map_model_to_available(self, model: str) -> str:
        """
        Map a requested model to an available Ollama model.
        
        Args:
            model: The requested model name
            
        Returns:
            An available model name that best matches the request
            
        Raises:
            ModelNotFoundError: If no suitable model can be found
        """
        # If we don't have available models yet, try to fetch them
        if not hasattr(self, '_available_model_names') or not self._available_model_names:
            try:
                await self.get_models()
            except Exception as e:
                logger.warning(f"Failed to fetch available models: {e}")
                # If we can't fetch models, use the original model name
                return model
        
        # If the model is already available, use it directly
        if hasattr(self, '_available_model_names') and model in self._available_model_names:
            return model
            
        # Common model mappings
        model_mapping = {
            # Standard mappings
            'gpt-3.5-turbo': ['llama2', 'mistral', 'neural-chat', 'phi'],
            'gpt-4': ['llama2:70b', 'llama2:13b', 'mixtral', 'mistral-large'],
            'claude': ['mistral', 'llama2', 'neural-chat'],
            
            # Mistral models
            'mistral-tiny': ['mistral', 'mistral:7b', 'mistral-openorca'],
            'mistral-small': ['mistral', 'mistral:7b', 'mistral-openorca'],
            'mistral-medium': ['mistral', 'mistral:7b', 'mistral-openorca'],
            'mistral-large': ['mistral', 'mistral:7b', 'mistral-openorca'],
            
            # Google models
            'gemini-pro': ['llama2', 'mistral', 'neural-chat'],
            
            # Generic fallbacks
            'llama': ['llama2', 'llama2:7b'],
            'mixtral': ['mixtral', 'mistral'],
            'codellama': ['codellama', 'llama2-code', 'codellama:7b']
        }
        
        # Try to map the model
        if model in model_mapping:
            # Try each potential mapping in order
            for potential_model in model_mapping[model]:
                if hasattr(self, '_available_model_names') and potential_model in self._available_model_names:
                    logger.info(f"Mapped model '{model}' to available Ollama model '{potential_model}'")
                    return potential_model
        
        # If we have available models, try to find a partial match
        if hasattr(self, '_available_model_names') and self._available_model_names:
            # Try to find a model that contains the requested model name
            model_lower = model.lower()
            for available_model in self._available_model_names:
                if model_lower in available_model.lower():
                    logger.info(f"Found partial match for '{model}': '{available_model}'")
                    return available_model
                    
            # Try common models that might be available
            common_models = ['llama2', 'mistral', 'neural-chat', 'phi']
            for common_model in common_models:
                if common_model in self._available_model_names:
                    logger.warning(f"Model '{model}' not found. Using common model '{common_model}' instead")
                    return common_model
                    
            # If we still haven't found a match, use the first available model
            if self._available_model_names:
                first_model = self._available_model_names[0]
                logger.warning(f"Model '{model}' not found. Using first available model '{first_model}' instead")
                return first_model
        
        # If we don't have available models or couldn't find a match, return the original model
        # and let the API handle the error
        logger.warning(f"No mapping found for model '{model}'. Using as-is.")
        return model