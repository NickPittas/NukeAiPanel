"""
Authentication and API key management system.

This module provides secure storage and retrieval of API keys using local encryption,
ensuring that sensitive credentials are protected.
"""

import os
import json
import base64
from typing import Dict, Optional, Any
from pathlib import Path
# Handle optional cryptography dependency gracefully
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    # Simple fallback - store credentials in plain text with warning
    class Fernet:
        @staticmethod
        def generate_key():
            return b"fallback_key_no_encryption"
        
        def __init__(self, key):
            pass
        
        def encrypt(self, data):
            return data
        
        def decrypt(self, data):
            return data
    
    # Minimal fallbacks for PBKDF2HMAC and hashes
    class PBKDF2HMAC:
        def __init__(self, **kwargs):
            pass
        def derive(self, password):
            return password
    
    class hashes:
        class SHA256:
            pass

from .exceptions import AuthenticationError, ConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AuthManager:
    """
    Manages authentication credentials with local encryption.
    
    This class handles secure storage and retrieval of API keys for different
    AI providers using encryption based on a master password or system-generated key.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the authentication manager.
        
        Args:
            config_dir: Directory to store encrypted credentials
        """
        self.config_dir = config_dir or Path.home() / ".nuke_ai_panel"
        self.config_dir.mkdir(exist_ok=True)
        
        self.credentials_file = self.config_dir / "credentials.enc"
        self.key_file = self.config_dir / "key.enc"
        
        self._fernet: Optional[Fernet] = None
        self._credentials: Dict[str, Dict[str, Any]] = {}
        
        # Initialize encryption
        self._initialize_encryption()
        
        # Load existing credentials
        self._load_credentials()
    
    def _initialize_encryption(self):
        """Initialize or load the encryption key."""
        if not HAS_CRYPTOGRAPHY:
            logger.warning("Cryptography not available - credentials will be stored in plain text!")
            logger.warning("Install 'cryptography' package for secure credential storage")
            self._fernet = Fernet(b"fallback_key")
            return
            
        try:
            if self.key_file.exists():
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key_data = f.read()
                self._fernet = Fernet(key_data)
                logger.debug("Loaded existing encryption key")
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                self._fernet = Fernet(key)
                logger.info("Generated new encryption key")
                
                # Set restrictive permissions on key file
                os.chmod(self.key_file, 0o600)
                
        except Exception as e:
            raise ConfigurationError("encryption_key", f"Failed to initialize encryption: {e}")
    
    def _load_credentials(self):
        """Load and decrypt stored credentials."""
        if not self.credentials_file.exists():
            self._credentials = {}
            return
        
        try:
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                self._credentials = {}
                return
            
            decrypted_data = self._fernet.decrypt(encrypted_data)
            self._credentials = json.loads(decrypted_data.decode('utf-8'))
            logger.debug(f"Loaded credentials for {len(self._credentials)} providers")
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            self._credentials = {}
    
    def _save_credentials(self):
        """Encrypt and save credentials to disk."""
        try:
            credentials_json = json.dumps(self._credentials, indent=2)
            encrypted_data = self._fernet.encrypt(credentials_json.encode('utf-8'))
            
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.credentials_file, 0o600)
            logger.debug("Saved encrypted credentials")
            
        except Exception as e:
            raise ConfigurationError("credentials_save", f"Failed to save credentials: {e}")
    
    def set_api_key(self, provider: str, api_key: str, **kwargs):
        """
        Store an API key for a provider.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            api_key: The API key to store
            **kwargs: Additional provider-specific configuration
        """
        if not provider:
            raise ValueError("Provider name cannot be empty")
        
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        # Initialize provider config if it doesn't exist
        if provider not in self._credentials:
            self._credentials[provider] = {}
        
        # Store API key and additional config
        self._credentials[provider]['api_key'] = api_key
        self._credentials[provider].update(kwargs)
        
        # Save to disk
        self._save_credentials()
        logger.info(f"Stored API key for provider: {provider}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Retrieve an API key for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            API key if found, None otherwise
        """
        provider_config = self._credentials.get(provider, {})
        return provider_config.get('api_key')
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get all configuration for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary with provider configuration
        """
        return self._credentials.get(provider, {}).copy()
    
    def remove_provider(self, provider: str) -> bool:
        """
        Remove all credentials for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider was removed, False if not found
        """
        if provider in self._credentials:
            del self._credentials[provider]
            self._save_credentials()
            logger.info(f"Removed credentials for provider: {provider}")
            return True
        return False
    
    def list_providers(self) -> list[str]:
        """
        Get list of providers with stored credentials.
        
        Returns:
            List of provider names
        """
        return list(self._credentials.keys())
    
    def has_credentials(self, provider: str) -> bool:
        """
        Check if credentials exist for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if credentials exist, False otherwise
        """
        return provider in self._credentials and 'api_key' in self._credentials[provider]
    
    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """
        Validate an API key format for a provider.
        
        Args:
            provider: Provider name
            api_key: API key to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not api_key:
            return False
        
        # Provider-specific validation rules
        validation_rules = {
            'openai': lambda key: key.startswith('sk-') and len(key) > 20,
            'anthropic': lambda key: key.startswith('sk-ant-') and len(key) > 20,
            'google': lambda key: len(key) > 20,  # Google API keys vary in format
            'openrouter': lambda key: key.startswith('sk-or-') and len(key) > 20,
            'mistral': lambda key: len(key) > 20,  # Mistral keys vary in format
            'ollama': lambda key: True,  # Ollama might not require API keys for local
        }
        
        validator = validation_rules.get(provider.lower())
        if validator:
            return validator(api_key)
        
        # Default validation - just check it's not empty
        return len(api_key.strip()) > 0
    
    def update_provider_config(self, provider: str, **kwargs):
        """
        Update additional configuration for a provider.
        
        Args:
            provider: Provider name
            **kwargs: Configuration parameters to update
        """
        if provider not in self._credentials:
            self._credentials[provider] = {}
        
        # Update configuration but preserve API key
        self._credentials[provider].update(kwargs)
        self._save_credentials()
        logger.debug(f"Updated configuration for provider: {provider}")
    
    def export_config(self, provider: str, include_api_key: bool = False) -> Dict[str, Any]:
        """
        Export provider configuration.
        
        Args:
            provider: Provider name
            include_api_key: Whether to include the API key in export
            
        Returns:
            Provider configuration dictionary
        """
        config = self.get_provider_config(provider)
        
        if not include_api_key and 'api_key' in config:
            config = config.copy()
            config['api_key'] = '***REDACTED***'
        
        return config
    
    def clear_all_credentials(self):
        """Clear all stored credentials."""
        self._credentials = {}
        if self.credentials_file.exists():
            self.credentials_file.unlink()
        logger.warning("Cleared all stored credentials")
    
    def backup_credentials(self, backup_path: Path, password: Optional[str] = None):
        """
        Create a backup of credentials.
        
        Args:
            backup_path: Path to save backup
            password: Optional password for additional encryption
        """
        try:
            backup_data = {
                'credentials': self._credentials,
                'version': '1.0',
                'created_at': str(Path.ctime(Path.now()))
            }
            
            if password:
                # Additional encryption with user password
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                f = Fernet(key)
                
                data_json = json.dumps(backup_data)
                encrypted_backup = f.encrypt(data_json.encode())
                
                final_backup = {
                    'encrypted': True,
                    'salt': base64.b64encode(salt).decode(),
                    'data': base64.b64encode(encrypted_backup).decode()
                }
            else:
                final_backup = backup_data
            
            with open(backup_path, 'w') as f:
                json.dump(final_backup, f, indent=2)
            
            logger.info(f"Created credentials backup at: {backup_path}")
            
        except Exception as e:
            raise ConfigurationError("backup", f"Failed to create backup: {e}")
    
    def restore_credentials(self, backup_path: Path, password: Optional[str] = None):
        """
        Restore credentials from backup.
        
        Args:
            backup_path: Path to backup file
            password: Password if backup is encrypted
        """
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            if backup_data.get('encrypted'):
                if not password:
                    raise AuthenticationError("backup", "Password required for encrypted backup")
                
                salt = base64.b64decode(backup_data['salt'])
                encrypted_data = base64.b64decode(backup_data['data'])
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                f = Fernet(key)
                
                decrypted_data = f.decrypt(encrypted_data)
                backup_data = json.loads(decrypted_data.decode())
            
            # Restore credentials
            self._credentials = backup_data.get('credentials', {})
            self._save_credentials()
            
            logger.info(f"Restored credentials from backup: {backup_path}")
            
        except Exception as e:
            raise ConfigurationError("restore", f"Failed to restore backup: {e}")