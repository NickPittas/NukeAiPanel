"""
Ollama provider implementation for Nuke AI Panel.

Provides integration with Ollama for running local AI models.
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
        
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.timeout = config.get('timeout', 120)  # Longer timeout for local models
        
        # Ollama typically doesn't require API keys for local usage
        self.api_key = config.get('api_key')  # Optional
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
        
        # HTTP session for reuse
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            headers = {'Content-Type': 'application/json'}
            
            # Add API key if provided
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self._session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Ollama API.
        
        For Ollama, this mainly checks if the service is running and accessible.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            session = await self._get_session()
            
            # Test connection by checking if Ollama is running
            async with session.get(f'{self.base_url}/api/tags') as response:
                if response.status == 200:
                    self._authenticated = True
                    logger.info("Ollama connection successful")
                    return True
                else:
                    self._authenticated = False
                    raise AuthenticationError(self.name, f"Ollama not accessible: HTTP {response.status}")
                    
        except aiohttp.ClientConnectorError:
            self._authenticated = False
            raise AuthenticationError(self.name, "Cannot connect to Ollama. Is Ollama running?")
        except aiohttp.ClientError as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Network error: {e}")
        except Exception as e:
            self._authenticated = False
            raise AuthenticationError(self.name, f"Authentication failed: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available Ollama models.
        
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
            
            async with session.get(f'{self.base_url}/api/tags') as response:
                if response.status != 200:
                    raise ProviderError(self.name, f"Failed to fetch models: HTTP {response.status}")
                
                data = await response.json()
                models = []
                
                for model_data in data.get('models', []):
                    # Extract model information
                    model_name = model_data.get('name', '')
                    model_size = model_data.get('size', 0)
                    modified_at = model_data.get('modified_at', '')
                    
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
                
                self._models_cache = models
                logger.debug(f"Retrieved {len(models)} Ollama models")
                return models
                
        except aiohttp.ClientError as e:
            raise ProviderError(self.name, f"Network error fetching models: {e}")
        except Exception as e:
            raise ProviderError(self.name, f"Failed to fetch models: {e}")
    
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
        self._ensure_authenticated()
        self._validate_messages(messages)
        config = self._validate_config(config)
        
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
            
            # Make API call
            async with session.post(f'{self.base_url}/api/generate', json=payload) as response:
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
        self._ensure_authenticated()
        self._validate_messages(messages)
        config = self._validate_config(config)
        
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
            
            # Make streaming API call
            async with session.post(f'{self.base_url}/api/generate', json=payload) as response:
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
        try:
            session = await self._get_session()
            
            async with session.get(f'{self.base_url}/api/tags') as response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('models', []))
                    
                    return {
                        'status': 'healthy',
                        'authenticated': self._authenticated,
                        'models_available': model_count,
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
                    
        except aiohttp.ClientConnectorError:
            return {
                'status': 'unhealthy',
                'error': 'Cannot connect to Ollama. Is Ollama running?',
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