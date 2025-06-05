"""
Unit tests for AI provider implementations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
from typing import List, Dict, Any

from nuke_ai_panel.core.base_provider import (
    BaseProvider, Message, MessageRole, GenerationConfig, 
    GenerationResponse, ModelInfo, HealthStatus
)
from nuke_ai_panel.providers.openai_provider import OpenAIProvider
from nuke_ai_panel.providers.anthropic_provider import AnthropicProvider
from nuke_ai_panel.providers.google_provider import GoogleProvider
from nuke_ai_panel.providers.openrouter_provider import OpenRouterProvider
from nuke_ai_panel.providers.ollama_provider import OllamaProvider
from nuke_ai_panel.providers.mistral_provider import MistralProvider
from nuke_ai_panel.core.exceptions import (
    AuthenticationError, ProviderError, RateLimitError
)


class TestBaseProvider:
    """Test the base provider abstract class."""
    
    def test_base_provider_is_abstract(self):
        """Test that BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider()
    
    def test_message_creation(self):
        """Test Message creation and validation."""
        message = Message(
            role=MessageRole.USER,
            content="Test message",
            metadata={"timestamp": "2024-01-01"}
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Test message"
        assert message.metadata["timestamp"] == "2024-01-01"
    
    def test_generation_config_defaults(self):
        """Test GenerationConfig default values."""
        config = GenerationConfig()
        
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stream is False
    
    def test_generation_response_creation(self):
        """Test GenerationResponse creation."""
        response = GenerationResponse(
            content="Generated text",
            model="test-model",
            provider="test-provider"
        )
        
        assert response.content == "Generated text"
        assert response.model == "test-model"
        assert response.provider == "test-provider"


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def openai_provider(self, test_config):
        """Create OpenAI provider for testing."""
        return OpenAIProvider(
            api_key="sk-test-key",
            config=test_config
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, openai_provider, mock_http_responses):
        """Test successful authentication."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_http_responses["openai_models"])
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await openai_provider.authenticate()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, openai_provider):
        """Test authentication failure."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(AuthenticationError):
                await openai_provider.authenticate()
    
    @pytest.mark.asyncio
    async def test_get_models(self, openai_provider, mock_http_responses):
        """Test getting available models."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_http_responses["openai_models"])
            mock_get.return_value.__aenter__.return_value = mock_response
            
            models = await openai_provider.get_models()
            assert len(models) == 2
            assert models[0].id == "gpt-3.5-turbo"
            assert models[1].id == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_generate_text(self, openai_provider, sample_messages, mock_http_responses):
        """Test text generation."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_http_responses["openai_chat"])
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = GenerationConfig(temperature=0.7, max_tokens=100)
            response = await openai_provider.generate_text(
                messages=sample_messages,
                model="gpt-3.5-turbo",
                config=config
            )
            
            assert response.content == "Test response"
            assert response.model == "gpt-3.5-turbo"
            assert response.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_generate_text_stream(self, openai_provider, sample_messages):
        """Test streaming text generation."""
        mock_chunks = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
            b'data: [DONE]\n\n'
        ]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content.iter_chunked = AsyncMock(return_value=iter(mock_chunks))
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = GenerationConfig(stream=True)
            chunks = []
            async for chunk in openai_provider.generate_text_stream(
                messages=sample_messages,
                model="gpt-3.5-turbo",
                config=config
            ):
                chunks.append(chunk)
            
            assert "Hello" in chunks
            assert " world" in chunks
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, openai_provider, sample_messages):
        """Test rate limit error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.json = AsyncMock(return_value={
                "error": {"message": "Rate limit exceeded"}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(RateLimitError):
                await openai_provider.generate_text(
                    messages=sample_messages,
                    model="gpt-3.5-turbo",
                    config=GenerationConfig()
                )
    
    @pytest.mark.asyncio
    async def test_health_check(self, openai_provider):
        """Test provider health check."""
        with patch.object(openai_provider, 'authenticate', return_value=True):
            health = await openai_provider.health_check()
            assert health.healthy is True
            assert health.provider == "openai"


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""
    
    @pytest.fixture
    def anthropic_provider(self, test_config):
        """Create Anthropic provider for testing."""
        return AnthropicProvider(
            api_key="sk-ant-test-key",
            config=test_config
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, anthropic_provider):
        """Test successful authentication."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "content": [{"type": "text", "text": "Hello"}],
                "model": "claude-3-sonnet-20240229"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await anthropic_provider.authenticate()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_text(self, anthropic_provider, sample_messages, mock_http_responses):
        """Test text generation with Anthropic."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_http_responses["anthropic_message"])
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = GenerationConfig(temperature=0.7, max_tokens=100)
            response = await anthropic_provider.generate_text(
                messages=sample_messages,
                model="claude-3-sonnet-20240229",
                config=config
            )
            
            assert response.content == "Test response from Claude"
            assert response.model == "claude-3-sonnet-20240229"
            assert response.provider == "anthropic"
    
    @pytest.mark.asyncio
    async def test_message_conversion(self, anthropic_provider):
        """Test conversion of messages to Anthropic format."""
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful"),
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there"),
            Message(role=MessageRole.USER, content="How are you?")
        ]
        
        converted = anthropic_provider._convert_messages(messages)
        
        # System message should be extracted
        assert "system" in converted
        assert converted["system"] == "You are helpful"
        
        # Other messages should be in messages array
        assert len(converted["messages"]) == 3
        assert converted["messages"][0]["role"] == "user"
        assert converted["messages"][1]["role"] == "assistant"
        assert converted["messages"][2]["role"] == "user"


class TestGoogleProvider:
    """Test Google provider implementation."""
    
    @pytest.fixture
    def google_provider(self, test_config):
        """Create Google provider for testing."""
        return GoogleProvider(
            api_key="test-google-key",
            config=test_config
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, google_provider):
        """Test successful authentication."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "models": [{"name": "models/gemini-pro"}]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await google_provider.authenticate()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_text(self, google_provider, sample_messages):
        """Test text generation with Google."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "candidates": [{
                    "content": {
                        "parts": [{"text": "Test response from Gemini"}]
                    }
                }]
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = GenerationConfig(temperature=0.7, max_tokens=100)
            response = await google_provider.generate_text(
                messages=sample_messages,
                model="gemini-pro",
                config=config
            )
            
            assert response.content == "Test response from Gemini"
            assert response.provider == "google"


class TestOllamaProvider:
    """Test Ollama provider implementation."""
    
    @pytest.fixture
    def ollama_provider(self, test_config):
        """Create Ollama provider for testing."""
        return OllamaProvider(
            base_url="http://localhost:11434",
            config=test_config
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, ollama_provider):
        """Test successful authentication (Ollama doesn't require auth)."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"version": "0.1.0"})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await ollama_provider.authenticate()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_models(self, ollama_provider):
        """Test getting available models from Ollama."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "models": [
                    {"name": "llama2:latest", "size": 3800000000},
                    {"name": "mistral:latest", "size": 4100000000}
                ]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            models = await ollama_provider.get_models()
            assert len(models) == 2
            assert models[0].id == "llama2:latest"
            assert models[1].id == "mistral:latest"
    
    @pytest.mark.asyncio
    async def test_generate_text(self, ollama_provider, sample_messages):
        """Test text generation with Ollama."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "response": "Test response from Ollama",
                "model": "llama2",
                "done": True
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = GenerationConfig(temperature=0.7, max_tokens=100)
            response = await ollama_provider.generate_text(
                messages=sample_messages,
                model="llama2",
                config=config
            )
            
            assert response.content == "Test response from Ollama"
            assert response.model == "llama2"
            assert response.provider == "ollama"


class TestOpenRouterProvider:
    """Test OpenRouter provider implementation."""
    
    @pytest.fixture
    def openrouter_provider(self, test_config):
        """Create OpenRouter provider for testing."""
        return OpenRouterProvider(
            api_key="sk-or-test-key",
            config=test_config
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, openrouter_provider):
        """Test successful authentication."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "data": [{"id": "openai/gpt-3.5-turbo"}]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await openrouter_provider.authenticate()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_custom_headers(self, openrouter_provider):
        """Test that custom headers are included in requests."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Test"}}]
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await openrouter_provider.generate_text(
                messages=[Message(role=MessageRole.USER, content="Test")],
                model="openai/gpt-3.5-turbo",
                config=GenerationConfig()
            )
            
            # Check that custom headers were included
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "HTTP-Referer" in headers
            assert "X-Title" in headers


class TestMistralProvider:
    """Test Mistral provider implementation."""
    
    @pytest.fixture
    def mistral_provider(self, test_config):
        """Create Mistral provider for testing."""
        return MistralProvider(
            api_key="test-mistral-key",
            config=test_config
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, mistral_provider):
        """Test successful authentication."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "data": [{"id": "mistral-medium"}]
            })
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await mistral_provider.authenticate()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_text(self, mistral_provider, sample_messages):
        """Test text generation with Mistral."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Test response from Mistral"
                    }
                }],
                "model": "mistral-medium"
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            config = GenerationConfig(temperature=0.7, max_tokens=100)
            response = await mistral_provider.generate_text(
                messages=sample_messages,
                model="mistral-medium",
                config=config
            )
            
            assert response.content == "Test response from Mistral"
            assert response.model == "mistral-medium"
            assert response.provider == "mistral"


class TestProviderErrorHandling:
    """Test error handling across all providers."""
    
    @pytest.mark.parametrize("provider_class,api_key", [
        (OpenAIProvider, "sk-test"),
        (AnthropicProvider, "sk-ant-test"),
        (GoogleProvider, "test-key"),
        (MistralProvider, "test-key")
    ])
    @pytest.mark.asyncio
    async def test_network_timeout(self, provider_class, api_key, test_config):
        """Test network timeout handling."""
        provider = provider_class(api_key=api_key, config=test_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timed out")
            
            with pytest.raises(ProviderError):
                await provider.generate_text(
                    messages=[Message(role=MessageRole.USER, content="Test")],
                    model="test-model",
                    config=GenerationConfig()
                )
    
    @pytest.mark.parametrize("provider_class,api_key", [
        (OpenAIProvider, "sk-test"),
        (AnthropicProvider, "sk-ant-test"),
        (GoogleProvider, "test-key"),
        (MistralProvider, "test-key")
    ])
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, provider_class, api_key, test_config):
        """Test invalid API key handling."""
        provider = provider_class(api_key="invalid-key", config=test_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.json = AsyncMock(return_value={
                "error": {"message": "Invalid API key"}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(AuthenticationError):
                await provider.authenticate()
    
    @pytest.mark.asyncio
    async def test_server_error_handling(self, test_config):
        """Test server error handling."""
        provider = OpenAIProvider(api_key="sk-test", config=test_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.json = AsyncMock(return_value={
                "error": {"message": "Internal server error"}
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(ProviderError):
                await provider.generate_text(
                    messages=[Message(role=MessageRole.USER, content="Test")],
                    model="gpt-3.5-turbo",
                    config=GenerationConfig()
                )


class TestProviderPerformance:
    """Test provider performance characteristics."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_config, performance_timer):
        """Test handling of concurrent requests."""
        provider = OpenAIProvider(api_key="sk-test", config=test_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "choices": [{"message": {"content": "Test"}}]
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = provider.generate_text(
                    messages=[Message(role=MessageRole.USER, content=f"Test {i}")],
                    model="gpt-3.5-turbo",
                    config=GenerationConfig()
                )
                tasks.append(task)
            
            performance_timer.start()
            results = await asyncio.gather(*tasks)
            performance_timer.stop()
            
            assert len(results) == 10
            assert all(r.content == "Test" for r in results)
            assert performance_timer.elapsed < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self, test_config):
        """Test streaming response performance."""
        provider = OpenAIProvider(api_key="sk-test", config=test_config)
        
        # Mock streaming response
        mock_chunks = [
            b'data: {"choices":[{"delta":{"content":"chunk1"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"chunk2"}}]}\n\n',
            b'data: [DONE]\n\n'
        ]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content.iter_chunked = AsyncMock(return_value=iter(mock_chunks))
            mock_post.return_value.__aenter__.return_value = mock_response
            
            chunks = []
            async for chunk in provider.generate_text_stream(
                messages=[Message(role=MessageRole.USER, content="Test")],
                model="gpt-3.5-turbo",
                config=GenerationConfig(stream=True)
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 2
            assert "chunk1" in chunks
            assert "chunk2" in chunks


if __name__ == "__main__":
    pytest.main([__file__])