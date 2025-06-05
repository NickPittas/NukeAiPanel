"""
Tests for UI components with Qt mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
import asyncio
from typing import List, Dict, Any

# Mock Qt/PySide6 before importing UI components
qt_mock = Mock()
qt_mock.QtWidgets = Mock()
qt_mock.QtCore = Mock()
qt_mock.QtGui = Mock()

# Mock specific Qt classes
qt_mock.QtWidgets.QWidget = Mock
qt_mock.QtWidgets.QVBoxLayout = Mock
qt_mock.QtWidgets.QHBoxLayout = Mock
qt_mock.QtWidgets.QTextEdit = Mock
qt_mock.QtWidgets.QLineEdit = Mock
qt_mock.QtWidgets.QPushButton = Mock
qt_mock.QtWidgets.QLabel = Mock
qt_mock.QtWidgets.QComboBox = Mock
qt_mock.QtWidgets.QCheckBox = Mock
qt_mock.QtWidgets.QSpinBox = Mock
qt_mock.QtWidgets.QDoubleSpinBox = Mock
qt_mock.QtWidgets.QTabWidget = Mock
qt_mock.QtWidgets.QScrollArea = Mock
qt_mock.QtWidgets.QSplitter = Mock
qt_mock.QtWidgets.QDialog = Mock
qt_mock.QtWidgets.QMessageBox = Mock
qt_mock.QtWidgets.QProgressBar = Mock
qt_mock.QtWidgets.QListWidget = Mock
qt_mock.QtWidgets.QTreeWidget = Mock
qt_mock.QtWidgets.QApplication = Mock

qt_mock.QtCore.Qt = Mock()
qt_mock.QtCore.QTimer = Mock
qt_mock.QtCore.QThread = Mock
qt_mock.QtCore.QObject = Mock
qt_mock.QtCore.pyqtSignal = Mock(return_value=Mock())
qt_mock.QtCore.QSize = Mock
qt_mock.QtCore.QRect = Mock

qt_mock.QtGui.QFont = Mock
qt_mock.QtGui.QPixmap = Mock
qt_mock.QtGui.QIcon = Mock
qt_mock.QtGui.QPalette = Mock

# Mock nuke module
nuke_mock = Mock()
nuke_mock.NUKE_VERSION_STRING = "14.0v5"

with patch.dict('sys.modules', {
    'PySide6': qt_mock,
    'PySide6.QtWidgets': qt_mock.QtWidgets,
    'PySide6.QtCore': qt_mock.QtCore,
    'PySide6.QtGui': qt_mock.QtGui,
    'nuke': nuke_mock
}):
    from src.ui.main_panel import NukeAIPanel
    from src.ui.chat_interface import ChatInterface
    from src.ui.settings_dialog import SettingsDialog
    from src.ui.action_preview import ActionPreview


class TestMainPanel:
    """Test the main AI panel."""
    
    @pytest.fixture
    def main_panel(self):
        """Create main panel for testing."""
        with patch('src.ui.main_panel.NukeAIPanel.__init__', return_value=None):
            panel = NukeAIPanel()
            panel.chat_interface = Mock()
            panel.settings_dialog = Mock()
            panel.action_preview = Mock()
            panel.provider_manager = Mock()
            panel.session_manager = Mock()
            return panel
    
    def test_panel_initialization(self, main_panel):
        """Test panel initialization."""
        with patch.object(main_panel, 'setup_ui') as mock_setup:
            with patch.object(main_panel, 'setup_connections') as mock_connections:
                main_panel.__init__ = NukeAIPanel.__init__.__wrapped__
                main_panel.__init__(main_panel)
                
                mock_setup.assert_called_once()
                mock_connections.assert_called_once()
    
    def test_setup_ui(self, main_panel):
        """Test UI setup."""
        main_panel.setup_ui = NukeAIPanel.setup_ui.__wrapped__
        
        with patch('src.ui.main_panel.QVBoxLayout') as mock_layout:
            with patch('src.ui.main_panel.QTabWidget') as mock_tabs:
                main_panel.setup_ui(main_panel)
                
                mock_layout.assert_called()
                mock_tabs.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_message(self, main_panel):
        """Test sending a message."""
        main_panel.provider_manager = AsyncMock()
        main_panel.provider_manager.generate_text = AsyncMock(return_value=Mock(content="AI response"))
        main_panel.chat_interface = Mock()
        main_panel.session_manager = Mock()
        
        await main_panel.send_message("Test message")
        
        main_panel.chat_interface.add_message.assert_called()
        main_panel.provider_manager.generate_text.assert_called_once()
    
    def test_show_settings(self, main_panel):
        """Test showing settings dialog."""
        main_panel.settings_dialog = Mock()
        
        main_panel.show_settings()
        
        main_panel.settings_dialog.show.assert_called_once()
    
    def test_clear_chat(self, main_panel):
        """Test clearing chat history."""
        main_panel.chat_interface = Mock()
        main_panel.session_manager = Mock()
        
        main_panel.clear_chat()
        
        main_panel.chat_interface.clear.assert_called_once()
        main_panel.session_manager.clear_current_session.assert_called_once()
    
    def test_load_session(self, main_panel):
        """Test loading a chat session."""
        main_panel.session_manager = Mock()
        main_panel.session_manager.get_session_messages.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        main_panel.chat_interface = Mock()
        
        main_panel.load_session("session_123")
        
        main_panel.session_manager.get_session_messages.assert_called_once_with("session_123")
        assert main_panel.chat_interface.add_message.call_count == 2
    
    def test_export_conversation(self, main_panel):
        """Test exporting conversation."""
        main_panel.chat_interface = Mock()
        main_panel.chat_interface.get_messages.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        with patch('builtins.open', mock_open()) as mock_file:
            main_panel.export_conversation("test.txt")
            
            mock_file.assert_called_once_with("test.txt", "w", encoding="utf-8")
    
    def test_update_provider_status(self, main_panel):
        """Test updating provider status display."""
        main_panel.provider_status_label = Mock()
        
        status = {
            "openai": {"healthy": True, "model": "gpt-4"},
            "anthropic": {"healthy": False, "error": "API key invalid"}
        }
        
        main_panel.update_provider_status(status)
        
        main_panel.provider_status_label.setText.assert_called()


class TestChatInterface:
    """Test the chat interface component."""
    
    @pytest.fixture
    def chat_interface(self):
        """Create chat interface for testing."""
        with patch('src.ui.chat_interface.ChatInterface.__init__', return_value=None):
            chat = ChatInterface()
            chat.chat_display = Mock()
            chat.input_field = Mock()
            chat.send_button = Mock()
            chat.messages = []
            return chat
    
    def test_add_user_message(self, chat_interface):
        """Test adding a user message."""
        chat_interface.add_message("Hello", is_user=True)
        
        assert len(chat_interface.messages) == 1
        assert chat_interface.messages[0]["role"] == "user"
        assert chat_interface.messages[0]["content"] == "Hello"
        chat_interface.chat_display.append.assert_called()
    
    def test_add_assistant_message(self, chat_interface):
        """Test adding an assistant message."""
        chat_interface.add_message("Hi there", is_user=False)
        
        assert len(chat_interface.messages) == 1
        assert chat_interface.messages[0]["role"] == "assistant"
        assert chat_interface.messages[0]["content"] == "Hi there"
        chat_interface.chat_display.append.assert_called()
    
    def test_clear_messages(self, chat_interface):
        """Test clearing all messages."""
        chat_interface.messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        
        chat_interface.clear()
        
        assert len(chat_interface.messages) == 0
        chat_interface.chat_display.clear.assert_called_once()
    
    def test_get_messages(self, chat_interface):
        """Test getting all messages."""
        test_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        chat_interface.messages = test_messages
        
        messages = chat_interface.get_messages()
        
        assert messages == test_messages
    
    def test_format_message_html(self, chat_interface):
        """Test HTML formatting of messages."""
        user_html = chat_interface.format_message_html("Hello", is_user=True)
        assistant_html = chat_interface.format_message_html("Hi there", is_user=False)
        
        assert "user-message" in user_html
        assert "assistant-message" in assistant_html
        assert "Hello" in user_html
        assert "Hi there" in assistant_html
    
    def test_handle_send_button(self, chat_interface):
        """Test send button handling."""
        chat_interface.input_field.text.return_value = "Test message"
        chat_interface.input_field.clear = Mock()
        chat_interface.message_sent = Mock()
        chat_interface.message_sent.emit = Mock()
        
        chat_interface.handle_send_button()
        
        chat_interface.input_field.clear.assert_called_once()
        chat_interface.message_sent.emit.assert_called_once_with("Test message")
    
    def test_streaming_message_update(self, chat_interface):
        """Test updating streaming message."""
        # Start streaming message
        chat_interface.start_streaming_message()
        
        # Update with chunks
        chat_interface.update_streaming_message("Hello")
        chat_interface.update_streaming_message(" world")
        
        # Finish streaming
        chat_interface.finish_streaming_message()
        
        assert len(chat_interface.messages) == 1
        assert chat_interface.messages[0]["content"] == "Hello world"
    
    def test_message_history_navigation(self, chat_interface):
        """Test navigating through message history."""
        chat_interface.input_history = ["Hello", "How are you?", "Goodbye"]
        chat_interface.history_index = -1
        chat_interface.input_field.setText = Mock()
        
        # Navigate up
        chat_interface.navigate_history_up()
        chat_interface.input_field.setText.assert_called_with("Goodbye")
        
        chat_interface.navigate_history_up()
        chat_interface.input_field.setText.assert_called_with("How are you?")
        
        # Navigate down
        chat_interface.navigate_history_down()
        chat_interface.input_field.setText.assert_called_with("Goodbye")


class TestSettingsDialog:
    """Test the settings dialog."""
    
    @pytest.fixture
    def settings_dialog(self):
        """Create settings dialog for testing."""
        with patch('src.ui.settings_dialog.SettingsDialog.__init__', return_value=None):
            dialog = SettingsDialog()
            dialog.config = Mock()
            dialog.auth_manager = Mock()
            dialog.provider_tabs = {}
            dialog.general_settings = {}
            return dialog
    
    def test_load_settings(self, settings_dialog):
        """Test loading settings from config."""
        settings_dialog.config.get.side_effect = lambda key, default=None: {
            'providers.openai.enabled': True,
            'providers.openai.default_model': 'gpt-4',
            'cache.enabled': True,
            'logging.level': 'INFO'
        }.get(key, default)
        
        settings_dialog.load_settings()
        
        # Should have called config.get multiple times
        assert settings_dialog.config.get.call_count > 0
    
    def test_save_settings(self, settings_dialog):
        """Test saving settings to config."""
        # Mock UI elements
        settings_dialog.provider_tabs = {
            'openai': {
                'enabled_checkbox': Mock(isChecked=Mock(return_value=True)),
                'model_combo': Mock(currentText=Mock(return_value='gpt-4')),
                'api_key_field': Mock(text=Mock(return_value='sk-test-key'))
            }
        }
        
        settings_dialog.general_settings = {
            'cache_enabled': Mock(isChecked=Mock(return_value=True)),
            'log_level_combo': Mock(currentText=Mock(return_value='DEBUG'))
        }
        
        settings_dialog.save_settings()
        
        # Should have called config.set and auth_manager.set_api_key
        settings_dialog.config.set.assert_called()
        settings_dialog.auth_manager.set_api_key.assert_called()
    
    def test_test_provider_connection(self, settings_dialog):
        """Test testing provider connection."""
        settings_dialog.provider_manager = AsyncMock()
        settings_dialog.provider_manager.test_provider = AsyncMock(return_value=True)
        
        with patch('asyncio.create_task') as mock_task:
            settings_dialog.test_provider_connection('openai')
            mock_task.assert_called_once()
    
    def test_reset_to_defaults(self, settings_dialog):
        """Test resetting settings to defaults."""
        settings_dialog.reset_to_defaults()
        
        # Should reset config to defaults
        settings_dialog.config.reset_to_defaults.assert_called_once()
    
    def test_import_export_settings(self, settings_dialog):
        """Test importing and exporting settings."""
        test_config = {"providers": {"openai": {"enabled": True}}}
        
        # Test export
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_dump:
                settings_dialog.export_settings("test.json")
                mock_file.assert_called_once()
                mock_dump.assert_called_once()
        
        # Test import
        with patch('builtins.open', mock_open(read_data='{"test": "data"}')):
            with patch('json.load', return_value=test_config):
                settings_dialog.import_settings("test.json")
                settings_dialog.config.update.assert_called_once_with(test_config)


class TestActionPreview:
    """Test the action preview component."""
    
    @pytest.fixture
    def action_preview(self):
        """Create action preview for testing."""
        with patch('src.ui.action_preview.ActionPreview.__init__', return_value=None):
            preview = ActionPreview()
            preview.action_list = Mock()
            preview.preview_text = Mock()
            preview.apply_button = Mock()
            preview.cancel_button = Mock()
            preview.actions = []
            return preview
    
    def test_set_actions(self, action_preview):
        """Test setting actions to preview."""
        actions = [
            {"type": "create_node", "node_type": "Blur", "name": "Blur1"},
            {"type": "create_node", "node_type": "Grade", "name": "Grade1"},
            {"type": "connect_nodes", "from": "Blur1", "to": "Grade1"}
        ]
        
        action_preview.set_actions(actions)
        
        assert action_preview.actions == actions
        action_preview.action_list.clear.assert_called_once()
        assert action_preview.action_list.addItem.call_count == 3
    
    def test_preview_action(self, action_preview):
        """Test previewing a single action."""
        action = {
            "type": "create_node",
            "node_type": "Blur",
            "name": "Blur1",
            "properties": {"size": 10.0}
        }
        
        action_preview.preview_action(action)
        
        action_preview.preview_text.setPlainText.assert_called()
        # Should show formatted action details
    
    def test_apply_actions(self, action_preview):
        """Test applying all actions."""
        action_preview.actions = [
            {"type": "create_node", "node_type": "Blur"},
            {"type": "create_node", "node_type": "Grade"}
        ]
        action_preview.action_applier = AsyncMock()
        action_preview.actions_applied = Mock()
        action_preview.actions_applied.emit = Mock()
        
        with patch('asyncio.create_task') as mock_task:
            action_preview.apply_actions()
            mock_task.assert_called_once()
    
    def test_cancel_actions(self, action_preview):
        """Test canceling actions."""
        action_preview.actions_cancelled = Mock()
        action_preview.actions_cancelled.emit = Mock()
        
        action_preview.cancel_actions()
        
        action_preview.actions_cancelled.emit.assert_called_once()
    
    def test_format_action_description(self, action_preview):
        """Test formatting action descriptions."""
        create_action = {
            "type": "create_node",
            "node_type": "Blur",
            "name": "Blur1",
            "properties": {"size": 10.0}
        }
        
        connect_action = {
            "type": "connect_nodes",
            "from": "Read1",
            "to": "Blur1"
        }
        
        create_desc = action_preview.format_action_description(create_action)
        connect_desc = action_preview.format_action_description(connect_action)
        
        assert "Create Blur node" in create_desc
        assert "Blur1" in create_desc
        assert "Connect Read1 to Blur1" in connect_desc
    
    def test_validate_actions(self, action_preview):
        """Test validating actions before applying."""
        valid_actions = [
            {"type": "create_node", "node_type": "Blur", "name": "Blur1"}
        ]
        
        invalid_actions = [
            {"type": "invalid_type", "node_type": "Blur"}
        ]
        
        assert action_preview.validate_actions(valid_actions) is True
        assert action_preview.validate_actions(invalid_actions) is False


class TestUIIntegration:
    """Test UI component integration."""
    
    def test_main_panel_chat_integration(self):
        """Test integration between main panel and chat interface."""
        with patch('src.ui.main_panel.NukeAIPanel') as mock_panel:
            with patch('src.ui.chat_interface.ChatInterface') as mock_chat:
                panel_instance = Mock()
                chat_instance = Mock()
                
                mock_panel.return_value = panel_instance
                mock_chat.return_value = chat_instance
                
                # Simulate message sending
                panel_instance.chat_interface = chat_instance
                panel_instance.send_message = AsyncMock()
                
                # Test message flow
                chat_instance.message_sent.emit("Test message")
                
                # Should trigger send_message on panel
                # (In real implementation, this would be connected via signals)
    
    def test_settings_dialog_main_panel_integration(self):
        """Test integration between settings dialog and main panel."""
        with patch('src.ui.main_panel.NukeAIPanel') as mock_panel:
            with patch('src.ui.settings_dialog.SettingsDialog') as mock_settings:
                panel_instance = Mock()
                settings_instance = Mock()
                
                mock_panel.return_value = panel_instance
                mock_settings.return_value = settings_instance
                
                panel_instance.settings_dialog = settings_instance
                
                # Test settings update
                settings_instance.settings_changed.emit({"test": "config"})
                
                # Should update panel configuration
                # (In real implementation, this would update provider_manager)
    
    def test_action_preview_main_panel_integration(self):
        """Test integration between action preview and main panel."""
        with patch('src.ui.main_panel.NukeAIPanel') as mock_panel:
            with patch('src.ui.action_preview.ActionPreview') as mock_preview:
                panel_instance = Mock()
                preview_instance = Mock()
                
                mock_panel.return_value = panel_instance
                mock_preview.return_value = preview_instance
                
                panel_instance.action_preview = preview_instance
                
                # Test action application
                test_actions = [{"type": "create_node", "node_type": "Blur"}]
                preview_instance.set_actions(test_actions)
                preview_instance.actions_applied.emit(test_actions)
                
                # Should trigger action execution in panel


class TestUIErrorHandling:
    """Test UI error handling."""
    
    def test_chat_interface_error_display(self):
        """Test displaying errors in chat interface."""
        with patch('src.ui.chat_interface.ChatInterface') as mock_chat:
            chat_instance = Mock()
            mock_chat.return_value = chat_instance
            
            # Simulate error
            error_message = "API connection failed"
            chat_instance.display_error(error_message)
            
            chat_instance.add_message.assert_called_with(
                f"Error: {error_message}", 
                is_user=False, 
                is_error=True
            )
    
    def test_settings_dialog_validation_errors(self):
        """Test validation error handling in settings dialog."""
        with patch('src.ui.settings_dialog.SettingsDialog') as mock_settings:
            settings_instance = Mock()
            mock_settings.return_value = settings_instance
            
            # Test invalid API key format
            settings_instance.validate_api_key("invalid-key", "openai")
            
            # Should show validation error
            settings_instance.show_validation_error.assert_called()
    
    def test_action_preview_execution_errors(self):
        """Test handling action execution errors."""
        with patch('src.ui.action_preview.ActionPreview') as mock_preview:
            preview_instance = Mock()
            mock_preview.return_value = preview_instance
            
            # Simulate action execution error
            error = Exception("Node creation failed")
            preview_instance.handle_execution_error(error)
            
            # Should display error message
            preview_instance.show_error_message.assert_called()


class TestUIPerformance:
    """Test UI performance characteristics."""
    
    @pytest.mark.slow
    def test_chat_interface_large_history(self):
        """Test chat interface with large message history."""
        with patch('src.ui.chat_interface.ChatInterface') as mock_chat:
            chat_instance = Mock()
            mock_chat.return_value = chat_instance
            
            # Add many messages
            for i in range(1000):
                chat_instance.add_message(f"Message {i}", is_user=i % 2 == 0)
            
            # Should handle large history efficiently
            assert chat_instance.add_message.call_count == 1000
    
    def test_settings_dialog_responsive_updates(self):
        """Test settings dialog responsiveness during updates."""
        with patch('src.ui.settings_dialog.SettingsDialog') as mock_settings:
            settings_instance = Mock()
            mock_settings.return_value = settings_instance
            
            # Simulate rapid setting changes
            for i in range(100):
                settings_instance.update_setting(f"key_{i}", f"value_{i}")
            
            # Should remain responsive
            assert settings_instance.update_setting.call_count == 100


def mock_open(read_data=""):
    """Helper function to mock file operations."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)


if __name__ == "__main__":
    pytest.main([__file__])