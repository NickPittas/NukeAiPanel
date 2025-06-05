"""
Google provider implementation for Nuke AI Panel.

Provides integration with Google's Gemini models including Gemini Pro and Ultra.
"""

import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

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


class GoogleProvider(BaseProvider):
    """
    Google provider implementation.
    
    Supports Gemini models (Pro, Ultra) with
    both standard and streaming generation.
    """
    
    # Available Gemini models with their specifications
    GEMINI_MODELS = {
        'gemini-pro': {
            'display_name': 'Gemini Pro',
            'description': 'Google\'s most capable multimodal model',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': True
        },
        'gemini-pro-vision': {
            'display_name': 'Gemini Pro Vision',
            'description': 'Gemini Pro with vision capabilities',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': False
        },
        'gemini-ultra': {
            'display_name': 'Gemini Ultra',
            'description': 'Google\'s most capable model (when available)',
            'max_tokens': 8192,
            'context_window': 32768,
            'supports_streaming': True,
            'supports_functions': True
        }
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Google provider.
        
        Args:
            name: Provider name
            config: Configuration including API key
        """
        super().__init__(name, config)
        
        self.api_key = config.get('api_key')
        
        if not self.api_key:
            raise ProviderError(name, "Google API key is required")
        
        # Configure the Google AI client
        genai.configure(api_key=self.api_key)
        
        # Model information cache
        self._models_cache: Optional[List[ModelInfo]] = None
        self._client_models: Dict[str, genai.GenerativeModel] = {}
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Google AI API.
        
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Test authentication by listing models
            models = genai.list_models()
            model_list = list(models)
            
            self._authenticated = True
            logger.info(f"Google AI authentication successful, found {len(model_list)} models")
            return True
            
        except Exception as e:
            self._authenticated = False
            if "API_KEY_INVALID" in str(e) or "authentication" in str(e).lower():
                raise AuthenticationError(self.name, f"Invalid API key: {e}")
            else:
                raise AuthenticationError(self.name, f"Authentication failed: {e}")
    
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available Google models.
        
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
            
            # Get available models from Google AI
            available_models = genai.list_models()
            available_model_names = {model.name.split('/')[-1] for model in available_models}
            
            # Filter our known models by what's actually available
            for model_id, specs in self.GEMINI_MODELS.items():
                if model_id in available_model_names:
                    model_info = ModelInfo(
                        name=model_id,
                        display_name=specs['display_name'],
                        description=specs['description'],
                        max_tokens=specs['max_tokens'],
                        supports_streaming=specs['supports_streaming'],
                        supports_functions=specs['supports_functions'],
                        context_window=specs['context_window'],
                        metadata={
                            'provider': 'google',
                            'family': 'gemini'
                        }
                    )
                    models.append(model_info)
            
            self._models_cache = models
            logger.debug(f"Retrieved {len(models)} Google models")
            return models
            
        except Exception as e:
            raise ProviderError(self.name, f"Failed to fetch models: {e}")
    
    def _get_model_client(self, model: str) -> genai.GenerativeModel:
        """Get or create a model client."""
        if model not in self._client_models:
            self._client_models[model] = genai.GenerativeModel(model)
        return self._client_models[model]
    
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using Google AI API.
        
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
            # Get model client
            model_client = self._get_model_client(model)
            
            # Convert messages to Google format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                max_output_tokens=config.max_tokens,
                stop_sequences=config.stop_sequences or []
            )
            
            # Make API call
            response = await asyncio.to_thread(
                model_client.generate_content,
                prompt,
                generation_config=generation_config,
                stream=False
            )
            
            # Extract response data
            content = response.text if response.text else ""
            
            # Create usage info (Google doesn't provide detailed token counts)
            usage = {
                'prompt_tokens': 0,  # Not available from Google AI
                'completion_tokens': 0,  # Not available from Google AI
                'total_tokens': 0  # Not available from Google AI
            }
            
            # Determine finish reason
            finish_reason = "stop"
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason).lower()
            
            return GenerationResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={
                    'safety_ratings': [
                        {
                            'category': str(rating.category),
                            'probability': str(rating.probability)
                        }
                        for rating in (response.candidates[0].safety_ratings if response.candidates else [])
                    ]
                }
            )
            
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                raise AuthenticationError(self.name, f"Invalid API key: {e}")
            elif "RATE_LIMIT_EXCEEDED" in str(e):
                raise RateLimitError(self.name)
            elif "MODEL_NOT_FOUND" in str(e):
                raise ModelNotFoundError(self.name, model)
            else:
                raise APIError(self.name, message=f"API call failed: {e}")
    
    async def generate_text_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using Google AI streaming API.
        
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
            # Get model client
            model_client = self._get_model_client(model)
            
            # Convert messages to Google format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Prepare generation config
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature,
                top_p=config.top_p,
                max_output_tokens=config.max_tokens,
                stop_sequences=config.stop_sequences or []
            )
            
            # Make streaming API call
            response_stream = await asyncio.to_thread(
                model_client.generate_content,
                prompt,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
            
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                raise AuthenticationError(self.name, f"Invalid API key: {e}")
            elif "RATE_LIMIT_EXCEEDED" in str(e):
                raise RateLimitError(self.name)
            elif "MODEL_NOT_FOUND" in str(e):
                raise ModelNotFoundError(self.name, model)
            else:
                raise APIError(self.name, message=f"Streaming API call failed: {e}")
    
    def _convert_messages_to_prompt(self, messages: List[Message]) -> str:
        """
        Convert internal message format to Google prompt format.
        
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
        Perform a health check on the Google provider.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Test with a simple model list call
            models = genai.list_models()
            model_count = len(list(models))
            
            return {
                'status': 'healthy',
                'authenticated': self._authenticated,
                'models_available': model_count,
                'api_version': 'v1',
                'timestamp': str(asyncio.get_event_loop().time())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'authenticated': self._authenticated,
                'timestamp': str(asyncio.get_event_loop().time())
            }