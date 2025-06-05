# API Reference

Complete API documentation for the Nuke AI Panel system.

## Table of Contents

- [Core Classes](#core-classes)
- [Provider System](#provider-system)
- [Configuration Management](#configuration-management)
- [Authentication](#authentication)
- [Utilities](#utilities)
- [Nuke Integration](#nuke-integration)
- [UI Components](#ui-components)
- [Data Models](#data-models)
- [Exceptions](#exceptions)

## Core Classes

### ProviderManager

Main interface for managing AI providers and generating responses.

```python
from nuke_ai_panel.core.provider_manager import ProviderManager
```

#### Constructor

```python
ProviderManager(
    config: Config = None,
    auth_manager: AuthManager = None,
    cache_manager: CacheManager = None,
    rate_limiter: RateLimiter = None
)
```

**Parameters:**
- `config` (Config, optional): Configuration instance
- `auth_manager` (AuthManager, optional): Authentication manager
- `cache_manager` (CacheManager, optional): Cache manager
- `rate_limiter` (RateLimiter, optional): Rate limiter

#### Methods

##### `authenticate_all_providers()`

Authenticate all enabled providers.

```python
async def authenticate_all_providers() -> Dict[str, bool]
```

**Returns:** Dictionary mapping provider names to authentication status.

**Example:**
```python
auth_results = await provider_manager.authenticate_all_providers()
print(auth_results)  # {'openai': True, 'anthropic': True, ...}
```

##### `generate_text()`

Generate text using the specified model and provider.

```python
async def generate_text(
    messages: List[Message],
    model: str = None,
    provider: str = None,
    config: GenerationConfig = None,
    **kwargs
) -> GenerationResponse
```

**Parameters:**
- `messages` (List[Message]): Conversation messages
- `model` (str, optional): Model name to use
- `provider` (str, optional): Provider name to use
- `config` (GenerationConfig, optional): Generation configuration
- `**kwargs`: Additional provider-specific parameters

**Returns:** GenerationResponse object with the generated text.

**Example:**
```python
messages = [Message(role=MessageRole.USER, content="Hello!")]
response = await provider_manager.generate_text(
    messages=messages,
    model="gpt-4",
    config=GenerationConfig(temperature=0.7, max_tokens=100)
)
print(response.content)
```

##### `generate_text_stream()`

Generate text with streaming response.

```python
async def generate_text_stream(
    messages: List[Message],
    model: str = None,
    provider: str = None,
    config: GenerationConfig = None,
    **kwargs
) -> AsyncIterator[str]
```

**Parameters:** Same as `generate_text()`

**Returns:** Async iterator yielding text chunks.

**Example:**
```python
messages = [Message(role=MessageRole.USER, content="Write a story")]
async for chunk in provider_manager.generate_text_stream(messages=messages):
    print(chunk, end='', flush=True)
```

##### `get_available_models()`

Get list of available models from all providers.

```python
async def get_available_models(provider: str = None) -> Dict[str, List[ModelInfo]]
```

**Parameters:**
- `provider` (str, optional): Specific provider name

**Returns:** Dictionary mapping provider names to model lists.

##### `health_check()`

Check health status of all providers.

```python
async def health_check() -> Dict[str, HealthStatus]
```

**Returns:** Dictionary mapping provider names to health status.

### Config

Configuration management system.

```python
from nuke_ai_panel.core.config import Config
```

#### Constructor

```python
Config(config_path: str = None, config_dict: dict = None)
```

**Parameters:**
- `config_path` (str, optional): Path to configuration file
- `config_dict` (dict, optional): Configuration dictionary

#### Methods

##### `get()`

Get configuration value using dot notation.

```python
def get(self, key: str, default=None) -> Any
```

**Parameters:**
- `key` (str): Configuration key (e.g., "providers.openai.enabled")
- `default`: Default value if key not found

**Example:**
```python
config = Config()
enabled = config.get('providers.openai.enabled', False)
model = config.get('providers.openai.default_model', 'gpt-3.5-turbo')
```

##### `set()`

Set configuration value using dot notation.

```python
def set(self, key: str, value: Any) -> None
```

**Parameters:**
- `key` (str): Configuration key
- `value` (Any): Value to set

**Example:**
```python
config.set('providers.openai.rate_limit', 100)
config.set('cache.enabled', True)
```

##### `save()`

Save configuration to file.

```python
def save(self, path: str = None) -> None
```

**Parameters:**
- `path` (str, optional): File path to save to

##### `load()`

Load configuration from file.

```python
def load(self, path: str) -> None
```

**Parameters:**
- `path` (str): File path to load from

### AuthManager

Secure API key management.

```python
from nuke_ai_panel.core.auth import AuthManager
```

#### Constructor

```python
AuthManager(encryption_key: bytes = None)
```

**Parameters:**
- `encryption_key` (bytes, optional): Custom encryption key

#### Methods

##### `set_api_key()`

Store encrypted API key for a provider.

```python
def set_api_key(self, provider: str, api_key: str) -> None
```

**Parameters:**
- `provider` (str): Provider name
- `api_key` (str): API key to store

**Example:**
```python
auth_manager = AuthManager()
auth_manager.set_api_key('openai', 'sk-your-key-here')
auth_manager.set_api_key('anthropic', 'sk-ant-your-key-here')
```

##### `get_api_key()`

Retrieve decrypted API key for a provider.

```python
def get_api_key(self, provider: str) -> str
```

**Parameters:**
- `provider` (str): Provider name

**Returns:** Decrypted API key or None if not found.

##### `list_providers()`

List all providers with stored credentials.

```python
def list_providers(self) -> List[str]
```

**Returns:** List of provider names with stored API keys.

##### `remove_api_key()`

Remove stored API key for a provider.

```python
def remove_api_key(self, provider: str) -> bool
```

**Parameters:**
- `provider` (str): Provider name

**Returns:** True if key was removed, False if not found.

## Provider System

### BaseProvider

Abstract base class for all AI providers.

```python
from nuke_ai_panel.core.base_provider import BaseProvider
```

#### Abstract Methods

```python
async def authenticate(self) -> bool
async def get_models(self) -> List[ModelInfo]
async def generate_text(
    self,
    messages: List[Message],
    model: str,
    config: GenerationConfig
) -> GenerationResponse
async def generate_text_stream(
    self,
    messages: List[Message],
    model: str,
    config: GenerationConfig
) -> AsyncIterator[str]
```

### Individual Providers

#### OpenAIProvider

```python
from nuke_ai_panel.providers.openai_provider import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-your-key",
    config=config
)
```

#### AnthropicProvider

```python
from nuke_ai_panel.providers.anthropic_provider import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-your-key",
    config=config
)
```

#### GoogleProvider

```python
from nuke_ai_panel.providers.google_provider import GoogleProvider

provider = GoogleProvider(
    api_key="your-google-key",
    config=config
)
```

#### OpenRouterProvider

```python
from nuke_ai_panel.providers.openrouter_provider import OpenRouterProvider

provider = OpenRouterProvider(
    api_key="sk-or-your-key",
    config=config
)
```

#### OllamaProvider

```python
from nuke_ai_panel.providers.ollama_provider import OllamaProvider

provider = OllamaProvider(
    base_url="http://localhost:11434",
    config=config
)
```

#### MistralProvider

```python
from nuke_ai_panel.providers.mistral_provider import MistralProvider

provider = MistralProvider(
    api_key="your-mistral-key",
    config=config
)
```

## Data Models

### Message

Represents a conversation message.

```python
from nuke_ai_panel.core.base_provider import Message, MessageRole

message = Message(
    role=MessageRole.USER,  # USER, ASSISTANT, SYSTEM
    content="Your message content",
    metadata={"timestamp": "2024-01-01T00:00:00Z"}  # Optional
)
```

**Attributes:**
- `role` (MessageRole): Message role (USER, ASSISTANT, SYSTEM)
- `content` (str): Message content
- `metadata` (dict, optional): Additional metadata

### GenerationConfig

Configuration for text generation.

```python
from nuke_ai_panel.core.base_provider import GenerationConfig

config = GenerationConfig(
    temperature=0.7,
    max_tokens=1000,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop_sequences=["END"],
    stream=False
)
```

**Attributes:**
- `temperature` (float): Randomness (0.0-2.0)
- `max_tokens` (int): Maximum tokens to generate
- `top_p` (float): Nucleus sampling parameter
- `frequency_penalty` (float): Frequency penalty (-2.0 to 2.0)
- `presence_penalty` (float): Presence penalty (-2.0 to 2.0)
- `stop_sequences` (List[str]): Stop sequences
- `stream` (bool): Enable streaming

### GenerationResponse

Response from text generation.

```python
response = GenerationResponse(
    content="Generated text",
    model="gpt-4",
    provider="openai",
    usage=TokenUsage(prompt_tokens=10, completion_tokens=20),
    metadata={"finish_reason": "stop"}
)
```

**Attributes:**
- `content` (str): Generated text
- `model` (str): Model used
- `provider` (str): Provider used
- `usage` (TokenUsage): Token usage information
- `metadata` (dict): Additional response metadata

### ModelInfo

Information about an AI model.

```python
model_info = ModelInfo(
    id="gpt-4",
    name="GPT-4",
    provider="openai",
    context_length=8192,
    supports_streaming=True,
    supports_functions=True,
    cost_per_token=0.00003
)
```

**Attributes:**
- `id` (str): Model identifier
- `name` (str): Human-readable name
- `provider` (str): Provider name
- `context_length` (int): Maximum context length
- `supports_streaming` (bool): Streaming support
- `supports_functions` (bool): Function calling support
- `cost_per_token` (float): Cost per token

## Utilities

### CacheManager

Caching system for API responses.

```python
from nuke_ai_panel.utils.cache import CacheManager

cache = CacheManager(
    max_size=1000,
    ttl_seconds=3600
)

# Store value
cache.set("key", "value", ttl=1800)

# Retrieve value
value = cache.get("key")

# Check if key exists
exists = cache.has("key")

# Clear cache
cache.clear()
```

### RateLimiter

Rate limiting for API requests.

```python
from nuke_ai_panel.utils.rate_limiter import RateLimiter, RateLimit

rate_limit = RateLimit(requests_per_minute=60)
limiter = RateLimiter(rate_limit)

# Check if request can proceed
if limiter.can_proceed():
    # Make API request
    pass
else:
    # Wait or handle rate limit
    wait_time = limiter.time_until_reset()
    await asyncio.sleep(wait_time)
```

### Logger

Logging system with rotation and formatting.

```python
from nuke_ai_panel.utils.logger import get_logger

logger = get_logger("my_module")

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

## Nuke Integration

### PanelManager

Manages the main AI panel in Nuke.

```python
from src.core.panel_manager import PanelManager

panel_manager = PanelManager()
panel = panel_manager.create_panel()
panel_manager.show_panel()
```

### ActionEngine

Processes AI responses and converts them to Nuke actions.

```python
from src.core.action_engine import ActionEngine

engine = ActionEngine()
actions = await engine.process_response(ai_response, context)
results = await engine.execute_actions(actions)
```

### ContextAnalyzer

Analyzes current Nuke script context.

```python
from src.nuke_integration.context_analyzer import ContextAnalyzer

analyzer = ContextAnalyzer()
context = analyzer.analyze_current_script()
selected_nodes = analyzer.get_selected_nodes()
```

### NodeInspector

Inspects Nuke nodes and their properties.

```python
from src.nuke_integration.node_inspector import NodeInspector

inspector = NodeInspector()
node_info = inspector.inspect_node(node)
properties = inspector.get_node_properties(node)
```

### ScriptGenerator

Generates Nuke scripts from AI responses.

```python
from src.nuke_integration.script_generator import ScriptGenerator

generator = ScriptGenerator()
script = generator.generate_from_description("Create a glow effect")
nodes = generator.create_node_network(script)
```

## UI Components

### MainPanel

Main AI panel interface.

```python
from src.ui.main_panel import NukeAIPanel

panel = NukeAIPanel()
panel.show()
```

### ChatInterface

Chat interface component.

```python
from src.ui.chat_interface import ChatInterface

chat = ChatInterface(parent=panel)
chat.add_message("Hello!", is_user=True)
chat.add_message("Hi there!", is_user=False)
```

### SettingsDialog

Settings configuration dialog.

```python
from src.ui.settings_dialog import SettingsDialog

dialog = SettingsDialog(parent=panel)
dialog.show()
```

## Exceptions

### Core Exceptions

```python
from nuke_ai_panel.core.exceptions import (
    NukeAIPanelError,
    AuthenticationError,
    ProviderError,
    ConfigurationError,
    RateLimitError
)

try:
    response = await provider.generate_text(messages)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except ProviderError as e:
    print(f"Provider error: {e}")
```

### Exception Hierarchy

```
NukeAIPanelError (base)
├── AuthenticationError
├── ProviderError
│   ├── OpenAIError
│   ├── AnthropicError
│   └── GoogleError
├── ConfigurationError
├── RateLimitError
├── CacheError
└── ValidationError
```

## Usage Examples

### Basic Text Generation

```python
import asyncio
from nuke_ai_panel import Config, AuthManager, ProviderManager
from nuke_ai_panel.core.base_provider import Message, MessageRole

async def main():
    # Setup
    config = Config()
    auth_manager = AuthManager()
    auth_manager.set_api_key('openai', 'your-key')
    
    provider_manager = ProviderManager(
        config=config,
        auth_manager=auth_manager
    )
    
    # Authenticate
    await provider_manager.authenticate_all_providers()
    
    # Generate text
    messages = [
        Message(role=MessageRole.USER, content="Explain Nuke's merge nodes")
    ]
    
    response = await provider_manager.generate_text(
        messages=messages,
        model="gpt-4"
    )
    
    print(response.content)

asyncio.run(main())
```

### Streaming Generation

```python
async def streaming_example():
    messages = [
        Message(role=MessageRole.USER, content="Write a Python script for Nuke")
    ]
    
    print("AI Response:")
    async for chunk in provider_manager.generate_text_stream(
        messages=messages,
        model="gpt-4"
    ):
        print(chunk, end='', flush=True)
    print()  # New line at end

asyncio.run(streaming_example())
```

### Custom Provider

```python
from nuke_ai_panel.core.base_provider import BaseProvider

class CustomProvider(BaseProvider):
    def __init__(self, api_key: str, config: Config):
        super().__init__(config)
        self.api_key = api_key
    
    async def authenticate(self) -> bool:
        # Implement authentication
        return True
    
    async def get_models(self) -> List[ModelInfo]:
        # Return available models
        return [ModelInfo(id="custom-model", name="Custom Model")]
    
    async def generate_text(self, messages, model, config):
        # Implement text generation
        return GenerationResponse(
            content="Custom response",
            model=model,
            provider="custom"
        )
```

---

For more examples and advanced usage, see the [examples/](examples/) directory.