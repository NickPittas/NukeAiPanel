"""
Configuration management system for Nuke AI Panel.

This module handles loading, saving, and managing configuration settings
for the application and AI providers.
"""

import os
import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Try to import yaml, fall back to JSON-only mode if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False

from .exceptions import ConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    name: str
    enabled: bool = True
    default_model: Optional[str] = None
    max_retries: int = 3
    timeout: int = 30
    rate_limit: Optional[int] = None
    custom_endpoint: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None
    model_overrides: Optional[Dict[str, Any]] = None
    api_key: Optional[str] = None  # Add api_key parameter support
    temperature: Optional[float] = None  # Add temperature parameter support
    max_tokens: Optional[int] = None  # Add max_tokens parameter support
    base_url: Optional[str] = None  # Add base_url parameter support
    
    def __post_init__(self):
        if self.extra_headers is None:
            self.extra_headers = {}
        if self.model_overrides is None:
            self.model_overrides = {}


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    max_size: int = 1000
    ttl_seconds: int = 3600
    cache_dir: Optional[str] = None


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: LogLevel = LogLevel.INFO
    file_logging: bool = True
    console_logging: bool = True
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    encrypt_cache: bool = True
    api_key_rotation_days: int = 90
    max_failed_auth_attempts: int = 5
    session_timeout_minutes: int = 60


@dataclass
class UIConfig:
    """Configuration for UI settings."""
    theme: str = "dark"
    font_size: int = 12
    auto_save: bool = True
    show_token_usage: bool = True
    max_history_items: int = 100


class Config:
    """
    Main configuration manager for Nuke AI Panel.
    
    Handles loading, saving, and managing all configuration settings
    including provider configurations, logging, caching, and UI settings.
    """
    
    DEFAULT_CONFIG = {
        "version": "1.0",
        "providers": {
            "openai": {
                "name": "openai",
                "enabled": True,
                "default_model": "gpt-4",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "anthropic": {
                "name": "anthropic", 
                "enabled": True,
                "default_model": "claude-3-sonnet-20240229",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "google": {
                "name": "google",
                "enabled": True,
                "default_model": "gemini-pro",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "openrouter": {
                "name": "openrouter",
                "enabled": True,
                "default_model": "openai/gpt-4",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60,
                "custom_endpoint": "https://openrouter.ai/api/v1"
            },
            "ollama": {
                "name": "ollama",
                "enabled": True,
                "default_model": "llama2",
                "max_retries": 3,
                "timeout": 60,
                "custom_endpoint": "http://localhost:11434"
            },
            "mistral": {
                "name": "mistral",
                "enabled": True,
                "default_model": "mistral-medium",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            }
        },
        "cache": {
            "enabled": True,
            "max_size": 1000,
            "ttl_seconds": 3600
        },
        "logging": {
            "level": "INFO",
            "file_logging": True,
            "console_logging": True,
            "max_file_size": 10485760,
            "backup_count": 5
        },
        "security": {
            "encrypt_cache": True,
            "api_key_rotation_days": 90,
            "max_failed_auth_attempts": 5,
            "session_timeout_minutes": 60
        },
        "ui": {
            "theme": "dark",
            "font_size": 12,
            "auto_save": True,
            "show_token_usage": True,
            "max_history_items": 100
        }
    }
    
    def __init__(self, config_dir: Optional[Path] = None, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
            config_file: Specific config file name (defaults to config.yaml or config.json if YAML unavailable)
        """
        self.config_dir = config_dir or Path.home() / ".nuke_ai_panel"
        self.config_dir.mkdir(exist_ok=True)
        
        # Default to JSON format if YAML is not available
        if config_file is None:
            config_file = "config.yaml" if HAS_YAML else "config.json"
        
        self.config_file = self.config_dir / config_file
        self._config: Dict[str, Any] = {}
        
        # Load configuration
        self.load()
    
    def load(self):
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.suffix.lower() == '.json':
                        self._config = json.load(f)
                    elif HAS_YAML:
                        self._config = yaml.safe_load(f) or {}
                    else:
                        # Fallback: try to load as JSON even if extension is .yaml
                        try:
                            f.seek(0)
                            self._config = json.load(f)
                        except json.JSONDecodeError:
                            logger.warning("YAML not available and file is not valid JSON. Using defaults.")
                            self._config = self.DEFAULT_CONFIG.copy()
                            return
                
                # Merge with defaults to ensure all keys exist
                self._config = self._merge_configs(self.DEFAULT_CONFIG, self._config)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                # Create default configuration
                self._config = self.DEFAULT_CONFIG.copy()
                self.save()
                logger.info("Created default configuration")
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.suffix.lower() == '.json' or not HAS_YAML:
                    # Use JSON format if explicitly requested or if YAML is not available
                    json.dump(self._config, f, indent=2)
                    if not HAS_YAML and self.config_file.suffix.lower() != '.json':
                        logger.warning("YAML not available, saved configuration as JSON format")
                else:
                    yaml.dump(self._config, f, default_flow_style=False, indent=2)
            
            logger.debug(f"Saved configuration to {self.config_file}")
            
        except Exception as e:
            raise ConfigurationError("save", f"Failed to save configuration: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults."""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'providers.openai.enabled')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'providers.openai.enabled')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        logger.debug(f"Set config {key} = {value}")
    
    def get_provider_config(self, provider: str) -> ProviderConfig:
        """
        Get configuration for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            ProviderConfig object
        """
        provider_data = self.get(f"providers.{provider}", {})
        return ProviderConfig(**provider_data)
    
    def set_provider_config(self, provider: str, config: ProviderConfig):
        """
        Set configuration for a specific provider.
        
        Args:
            provider: Provider name
            config: ProviderConfig object
        """
        self.set(f"providers.{provider}", asdict(config))
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        cache_data = self.get("cache", {})
        return CacheConfig(**cache_data)
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        logging_data = self.get("logging", {})
        
        # Convert string log level to enum
        if "level" in logging_data and isinstance(logging_data["level"], str):
            try:
                logging_data["level"] = LogLevel(logging_data["level"])
            except ValueError:
                logging_data["level"] = LogLevel.INFO
        
        return LoggingConfig(**logging_data)
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration."""
        security_data = self.get("security", {})
        return SecurityConfig(**security_data)
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration."""
        ui_data = self.get("ui", {})
        return UIConfig(**ui_data)
    
    def list_providers(self) -> List[str]:
        """Get list of configured providers."""
        return list(self.get("providers", {}).keys())
    
    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a provider is enabled."""
        return self.get(f"providers.{provider}.enabled", False)
    
    def enable_provider(self, provider: str):
        """Enable a provider."""
        self.set(f"providers.{provider}.enabled", True)
    
    def disable_provider(self, provider: str):
        """Disable a provider."""
        self.set(f"providers.{provider}.enabled", False)
    
    def add_provider(self, provider: str, config: ProviderConfig):
        """
        Add a new provider configuration.
        
        Args:
            provider: Provider name
            config: ProviderConfig object
        """
        self.set_provider_config(provider, config)
        logger.info(f"Added provider configuration: {provider}")
    
    def remove_provider(self, provider: str) -> bool:
        """
        Remove a provider configuration.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider was removed, False if not found
        """
        providers = self.get("providers", {})
        if provider in providers:
            del providers[provider]
            self.set("providers", providers)
            logger.info(f"Removed provider configuration: {provider}")
            return True
        return False
    
    def validate(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate version
        version = self.get("version")
        if not version:
            errors.append("Missing configuration version")
        
        # Validate providers
        providers = self.get("providers", {})
        if not providers:
            errors.append("No providers configured")
        
        for provider_name, provider_config in providers.items():
            if not isinstance(provider_config, dict):
                errors.append(f"Invalid provider config for {provider_name}")
                continue
            
            if "name" not in provider_config:
                errors.append(f"Missing name for provider {provider_name}")
            
            if provider_config.get("timeout", 0) <= 0:
                errors.append(f"Invalid timeout for provider {provider_name}")
        
        # Validate cache config
        cache_config = self.get("cache", {})
        if cache_config.get("max_size", 0) <= 0:
            errors.append("Invalid cache max_size")
        
        if cache_config.get("ttl_seconds", 0) <= 0:
            errors.append("Invalid cache TTL")
        
        return errors
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self.save()
        logger.warning("Reset configuration to defaults")
    
    def export_config(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Export configuration.
        
        Args:
            include_sensitive: Whether to include sensitive data
            
        Returns:
            Configuration dictionary
        """
        config = self._config.copy()
        
        if not include_sensitive:
            # Remove sensitive information
            for provider in config.get("providers", {}).values():
                if "api_key" in provider:
                    provider["api_key"] = "***REDACTED***"
        
        return config
    
    def import_config(self, config_data: Dict[str, Any], merge: bool = True):
        """
        Import configuration.
        
        Args:
            config_data: Configuration data to import
            merge: Whether to merge with existing config or replace
        """
        if merge:
            self._config = self._merge_configs(self._config, config_data)
        else:
            self._config = config_data
        
        self.save()
        logger.info("Imported configuration")
    
    def backup_config(self, backup_path: Path):
        """
        Create a backup of the configuration.
        
        Args:
            backup_path: Path to save backup
        """
        try:
            import datetime
            backup_data = {
                "config": self._config,
                "version": "1.0",
                "created_at": datetime.datetime.now().isoformat()
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                if backup_path.suffix.lower() == '.json' or not HAS_YAML:
                    json.dump(backup_data, f, indent=2)
                    if not HAS_YAML and backup_path.suffix.lower() != '.json':
                        logger.warning("YAML not available, saved backup as JSON format")
                else:
                    yaml.dump(backup_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Created configuration backup at: {backup_path}")
            
        except Exception as e:
            raise ConfigurationError("backup", f"Failed to create backup: {e}")
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-style assignment."""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration."""
        return self.get(key) is not None