"""
Base provider class for AI service integrations.

This module defines the abstract base class that all AI providers must implement,
ensuring a consistent interface across different AI services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from .exceptions import ProviderError, AuthenticationError, APIError


class MessageRole(Enum):
    """Enumeration for message roles in conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Represents a message in a conversation."""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ModelInfo:
    """Information about an AI model."""
    name: str
    display_name: str
    description: str
    max_tokens: int
    supports_streaming: bool = True
    supports_functions: bool = False
    cost_per_token: Optional[float] = None
    context_window: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


@dataclass
class GenerationResponse:
    """Response from a text generation request."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    This class defines the interface that all AI providers must implement,
    ensuring consistency across different AI services.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the provider.
        
        Args:
            name: The name of the provider
            config: Configuration dictionary containing API keys and settings
        """
        self.name = name
        self.config = config
        self._authenticated = False
        self._models: Optional[List[ModelInfo]] = None
        self._rate_limiter = None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the provider is authenticated."""
        return self._authenticated
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the AI service.
        
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    async def get_models(self) -> List[ModelInfo]:
        """
        Get list of available models from the provider.
        
        Returns:
            List of ModelInfo objects
            
        Raises:
            ProviderError: If unable to fetch models
            AuthenticationError: If not authenticated
        """
        pass
    
    @abstractmethod
    async def generate_text(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        """
        Generate text using the specified model.
        
        Args:
            messages: List of conversation messages
            model: Model name to use for generation
            config: Generation configuration
            
        Returns:
            GenerationResponse object
            
        Raises:
            ProviderError: If generation fails
            AuthenticationError: If not authenticated
            APIError: If API call fails
        """
        pass
    
    @abstractmethod
    async def generate_text_stream(
        self,
        messages: List[Message],
        model: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using streaming.
        
        Args:
            messages: List of conversation messages
            model: Model name to use for generation
            config: Generation configuration
            
        Yields:
            Text chunks as they are generated
            
        Raises:
            ProviderError: If generation fails
            AuthenticationError: If not authenticated
            APIError: If API call fails
        """
        pass
    
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
    
    def _ensure_authenticated(self):
        """Ensure the provider is authenticated."""
        if not self._authenticated:
            raise AuthenticationError(self.name, "Provider not authenticated")
    
    def _validate_messages(self, messages: List[Message]):
        """Validate message format."""
        if not messages:
            raise ProviderError(self.name, "Messages list cannot be empty")
        
        for i, message in enumerate(messages):
            if not isinstance(message, Message):
                raise ProviderError(self.name, f"Message {i} is not a Message object")
            if not message.content.strip():
                raise ProviderError(self.name, f"Message {i} content cannot be empty")
    
    def _validate_config(self, config: Optional[GenerationConfig]) -> GenerationConfig:
        """Validate and return generation config."""
        if config is None:
            config = GenerationConfig()
        
        if not 0.0 <= config.temperature <= 2.0:
            raise ProviderError(self.name, "Temperature must be between 0.0 and 2.0")
        
        if not 0.0 <= config.top_p <= 1.0:
            raise ProviderError(self.name, "Top-p must be between 0.0 and 1.0")
        
        return config
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.
        
        Returns:
            Dictionary with health status information
        """
        try:
            await self.authenticate()
            models = await self.get_models()
            return {
                "status": "healthy",
                "authenticated": self._authenticated,
                "models_available": len(models),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "authenticated": self._authenticated,
                "timestamp": datetime.now().isoformat()
            }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', authenticated={self._authenticated})"