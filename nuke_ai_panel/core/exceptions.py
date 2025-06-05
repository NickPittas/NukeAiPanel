"""
Custom exceptions for the Nuke AI Panel system.

This module defines all custom exceptions used throughout the application
for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class NukeAIError(Exception):
    """Base exception for all Nuke AI Panel errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ProviderError(NukeAIError):
    """Exception raised when there's an error with an AI provider."""
    
    def __init__(self, provider_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.provider_name = provider_name
        super().__init__(f"Provider '{provider_name}': {message}", details)


class AuthenticationError(NukeAIError):
    """Exception raised when authentication fails."""
    
    def __init__(self, provider_name: str, message: str = "Authentication failed"):
        super().__init__(f"Authentication error for '{provider_name}': {message}")
        self.provider_name = provider_name


class ConfigurationError(NukeAIError):
    """Exception raised when there's a configuration error."""
    
    def __init__(self, config_key: str, message: str):
        super().__init__(f"Configuration error for '{config_key}': {message}")
        self.config_key = config_key


class APIError(NukeAIError):
    """Exception raised when an API call fails."""
    
    def __init__(self, provider_name: str, status_code: Optional[int] = None, 
                 message: str = "API call failed", response_data: Optional[Dict[str, Any]] = None):
        self.provider_name = provider_name
        self.status_code = status_code
        self.response_data = response_data or {}
        
        error_msg = f"API error for '{provider_name}': {message}"
        if status_code:
            error_msg += f" (Status: {status_code})"
            
        super().__init__(error_msg, {"status_code": status_code, "response": response_data})


class RateLimitError(APIError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, provider_name: str, retry_after: Optional[int] = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(provider_name, 429, message, {"retry_after": retry_after})
        self.retry_after = retry_after


class QuotaExceededError(APIError):
    """Exception raised when API quota is exceeded."""
    
    def __init__(self, provider_name: str, quota_type: str = "requests"):
        super().__init__(provider_name, 429, f"Quota exceeded for {quota_type}")
        self.quota_type = quota_type


class ModelNotFoundError(ProviderError):
    """Exception raised when a requested model is not found."""
    
    def __init__(self, provider_name: str, model_name: str):
        super().__init__(provider_name, f"Model '{model_name}' not found")
        self.model_name = model_name


class InvalidRequestError(ProviderError):
    """Exception raised when a request is invalid."""
    
    def __init__(self, provider_name: str, message: str, validation_errors: Optional[Dict[str, Any]] = None):
        super().__init__(provider_name, message, validation_errors)
        self.validation_errors = validation_errors or {}