"""
Basic usage example for Nuke AI Panel.

This example demonstrates how to set up and use the AI provider system
with multiple providers and basic text generation.
"""

import asyncio
import os
from pathlib import Path

# Add the parent directory to the path so we can import nuke_ai_panel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nuke_ai_panel import Config, AuthManager, ProviderManager
from nuke_ai_panel.core.base_provider import Message, MessageRole, GenerationConfig
from nuke_ai_panel.utils.logger import setup_logging


async def main():
    """Main example function."""
    
    # Set up logging
    setup_logging(level="INFO", console_logging=True, file_logging=False)
    
    print("🚀 Nuke AI Panel - Basic Usage Example")
    print("=" * 50)
    
    # Initialize configuration
    config = Config()
    
    # Initialize authentication manager
    auth_manager = AuthManager()
    
    # Set up API keys from environment variables or prompt user
    setup_api_keys(auth_manager)
    
    # Initialize provider manager
    provider_manager = ProviderManager(
        config=config,
        auth_manager=auth_manager
    )
    
    print("\n📡 Authenticating providers...")
    
    # Authenticate all providers
    auth_results = await provider_manager.authenticate_all_providers()
    
    # Display authentication results
    for provider, success in auth_results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {provider}: {status}")
    
    # Get available providers
    available_providers = provider_manager.get_available_providers()
    
    if not available_providers:
        print("\n❌ No providers are available. Please check your API keys and try again.")
        return
    
    print(f"\n🎯 Available providers: {', '.join(available_providers)}")
    
    # Get available models
    print("\n📋 Fetching available models...")
    models_by_provider = await provider_manager.get_available_models()
    
    for provider, models in models_by_provider.items():
        if models:
            print(f"  {provider}: {len(models)} models")
            for model in models[:3]:  # Show first 3 models
                print(f"    - {model.name}: {model.description}")
            if len(models) > 3:
                print(f"    ... and {len(models) - 3} more")
    
    # Example 1: Basic text generation
    print("\n💬 Example 1: Basic Text Generation")
    print("-" * 40)
    
    messages = [
        Message(role=MessageRole.USER, content="Hello! Can you tell me a fun fact about AI?")
    ]
    
    try:
        response = await provider_manager.generate_text(
            messages=messages,
            # Let the system choose the best available provider and model
        )
        
        print(f"🤖 Response: {response.content}")
        print(f"📊 Model: {response.model}")
        print(f"📈 Usage: {response.usage}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Streaming text generation
    print("\n🌊 Example 2: Streaming Text Generation")
    print("-" * 40)
    
    messages = [
        Message(role=MessageRole.USER, content="Write a short poem about technology.")
    ]
    
    try:
        print("🤖 Streaming response: ", end="", flush=True)
        
        async for chunk in provider_manager.generate_text_stream(
            messages=messages,
        ):
            print(chunk, end="", flush=True)
        
        print("\n")  # New line after streaming
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")
    
    # Example 3: Conversation with context
    print("\n💭 Example 3: Multi-turn Conversation")
    print("-" * 40)
    
    conversation = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant that gives concise answers."),
        Message(role=MessageRole.USER, content="What is machine learning?"),
    ]
    
    try:
        # First response
        response1 = await provider_manager.generate_text(
            messages=conversation,
            config=GenerationConfig(temperature=0.7, max_tokens=100)
        )
        
        print(f"🤖 Assistant: {response1.content}")
        
        # Add assistant response to conversation
        conversation.append(
            Message(role=MessageRole.ASSISTANT, content=response1.content)
        )
        
        # Follow-up question
        conversation.append(
            Message(role=MessageRole.USER, content="Can you give me a simple example?")
        )
        
        response2 = await provider_manager.generate_text(
            messages=conversation,
            config=GenerationConfig(temperature=0.7, max_tokens=150)
        )
        
        print(f"🤖 Assistant: {response2.content}")
        
    except Exception as e:
        print(f"❌ Conversation error: {e}")
    
    # Example 4: Provider health check
    print("\n🏥 Example 4: Provider Health Check")
    print("-" * 40)
    
    health_results = await provider_manager.health_check()
    
    for provider, health in health_results.items():
        status = health.get('status', 'unknown')
        if status == 'healthy':
            print(f"  {provider}: ✅ Healthy")
            if 'models_available' in health:
                print(f"    Models: {health['models_available']}")
            if 'response_time' in health:
                print(f"    Response time: {health['response_time']:.2f}s")
        else:
            print(f"  {provider}: ❌ Unhealthy - {health.get('error', 'Unknown error')}")
    
    # Example 5: Statistics
    print("\n📊 Example 5: System Statistics")
    print("-" * 40)
    
    stats = provider_manager.get_stats()
    
    print(f"  Total providers: {stats['total_providers']}")
    print(f"  Available providers: {stats['available_providers']}")
    print(f"  Total usage: {stats['total_usage']}")
    print(f"  Total errors: {stats['total_errors']}")
    print(f"  Error rate: {stats['error_rate']:.2%}")
    
    if stats['provider_usage']:
        print("  Provider usage:")
        for provider, count in stats['provider_usage'].items():
            print(f"    {provider}: {count} requests")
    
    # Cleanup
    await provider_manager.shutdown()
    
    print("\n✨ Example completed successfully!")


def setup_api_keys(auth_manager: AuthManager):
    """Set up API keys from environment variables or user input."""
    
    # API key environment variable mapping
    api_key_env_vars = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY',
        'mistral': 'MISTRAL_API_KEY',
    }
    
    print("\n🔑 Setting up API keys...")
    
    for provider, env_var in api_key_env_vars.items():
        api_key = os.getenv(env_var)
        
        if api_key:
            auth_manager.set_api_key(provider, api_key)
            print(f"  {provider}: ✅ Loaded from {env_var}")
        else:
            print(f"  {provider}: ⚠️  No API key found in {env_var}")
    
    # Special case for Ollama (usually doesn't need API key)
    if not auth_manager.has_credentials('ollama'):
        # Set a dummy API key for Ollama since it typically runs locally
        auth_manager.set_api_key('ollama', 'local')
        print("  ollama: ✅ Set up for local usage")
    
    # Check if we have at least one provider configured
    providers_with_keys = auth_manager.list_providers()
    
    if not providers_with_keys:
        print("\n⚠️  No API keys configured!")
        print("Please set environment variables for at least one provider:")
        for provider, env_var in api_key_env_vars.items():
            print(f"  export {env_var}=your-{provider}-api-key")
        print("\nOr run Ollama locally for free local AI:")
        print("  curl -fsSL https://ollama.ai/install.sh | sh")
        print("  ollama run llama2")


if __name__ == "__main__":
    asyncio.run(main())