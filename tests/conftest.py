"""
Pytest configuration and fixtures for Nuke AI Panel tests.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

# Test imports
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.auth import AuthManager
from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.core.base_provider import Message, MessageRole, GenerationConfig, GenerationResponse
from nuke_ai_panel.utils.cache import CacheManager
from nuke_ai_panel.utils.rate_limiter import RateLimiter, RateLimit


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config_dict():
    """Test configuration dictionary."""
    return {
        "version": "1.0",
        "providers": {
            "openai": {
                "name": "openai",
                "enabled": True,
                "default_model": "gpt-3.5-turbo",
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
            "ollama": {
                "name": "ollama",
                "enabled": False,
                "default_model": "llama2",
                "custom_endpoint": "http://localhost:11434",
                "timeout": 120
            }
        },
        "cache": {
            "enabled": True,
            "max_size": 100,
            "ttl_seconds": 300
        },
        "logging": {
            "level": "DEBUG",
            "file_logging": False,
            "console_logging": True
        },
        "security": {
            "encrypt_cache": True,
            "api_key_rotation_days": 90
        }
    }


@pytest.fixture
def test_config(test_config_dict, temp_dir):
    """Create a test configuration instance."""
    config_path = os.path.join(temp_dir, "test_config.yaml")
    config = Config(config_dict=test_config_dict)
    config.config_path = config_path
    return config


@pytest.fixture
def test_auth_manager(temp_dir):
    """Create a test authentication manager."""
    auth_dir = os.path.join(temp_dir, "auth")
    os.makedirs(auth_dir, exist_ok=True)
    
    with patch.object(AuthManager, '_get_auth_dir', return_value=auth_dir):
        auth_manager = AuthManager()
        # Set test API keys
        auth_manager.set_api_key('openai', 'sk-test-openai-key')
        auth_manager.set_api_key('anthropic', 'sk-ant-test-anthropic-key')
        yield auth_manager


@pytest.fixture
def test_cache_manager():
    """Create a test cache manager."""
    return CacheManager(max_size=50, ttl_seconds=300)


@pytest.fixture
def test_rate_limiter():
    """Create a test rate limiter."""
    rate_limit = RateLimit(requests_per_minute=60)
    return RateLimiter(rate_limit)


@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI provider."""
    provider = Mock()
    provider.name = "openai"
    provider.authenticate = AsyncMock(return_value=True)
    provider.get_models = AsyncMock(return_value=[
        Mock(id="gpt-3.5-turbo", name="GPT-3.5 Turbo"),
        Mock(id="gpt-4", name="GPT-4")
    ])
    provider.generate_text = AsyncMock(return_value=GenerationResponse(
        content="Test response from OpenAI",
        model="gpt-3.5-turbo",
        provider="openai"
    ))
    provider.generate_text_stream = AsyncMock()
    provider.health_check = AsyncMock(return_value=Mock(healthy=True))
    return provider


@pytest.fixture
def mock_anthropic_provider():
    """Mock Anthropic provider."""
    provider = Mock()
    provider.name = "anthropic"
    provider.authenticate = AsyncMock(return_value=True)
    provider.get_models = AsyncMock(return_value=[
        Mock(id="claude-3-sonnet-20240229", name="Claude 3 Sonnet"),
        Mock(id="claude-3-haiku-20240307", name="Claude 3 Haiku")
    ])
    provider.generate_text = AsyncMock(return_value=GenerationResponse(
        content="Test response from Anthropic",
        model="claude-3-sonnet-20240229",
        provider="anthropic"
    ))
    provider.generate_text_stream = AsyncMock()
    provider.health_check = AsyncMock(return_value=Mock(healthy=True))
    return provider


@pytest.fixture
def test_provider_manager(test_config, test_auth_manager, test_cache_manager, test_rate_limiter):
    """Create a test provider manager with mocked providers."""
    provider_manager = ProviderManager(
        config=test_config,
        auth_manager=test_auth_manager,
        cache_manager=test_cache_manager,
        rate_limiter=test_rate_limiter
    )
    return provider_manager


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        Message(role=MessageRole.USER, content="Hello, how are you?"),
        Message(role=MessageRole.ASSISTANT, content="I'm doing well, thank you!"),
        Message(role=MessageRole.USER, content="Can you help me with Nuke?")
    ]


@pytest.fixture
def sample_generation_config():
    """Sample generation configuration."""
    return GenerationConfig(
        temperature=0.7,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stream=False
    )


@pytest.fixture
def mock_nuke():
    """Mock Nuke module for testing Nuke integration."""
    mock_nuke = Mock()
    mock_nuke.NUKE_VERSION_STRING = "14.0v5"
    mock_nuke.selectedNodes = Mock(return_value=[])
    mock_nuke.allNodes = Mock(return_value=[])
    mock_nuke.root = Mock()
    mock_nuke.createNode = Mock()
    mock_nuke.delete = Mock()
    mock_nuke.connectNodes = Mock()
    
    # Mock node
    mock_node = Mock()
    mock_node.name = Mock(return_value="TestNode")
    mock_node.Class = Mock(return_value="Blur")
    mock_node.knobs = Mock(return_value={})
    mock_node.input = Mock(return_value=None)
    mock_node.output = Mock(return_value=None)
    
    mock_nuke.selectedNodes.return_value = [mock_node]
    mock_nuke.createNode.return_value = mock_node
    
    return mock_nuke


@pytest.fixture
def mock_nuke_context():
    """Mock Nuke context for testing."""
    return {
        "selected_nodes": [
            {
                "name": "Blur1",
                "class": "Blur",
                "properties": {"size": 10.0, "channels": "rgba"}
            }
        ],
        "all_nodes": [
            {
                "name": "Read1",
                "class": "Read",
                "properties": {"file": "/path/to/image.exr"}
            },
            {
                "name": "Blur1", 
                "class": "Blur",
                "properties": {"size": 10.0, "channels": "rgba"}
            }
        ],
        "script_info": {
            "frame_range": [1, 100],
            "format": "HD_1080",
            "fps": 24.0
        }
    }


# Async test helpers
@pytest.fixture
def async_test():
    """Helper for running async tests."""
    def _async_test(coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    return _async_test


# Mock HTTP responses
@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for API calls."""
    responses = {
        "openai_models": {
            "data": [
                {"id": "gpt-3.5-turbo", "object": "model"},
                {"id": "gpt-4", "object": "model"}
            ]
        },
        "openai_chat": {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        },
        "anthropic_message": {
            "content": [
                {
                    "type": "text",
                    "text": "Test response from Claude"
                }
            ],
            "model": "claude-3-sonnet-20240229",
            "role": "assistant",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }
    }
    return responses


# Test data generators
@pytest.fixture
def generate_test_messages():
    """Generate test messages for various scenarios."""
    def _generate(count: int = 5, include_system: bool = True) -> List[Message]:
        messages = []
        
        if include_system:
            messages.append(Message(
                role=MessageRole.SYSTEM,
                content="You are a helpful VFX assistant."
            ))
        
        for i in range(count):
            if i % 2 == 0:
                messages.append(Message(
                    role=MessageRole.USER,
                    content=f"User message {i + 1}"
                ))
            else:
                messages.append(Message(
                    role=MessageRole.ASSISTANT,
                    content=f"Assistant response {i + 1}"
                ))
        
        return messages
    
    return _generate


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_dir):
    """Set up test environment variables."""
    # Set test environment variables
    monkeypatch.setenv("NUKE_AI_PANEL_CONFIG_DIR", temp_dir)
    monkeypatch.setenv("NUKE_AI_PANEL_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("NUKE_AI_PANEL_TESTING", "true")
    
    # Mock API keys for testing
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Clear any global state
    # Reset singletons if any
    # Clear caches
    pass


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Parametrized test data
@pytest.fixture(params=[
    ("openai", "gpt-3.5-turbo"),
    ("openai", "gpt-4"),
    ("anthropic", "claude-3-sonnet-20240229"),
    ("anthropic", "claude-3-haiku-20240307")
])
def provider_model_combinations(request):
    """Parametrized provider and model combinations."""
    return request.param


# Error simulation fixtures
@pytest.fixture
def simulate_network_error():
    """Simulate network errors for testing."""
    def _simulate(error_type="timeout"):
        if error_type == "timeout":
            return asyncio.TimeoutError("Request timed out")
        elif error_type == "connection":
            return ConnectionError("Connection failed")
        elif error_type == "http":
            return Exception("HTTP 500 Internal Server Error")
        else:
            return Exception("Unknown error")
    
    return _simulate


# Database/Storage mocks
@pytest.fixture
def mock_storage():
    """Mock storage for testing persistence."""
    storage = {}
    
    class MockStorage:
        def save(self, key: str, data: Any):
            storage[key] = data
        
        def load(self, key: str) -> Any:
            return storage.get(key)
        
        def delete(self, key: str) -> bool:
            if key in storage:
                del storage[key]
                return True
            return False
        
        def list_keys(self) -> List[str]:
            return list(storage.keys())
        
        def clear(self):
            storage.clear()
    
    return MockStorage()


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "nuke: marks tests that require Nuke"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )


# Skip conditions
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on conditions."""
    # Skip Nuke tests if Nuke is not available
    try:
        import nuke
        nuke_available = True
    except ImportError:
        nuke_available = False
    
    if not nuke_available:
        skip_nuke = pytest.mark.skip(reason="Nuke not available")
        for item in items:
            if "nuke" in item.keywords:
                item.add_marker(skip_nuke)
    
    # Skip network tests if requested
    if config.getoption("--no-network", default=False):
        skip_network = pytest.mark.skip(reason="Network tests disabled")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--no-network",
        action="store_true",
        default=False,
        help="Skip tests that require network access"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )