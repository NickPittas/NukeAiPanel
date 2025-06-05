"""
Main Nuke AI Panel

This module implements the primary Nuke panel that serves as the main interface
for the AI chat system, provider selection, and settings management.
"""

import logging
from typing import Optional, Dict, Any

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError:
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from PySide2.QtGui import *

try:
    import nuke
    import nukescripts
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False

from .chat_interface import ChatInterface
from .settings_dialog import SettingsDialog
from ..core.panel_manager import PanelManager


class NukeAIPanel(QWidget):
    """
    Main AI Panel for Nuke integration.
    
    This panel provides the primary interface for AI chat functionality,
    provider selection, and settings management within Nuke.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.panel_manager = None
        self.settings_dialog = None
        
        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.setup_styling()
        
        # Initialize panel manager
        self.initialize_panel_manager()
        
    def setup_ui(self):
        """Set up the main UI layout and components."""
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(400, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Header section
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Chat interface
        self.chat_interface = ChatInterface(self)
        main_layout.addWidget(self.chat_interface, 1)  # Stretch factor 1
        
        # Status bar
        self.status_bar = self.create_status_bar()
        main_layout.addWidget(self.status_bar)
        
    def create_header(self) -> QWidget:
        """Create the header section with provider selection and controls."""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        # Title and settings row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("AI Assistant")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0;")
        title_row.addWidget(title_label)
        
        title_row.addStretch()
        
        # Settings button
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setFlat(True)
        title_row.addWidget(self.settings_btn)
        
        header_layout.addLayout(title_row)
        
        # Provider selection row
        provider_row = QHBoxLayout()
        provider_row.setContentsMargins(0, 0, 0, 0)
        
        provider_label = QLabel("Provider:")
        provider_label.setStyleSheet("color: #B0B0B0;")
        provider_row.addWidget(provider_label)
        
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(120)
        provider_row.addWidget(self.provider_combo)
        
        # Model selection
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #B0B0B0;")
        provider_row.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(150)
        provider_row.addWidget(self.model_combo)
        
        provider_row.addStretch()
        
        # Connection status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #808080; font-size: 12px;")
        self.status_indicator.setToolTip("Disconnected")
        provider_row.addWidget(self.status_indicator)
        
        header_layout.addLayout(provider_row)
        
        return header_widget
        
    def create_status_bar(self) -> QWidget:
        """Create the status bar with connection info and controls."""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status text
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Action buttons
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedHeight(24)
        self.clear_btn.setToolTip("Clear chat history")
        status_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setFixedHeight(24)
        self.export_btn.setToolTip("Export chat history")
        status_layout.addWidget(self.export_btn)
        
        return status_widget
        
    def setup_connections(self):
        """Set up signal connections."""
        self.settings_btn.clicked.connect(self.show_settings)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.clear_btn.clicked.connect(self.clear_chat)
        self.export_btn.clicked.connect(self.export_chat)
        
    def setup_styling(self):
        """Apply Nuke-compatible styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #393939;
                color: #E0E0E0;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 11px;
            }
            
            QComboBox {
                background-color: #4A4A4A;
                border: 1px solid #5A5A5A;
                border-radius: 3px;
                padding: 2px 6px;
                min-height: 18px;
            }
            
            QComboBox:hover {
                border-color: #6A6A6A;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #B0B0B0;
                margin-right: 4px;
            }
            
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #5A5A5A;
                border-radius: 3px;
                padding: 4px 12px;
                min-height: 16px;
            }
            
            QPushButton:hover {
                background-color: #5A5A5A;
                border-color: #6A6A6A;
            }
            
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
            
            QPushButton:flat {
                border: none;
                background-color: transparent;
            }
            
            QPushButton:flat:hover {
                background-color: #4A4A4A;
                border-radius: 3px;
            }
        """)
        
    def initialize_panel_manager(self):
        """Initialize the panel manager and load providers."""
        try:
            self.panel_manager = PanelManager(self)
            self.panel_manager.status_changed.connect(self.update_status)
            self.panel_manager.provider_changed.connect(self.update_provider_info)
            self.panel_manager.error_occurred.connect(self.handle_error)
            
            # Load available providers
            self.load_providers()
            
            # Connect chat interface to panel manager
            self.chat_interface.set_panel_manager(self.panel_manager)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize panel manager: {e}")
            self.update_status(f"Initialization error: {e}", "error")
            
    def load_providers(self):
        """Load available AI providers into the combo box."""
        if not self.panel_manager:
            return
            
        try:
            providers = self.panel_manager.get_available_providers()
            
            self.provider_combo.clear()
            for provider_name in providers:
                self.provider_combo.addItem(provider_name)
                
            # Set default provider if available
            if providers:
                default_provider = self.panel_manager.get_default_provider()
                if default_provider in providers:
                    self.provider_combo.setCurrentText(default_provider)
                    
        except Exception as e:
            self.logger.error(f"Failed to load providers: {e}")
            
    def on_provider_changed(self, provider_name: str):
        """Handle provider selection change."""
        if not self.panel_manager or not provider_name:
            return
            
        try:
            # Update panel manager
            self.panel_manager.set_current_provider(provider_name)
            
            # Load models for selected provider
            self.load_models(provider_name)
            
            # Update status
            self.update_connection_status()
            
        except Exception as e:
            self.logger.error(f"Failed to change provider: {e}")
            self.handle_error(f"Provider change failed: {e}")
            
    def load_models(self, provider_name: str):
        """Load available models for the selected provider."""
        if not self.panel_manager:
            return
            
        try:
            models = self.panel_manager.get_available_models(provider_name)
            
            self.model_combo.clear()
            for model_name in models:
                self.model_combo.addItem(model_name)
                
            # Set default model if available
            if models:
                default_model = self.panel_manager.get_default_model(provider_name)
                if default_model in models:
                    self.model_combo.setCurrentText(default_model)
                    
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            
    def on_model_changed(self, model_name: str):
        """Handle model selection change."""
        if not self.panel_manager or not model_name:
            return
            
        try:
            self.panel_manager.set_current_model(model_name)
            self.update_connection_status()
            
        except Exception as e:
            self.logger.error(f"Failed to change model: {e}")
            
    def update_connection_status(self):
        """Update the connection status indicator."""
        if not self.panel_manager:
            self.status_indicator.setStyleSheet("color: #808080; font-size: 12px;")
            self.status_indicator.setToolTip("Disconnected")
            return
            
        try:
            is_connected = self.panel_manager.is_provider_connected()
            
            if is_connected:
                self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 12px;")
                self.status_indicator.setToolTip("Connected")
            else:
                self.status_indicator.setStyleSheet("color: #F44336; font-size: 12px;")
                self.status_indicator.setToolTip("Disconnected")
                
        except Exception as e:
            self.logger.error(f"Failed to update connection status: {e}")
            self.status_indicator.setStyleSheet("color: #FF9800; font-size: 12px;")
            self.status_indicator.setToolTip("Status unknown")
            
    def show_settings(self):
        """Show the settings dialog."""
        try:
            if not self.settings_dialog:
                self.settings_dialog = SettingsDialog(self)
                
            if self.panel_manager:
                self.settings_dialog.set_panel_manager(self.panel_manager)
                
            result = self.settings_dialog.exec_()
            
            if result == QDialog.Accepted:
                # Reload providers after settings change
                self.load_providers()
                self.update_connection_status()
                
        except Exception as e:
            self.logger.error(f"Failed to show settings: {e}")
            self.handle_error(f"Settings error: {e}")
            
    def clear_chat(self):
        """Clear the chat history."""
        try:
            reply = QMessageBox.question(
                self,
                "Clear Chat",
                "Are you sure you want to clear the chat history?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.chat_interface.clear_history()
                if self.panel_manager:
                    self.panel_manager.clear_session()
                    
        except Exception as e:
            self.logger.error(f"Failed to clear chat: {e}")
            
    def export_chat(self):
        """Export the chat history."""
        try:
            if not self.panel_manager:
                return
                
            history = self.panel_manager.get_chat_history()
            if not history:
                QMessageBox.information(self, "Export", "No chat history to export.")
                return
                
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Chat History",
                "chat_history.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                self.panel_manager.export_chat_history(filename)
                QMessageBox.information(self, "Export", f"Chat history exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Failed to export chat: {e}")
            self.handle_error(f"Export failed: {e}")
            
    def update_status(self, message: str, status_type: str = "info"):
        """Update the status bar message."""
        self.status_label.setText(message)
        
        # Color coding based on status type
        colors = {
            "info": "#B0B0B0",
            "success": "#4CAF50", 
            "warning": "#FF9800",
            "error": "#F44336"
        }
        
        color = colors.get(status_type, "#B0B0B0")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        
    def update_provider_info(self, provider_name: str, model_name: str):
        """Update UI when provider/model changes."""
        # Update combo boxes without triggering signals
        self.provider_combo.blockSignals(True)
        self.model_combo.blockSignals(True)
        
        try:
            if provider_name:
                index = self.provider_combo.findText(provider_name)
                if index >= 0:
                    self.provider_combo.setCurrentIndex(index)
                    
            if model_name:
                index = self.model_combo.findText(model_name)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                    
        finally:
            self.provider_combo.blockSignals(False)
            self.model_combo.blockSignals(False)
            
        self.update_connection_status()
        
    def handle_error(self, error_message: str):
        """Handle error messages from the panel manager."""
        self.update_status(error_message, "error")
        
        # Show error dialog for critical errors
        if "API key" in error_message.lower() or "authentication" in error_message.lower():
            QMessageBox.warning(
                self,
                "Configuration Error",
                f"{error_message}\n\nPlease check your settings."
            )
            
    def get_panel_manager(self) -> Optional[PanelManager]:
        """Get the panel manager instance."""
        return self.panel_manager
        
    def closeEvent(self, event):
        """Handle panel close event."""
        try:
            if self.panel_manager:
                self.panel_manager.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        finally:
            event.accept()


# Nuke panel registration
def create_ai_panel():
    """Create and return the AI panel widget."""
    return NukeAIPanel()


def register_panel():
    """Register the AI panel with Nuke."""
    if not NUKE_AVAILABLE:
        return
        
    try:
        # Register the panel
        nukescripts.registerPanel(
            'com.nukeaipanel.AIAssistant',
            create_ai_panel
        )
        
        # Add to Nuke menu
        nuke.menu('Nuke').addCommand(
            'AI Assistant/Show Panel',
            'nukescripts.showPanel("com.nukeaipanel.AIAssistant")'
        )
        
    except Exception as e:
        print(f"Failed to register AI panel: {e}")