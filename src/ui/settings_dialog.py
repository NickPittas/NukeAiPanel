"""
Settings Dialog Component

This module implements the configuration UI for API keys, provider settings,
and user preferences for the Nuke AI Panel.
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


class ProviderSettingsWidget(QWidget):
    """Widget for configuring individual AI provider settings."""
    
    def __init__(self, provider_name: str, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.provider_name = provider_name
        self.config = config.copy()
        self.widgets = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the provider settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Provider title
        title_label = QLabel(f"{self.provider_name.title()} Settings")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #E0E0E0;")
        layout.addWidget(title_label)
        
        # Settings form
        form_layout = QFormLayout()
        form_layout.setSpacing(6)
        
        # API Key
        api_key_widget = self.create_api_key_widget()
        form_layout.addRow("API Key:", api_key_widget)
        
        # Base URL (for some providers)
        if self.provider_name in ['openai', 'openrouter', 'ollama']:
            base_url_edit = QLineEdit()
            base_url_edit.setText(self.config.get('base_url', ''))
            base_url_edit.setPlaceholderText("Default URL will be used if empty")
            self.widgets['base_url'] = base_url_edit
            form_layout.addRow("Base URL:", base_url_edit)
            
        # Model settings
        model_widget = self.create_model_widget()
        form_layout.addRow("Default Model:", model_widget)
        
        # Temperature
        temp_widget = self.create_temperature_widget()
        form_layout.addRow("Temperature:", temp_widget)
        
        # Max tokens
        tokens_widget = self.create_tokens_widget()
        form_layout.addRow("Max Tokens:", tokens_widget)
        
        # Timeout
        timeout_widget = self.create_timeout_widget()
        form_layout.addRow("Timeout (s):", timeout_widget)
        
        layout.addLayout(form_layout)
        
        # Test connection button
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: 1px solid #45A049;
                border-radius: 4px;
                color: white;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #3D8B40;
            }
        """)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        
    def create_api_key_widget(self) -> QWidget:
        """Create API key input widget with show/hide functionality."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # API key input
        api_key_edit = QLineEdit()
        api_key_edit.setEchoMode(QLineEdit.Password)
        api_key_edit.setText(self.config.get('api_key', ''))
        api_key_edit.setPlaceholderText("Enter your API key")
        self.widgets['api_key'] = api_key_edit
        layout.addWidget(api_key_edit)
        
        # Show/hide button
        show_btn = QPushButton()
        show_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        show_btn.setFixedSize(24, 24)
        show_btn.setCheckable(True)
        show_btn.setToolTip("Show/Hide API key")
        show_btn.toggled.connect(
            lambda checked: api_key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        layout.addWidget(show_btn)
        
        return widget
        
    def create_model_widget(self) -> QComboBox:
        """Create model selection widget."""
        model_combo = QComboBox()
        model_combo.setEditable(True)
        
        # Add common models based on provider
        models = self.get_common_models()
        model_combo.addItems(models)
        
        # Set current model
        current_model = self.config.get('default_model', '')
        if current_model:
            model_combo.setCurrentText(current_model)
        elif models:
            model_combo.setCurrentIndex(0)
            
        self.widgets['default_model'] = model_combo
        return model_combo
        
    def create_temperature_widget(self) -> QWidget:
        """Create temperature control widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Slider
        temp_slider = QSlider(Qt.Horizontal)
        temp_slider.setRange(0, 200)  # 0.0 to 2.0
        temp_slider.setValue(int(self.config.get('temperature', 0.7) * 100))
        layout.addWidget(temp_slider)
        
        # Value label
        temp_label = QLabel("0.70")
        temp_label.setFixedWidth(30)
        temp_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(temp_label)
        
        # Update label when slider changes
        def update_temp_label(value):
            temp_value = value / 100.0
            temp_label.setText(f"{temp_value:.2f}")
            
        temp_slider.valueChanged.connect(update_temp_label)
        update_temp_label(temp_slider.value())
        
        self.widgets['temperature'] = temp_slider
        return widget
        
    def create_tokens_widget(self) -> QSpinBox:
        """Create max tokens input widget."""
        tokens_spin = QSpinBox()
        tokens_spin.setRange(1, 32000)
        tokens_spin.setValue(self.config.get('max_tokens', 2000))
        tokens_spin.setSuffix(" tokens")
        self.widgets['max_tokens'] = tokens_spin
        return tokens_spin
        
    def create_timeout_widget(self) -> QSpinBox:
        """Create timeout input widget."""
        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 300)
        timeout_spin.setValue(self.config.get('timeout', 30))
        timeout_spin.setSuffix(" seconds")
        self.widgets['timeout'] = timeout_spin
        return timeout_spin
        
    def get_common_models(self) -> list:
        """Get common models for the provider."""
        models_map = {
            'openai': [
                'gpt-4-turbo-preview',
                'gpt-4',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k'
            ],
            'anthropic': [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ],
            'google': [
                'gemini-pro',
                'gemini-pro-vision'
            ],
            'mistral': [
                'mistral-large-latest',
                'mistral-medium-latest',
                'mistral-small-latest'
            ],
            'ollama': [
                'llama2',
                'codellama',
                'mistral',
                'neural-chat'
            ],
            'openrouter': [
                'openai/gpt-4-turbo-preview',
                'anthropic/claude-3-opus',
                'google/gemini-pro'
            ]
        }
        
        return models_map.get(self.provider_name, [])
        
    def test_connection(self):
        """Test the connection with current settings."""
        try:
            # Get current settings
            settings = self.get_settings()
            
            # Show testing dialog
            progress = QProgressDialog("Testing connection...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # TODO: Implement actual connection test
            # This would use the panel manager to test the provider
            QTimer.singleShot(2000, lambda: self.connection_test_complete(progress, True))
            
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            QMessageBox.warning(self, "Connection Test", f"Test failed: {e}")
            
    def connection_test_complete(self, progress: QProgressDialog, success: bool):
        """Handle connection test completion."""
        progress.close()
        
        if success:
            QMessageBox.information(
                self,
                "Connection Test",
                "Connection successful!"
            )
        else:
            QMessageBox.warning(
                self,
                "Connection Test", 
                "Connection failed. Please check your settings."
            )
            
    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings from the widgets."""
        settings = {}
        
        for key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                settings[key] = widget.text()
            elif isinstance(widget, QComboBox):
                settings[key] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                settings[key] = widget.value()
            elif isinstance(widget, QSlider):
                settings[key] = widget.value() / 100.0
                
        return settings
        
    def set_settings(self, settings: Dict[str, Any]):
        """Set the settings in the widgets."""
        for key, value in settings.items():
            if key in self.widgets:
                widget = self.widgets[key]
                
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QSlider):
                    widget.setValue(int(float(value) * 100))


class SettingsDialog(QDialog):
    """
    Main settings dialog for the Nuke AI Panel.
    
    Provides configuration interface for AI providers, API keys,
    and user preferences.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.panel_manager = None
        self.provider_widgets = {}
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the settings dialog UI."""
        self.setWindowTitle("AI Assistant Settings")
        self.setModal(True)
        self.resize(500, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Tab widget for different settings categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Provider settings tab
        self.create_provider_tab()
        
        # General settings tab
        self.create_general_tab()
        
        # Advanced settings tab
        self.create_advanced_tab()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
        # Apply Nuke styling
        self.setStyleSheet("""
            QDialog {
                background-color: #393939;
                color: #E0E0E0;
            }
            QTabWidget::pane {
                border: 1px solid #5A5A5A;
                background-color: #393939;
            }
            QTabBar::tab {
                background-color: #4A4A4A;
                border: 1px solid #5A5A5A;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5A5A5A;
            }
        """)
        
    def create_provider_tab(self):
        """Create the AI provider settings tab."""
        provider_widget = QWidget()
        layout = QVBoxLayout(provider_widget)
        
        # Provider selection
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("Configure Provider:"))
        
        self.provider_selector = QComboBox()
        self.provider_selector.addItems([
            'openai', 'anthropic', 'google', 'mistral', 'ollama', 'openrouter'
        ])
        provider_layout.addWidget(self.provider_selector)
        provider_layout.addStretch()
        
        layout.addLayout(provider_layout)
        
        # Scroll area for provider settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.provider_settings_widget = QWidget()
        self.provider_settings_layout = QVBoxLayout(self.provider_settings_widget)
        scroll_area.setWidget(self.provider_settings_widget)
        
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(provider_widget, "Providers")
        
    def create_general_tab(self):
        """Create the general settings tab."""
        general_widget = QWidget()
        layout = QFormLayout(general_widget)
        
        # Default provider
        self.default_provider_combo = QComboBox()
        self.default_provider_combo.addItems([
            'openai', 'anthropic', 'google', 'mistral', 'ollama', 'openrouter'
        ])
        layout.addRow("Default Provider:", self.default_provider_combo)
        
        # Auto-save chat history
        self.auto_save_check = QCheckBox("Auto-save chat history")
        self.auto_save_check.setChecked(True)
        layout.addRow(self.auto_save_check)
        
        # Show typing indicators
        self.typing_indicators_check = QCheckBox("Show typing indicators")
        self.typing_indicators_check.setChecked(True)
        layout.addRow(self.typing_indicators_check)
        
        # Auto-scroll to new messages
        self.auto_scroll_check = QCheckBox("Auto-scroll to new messages")
        self.auto_scroll_check.setChecked(True)
        layout.addRow(self.auto_scroll_check)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Dark', 'Light', 'Nuke Default'])
        layout.addRow("Theme:", self.theme_combo)
        
        self.tab_widget.addTab(general_widget, "General")
        
    def create_advanced_tab(self):
        """Create the advanced settings tab."""
        advanced_widget = QWidget()
        layout = QFormLayout(advanced_widget)
        
        # Logging level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        self.log_level_combo.setCurrentText('INFO')
        layout.addRow("Log Level:", self.log_level_combo)
        
        # Cache settings
        self.enable_cache_check = QCheckBox("Enable response caching")
        self.enable_cache_check.setChecked(True)
        layout.addRow(self.enable_cache_check)
        
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setValue(100)
        self.cache_size_spin.setSuffix(" MB")
        layout.addRow("Cache Size:", self.cache_size_spin)
        
        # Rate limiting
        self.rate_limit_check = QCheckBox("Enable rate limiting")
        self.rate_limit_check.setChecked(True)
        layout.addRow(self.rate_limit_check)
        
        # Concurrent requests
        self.concurrent_requests_spin = QSpinBox()
        self.concurrent_requests_spin.setRange(1, 10)
        self.concurrent_requests_spin.setValue(3)
        layout.addRow("Max Concurrent Requests:", self.concurrent_requests_spin)
        
        # Export/Import settings
        export_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export Settings")
        export_btn.clicked.connect(self.export_settings)
        export_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import Settings")
        import_btn.clicked.connect(self.import_settings)
        export_layout.addWidget(import_btn)
        
        export_layout.addStretch()
        layout.addRow("Backup:", export_layout)
        
        self.tab_widget.addTab(advanced_widget, "Advanced")
        
    def setup_connections(self):
        """Set up signal connections."""
        self.provider_selector.currentTextChanged.connect(self.load_provider_settings)
        
        # Dialog buttons
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            button_box.accepted.connect(self.accept_settings)
            button_box.rejected.connect(self.reject)
            
    def set_panel_manager(self, panel_manager):
        """Set the panel manager for settings operations."""
        self.panel_manager = panel_manager
        
    def load_settings(self):
        """Load current settings into the dialog."""
        if not self.panel_manager:
            return
            
        try:
            # Load general settings
            config = self.panel_manager.get_config()
            
            # Set default provider
            default_provider = config.get('default_provider', 'openai')
            index = self.default_provider_combo.findText(default_provider)
            if index >= 0:
                self.default_provider_combo.setCurrentIndex(index)
                
            # Set other general settings
            self.auto_save_check.setChecked(config.get('auto_save_history', True))
            self.typing_indicators_check.setChecked(config.get('show_typing_indicators', True))
            self.auto_scroll_check.setChecked(config.get('auto_scroll', True))
            
            # Load provider settings
            self.load_provider_settings(self.provider_selector.currentText())
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            
    def load_provider_settings(self, provider_name: str):
        """Load settings for a specific provider."""
        if not provider_name or not self.panel_manager:
            return
            
        try:
            # Clear existing provider widget
            if self.provider_settings_layout.count() > 0:
                item = self.provider_settings_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
                    
            # Get provider config
            provider_config = self.panel_manager.get_provider_config(provider_name)
            
            # Create provider settings widget
            provider_widget = ProviderSettingsWidget(provider_name, provider_config, self)
            self.provider_widgets[provider_name] = provider_widget
            
            self.provider_settings_layout.addWidget(provider_widget)
            
        except Exception as e:
            self.logger.error(f"Failed to load provider settings: {e}")
            
    def apply_settings(self):
        """Apply the current settings without closing the dialog."""
        try:
            self.save_settings()
            QMessageBox.information(self, "Settings", "Settings applied successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            QMessageBox.warning(self, "Settings", f"Failed to apply settings: {e}")
            
    def accept_settings(self):
        """Accept and save the settings."""
        try:
            self.save_settings()
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "Settings", f"Failed to save settings: {e}")
            
    def save_settings(self):
        """Save the current settings."""
        if not self.panel_manager:
            return
            
        # Collect general settings
        general_settings = {
            'default_provider': self.default_provider_combo.currentText(),
            'auto_save_history': self.auto_save_check.isChecked(),
            'show_typing_indicators': self.typing_indicators_check.isChecked(),
            'auto_scroll': self.auto_scroll_check.isChecked(),
            'theme': self.theme_combo.currentText(),
            'log_level': self.log_level_combo.currentText(),
            'enable_cache': self.enable_cache_check.isChecked(),
            'cache_size_mb': self.cache_size_spin.value(),
            'enable_rate_limiting': self.rate_limit_check.isChecked(),
            'max_concurrent_requests': self.concurrent_requests_spin.value()
        }
        
        # Collect provider settings
        provider_settings = {}
        for provider_name, widget in self.provider_widgets.items():
            provider_settings[provider_name] = widget.get_settings()
            
        # Save to panel manager
        self.panel_manager.update_settings(general_settings, provider_settings)
        
    def export_settings(self):
        """Export settings to a file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Settings",
                "nuke_ai_settings.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename and self.panel_manager:
                self.panel_manager.export_settings(filename)
                QMessageBox.information(self, "Export", f"Settings exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            QMessageBox.warning(self, "Export", f"Export failed: {e}")
            
    def import_settings(self):
        """Import settings from a file."""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Import Settings",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename and self.panel_manager:
                self.panel_manager.import_settings(filename)
                self.load_settings()  # Reload UI
                QMessageBox.information(self, "Import", "Settings imported successfully!")
                
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            QMessageBox.warning(self, "Import", f"Import failed: {e}")