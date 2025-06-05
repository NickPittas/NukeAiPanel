#!/usr/bin/env python3
"""
Test script to reproduce the critical UI functionality issues:
1. Provider dropdown not working
2. Connection tests hanging
"""

import sys
import os
import asyncio
import logging
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.join(os.path.abspath('.'), 'src'))

def test_provider_dropdown_issue():
    """Test provider dropdown functionality."""
    print("🔍 Testing Provider Dropdown Issue...")
    
    try:
        # Import required modules
        from src.ui.main_panel import NukeAIPanel
        from src.core.panel_manager import PanelManager
        
        # Create mock panel manager
        mock_panel_manager = Mock(spec=PanelManager)
        mock_panel_manager.get_available_providers.return_value = ['openai', 'anthropic', 'ollama']
        mock_panel_manager.get_default_provider.return_value = 'openai'
        mock_panel_manager.get_available_models.return_value = ['gpt-4', 'gpt-3.5-turbo']
        mock_panel_manager.get_default_model.return_value = 'gpt-3.5-turbo'
        mock_panel_manager.is_provider_connected.return_value = True
        
        # Create main panel
        panel = NukeAIPanel()
        panel.panel_manager = mock_panel_manager
        
        # Test provider loading
        panel.load_providers()
        print("✅ Provider loading works")
        
        # Test provider change
        print("🔄 Testing provider change...")
        panel.on_provider_changed('anthropic')
        
        # Check if set_current_provider was called
        if mock_panel_manager.set_current_provider.called:
            print("✅ Provider change signal works")
        else:
            print("❌ Provider change signal NOT working")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Provider dropdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_test_issue():
    """Test connection test functionality."""
    print("\n🔍 Testing Connection Test Issue...")
    
    try:
        from src.ui.settings_dialog import ProviderSettingsWidget
        
        # Create provider settings widget
        config = {
            'api_key': 'test-key',
            'base_url': 'http://localhost:11434',
            'timeout': 30
        }
        
        widget = ProviderSettingsWidget('ollama', config)
        
        # Mock the async test method to avoid actual network calls
        async def mock_test_connection(settings):
            await asyncio.sleep(0.1)  # Simulate network delay
            return True, "Connection successful"
        
        widget._test_provider_connection_async = mock_test_connection
        
        # Test connection test method
        print("🔄 Testing connection test...")
        
        # This should not hang
        widget.test_connection()
        print("✅ Connection test initiated without hanging")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_connections():
    """Test Qt signal connections."""
    print("\n🔍 Testing Signal Connections...")
    
    try:
        from src.ui.settings_dialog import SettingsDialog
        from src.core.panel_manager import PanelManager
        
        # Create settings dialog
        dialog = SettingsDialog()
        
        # Create mock panel manager
        mock_panel_manager = Mock(spec=PanelManager)
        mock_panel_manager.get_config.return_value = {'default_provider': 'openai'}
        mock_panel_manager.get_provider_config.return_value = {'api_key': 'test'}
        
        dialog.set_panel_manager(mock_panel_manager)
        
        # Test provider selector signal
        if hasattr(dialog.provider_selector, 'currentTextChanged'):
            print("✅ Provider selector signal exists")
        else:
            print("❌ Provider selector signal missing")
            return False
            
        # Test signal connection
        dialog.provider_selector.currentTextChanged.emit('anthropic')
        print("✅ Signal emission works")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all UI functionality tests."""
    print("🚀 Testing Critical UI Functionality Issues")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    results = []
    
    # Test provider dropdown
    results.append(test_provider_dropdown_issue())
    
    # Test connection tests
    results.append(test_connection_test_issue())
    
    # Test signal connections
    results.append(test_signal_connections())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    if all(results):
        print("✅ All UI functionality tests passed!")
        print("🎯 Issues may be in the actual Qt event loop integration")
    else:
        print("❌ Some UI functionality tests failed!")
        print("🔧 Critical fixes needed for UI components")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)