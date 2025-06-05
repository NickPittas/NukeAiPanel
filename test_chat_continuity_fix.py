"""
Test script to verify the chat continuity fix.

This script tests multiple chat interactions to ensure that the event loop
is properly managed and not closed between messages, preventing the
"Event loop is closed" errors.
"""

import sys
import os
import time
import asyncio
from typing import List, Dict, Any
import unittest.mock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.base_provider import Message, MessageRole, BaseProvider, GenerationResponse
from nuke_ai_panel.utils.event_loop_manager import get_event_loop_manager, run_coroutine

# Create a mock provider for testing
class MockProvider(BaseProvider):
    """Mock provider for testing chat continuity."""
    
    def __init__(self, name, config):
        super().__init__(name, config)
        self._authenticated = True
    
    async def authenticate(self):
        return True
    
    async def get_models(self):
        return []
    
    async def generate_text(self, messages, model, config=None):
        # Simulate a delay
        await asyncio.sleep(0.1)
        
        # Get the last user message
        last_message = messages[-1].content if messages else "No message"
        
        # Generate a simple response
        response = f"Mock response to: {last_message}"
        
        return GenerationResponse(
            content=response,
            model=model,
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            finish_reason="stop"
        )
    
    async def generate_text_stream(self, messages, model, config=None):
        # Simulate a delay
        await asyncio.sleep(0.1)
        
        # Get the last user message
        last_message = messages[-1].content if messages else "No message"
        
        # Generate a simple response
        response = f"Mock response to: {last_message}"
        
        # Yield the response in chunks
        for chunk in response.split():
            yield chunk + " "
            await asyncio.sleep(0.05)
    
    async def close(self):
        pass

def test_chat_continuity():
    """Test multiple chat interactions to verify continuity."""
    print("\n===== TESTING CHAT CONTINUITY =====")
    
    # Create a provider manager with a mock provider
    config = Config()
    provider_manager = ProviderManager(config)
    
    # Replace the provider_manager._providers with our mock provider
    mock_provider = MockProvider("mock", {})
    provider_manager._providers = {"mock": mock_provider}
    provider_manager._provider_status = {"mock": provider_manager._provider_status.get("mock", {})}
    
    # Set the mock provider as the current provider
    default_provider = "mock"
    default_model = "mock-model"
    
    print(f"✅ Using mock provider for testing")
    
    # Test multiple chat interactions
    messages = []
    
    # First message
    print("\n----- SENDING FIRST MESSAGE -----")
    user_message = "Hello, how are you today?"
    messages.append(Message(role=MessageRole.USER, content=user_message))
    
    try:
        response = run_coroutine(
            mock_provider.generate_text(messages, default_model)
        )
        print(f"✅ First response received: {response.content}")
        
        # Add the response to the conversation
        messages.append(Message(role=MessageRole.ASSISTANT, content=response.content))
    except Exception as e:
        print(f"❌ First message error: {e}")
        return False
    
    # Second message
    print("\n----- SENDING SECOND MESSAGE -----")
    user_message = "What's the weather like today?"
    messages.append(Message(role=MessageRole.USER, content=user_message))
    
    try:
        response = run_coroutine(
            mock_provider.generate_text(messages, default_model)
        )
        print(f"✅ Second response received: {response.content}")
        
        # Add the response to the conversation
        messages.append(Message(role=MessageRole.ASSISTANT, content=response.content))
    except Exception as e:
        print(f"❌ Second message error: {e}")
        return False
    
    # Third message
    print("\n----- SENDING THIRD MESSAGE -----")
    user_message = "Thank you for the information!"
    messages.append(Message(role=MessageRole.USER, content=user_message))
    
    try:
        response = run_coroutine(
            mock_provider.generate_text(messages, default_model)
        )
        print(f"✅ Third response received: {response.content}")
    except Exception as e:
        print(f"❌ Third message error: {e}")
        return False
    
    # Clean up
    try:
        run_coroutine(mock_provider.close())
        print("✅ Mock provider cleanup successful")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
    
    print("\n✅ CHAT CONTINUITY TEST PASSED!")
    return True

def test_event_loop_persistence():
    """Test that the event loop persists across multiple operations."""
    print("\n===== TESTING EVENT LOOP PERSISTENCE =====")
    
    # Get the event loop manager
    event_loop_manager = get_event_loop_manager()
    
    # Get the event loop
    loop1 = event_loop_manager.get_loop()
    print(f"✅ Got event loop: {loop1}")
    
    # Run a simple coroutine
    async def simple_coro():
        await asyncio.sleep(0.1)
        return "Hello from coroutine"
    
    try:
        result = run_coroutine(simple_coro())
        print(f"✅ First coroutine result: {result}")
    except Exception as e:
        print(f"❌ First coroutine error: {e}")
        return False
    
    # Get the event loop again - should be the same instance
    loop2 = event_loop_manager.get_loop()
    print(f"✅ Got event loop again: {loop2}")
    
    # Verify it's the same loop
    if loop1 is loop2:
        print("✅ Event loop persisted (same instance)")
    else:
        print("❌ Event loop changed (different instance)")
        return False
    
    # Run another coroutine
    try:
        result = run_coroutine(simple_coro())
        print(f"✅ Second coroutine result: {result}")
    except Exception as e:
        print(f"❌ Second coroutine error: {e}")
        return False
    
    print("\n✅ EVENT LOOP PERSISTENCE TEST PASSED!")
    return True

if __name__ == "__main__":
    # Run the tests
    try:
        event_loop_test = test_event_loop_persistence()
        chat_test = test_chat_continuity()
        
        if event_loop_test and chat_test:
            print("\n✅✅✅ ALL TESTS PASSED! Chat continuity issue fixed.")
        else:
            print("\n❌❌❌ SOME TESTS FAILED. Please check the logs.")
    except Exception as e:
        print(f"\n❌❌❌ TEST ERROR: {e}")