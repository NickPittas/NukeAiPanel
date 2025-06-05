"""
Settings Dialog Component

This module implements the configuration UI for API keys, provider settings,
and user preferences for the Nuke AI Panel.
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
    HAS_QT = True
except ImportError:
    HAS_QT = False
    # Create minimal fallback classes for testing
    class QWidget:
        def __init__(self, parent=None): pass
        def setStyleSheet(self, style): pass
        def deleteLater(self): pass
    
    class QVBoxLayout:
        def __init__(self, parent=None): pass
        def setContentsMargins(self, *args): pass
        def setSpacing(self, spacing): pass
        def addWidget(self, widget): pass
        def addLayout(self, layout): pass
        def addStretch(self): pass
        def takeAt(self, index): return type('Item', (), {'widget': lambda: None})()
        def count(self): return 0
    
    class QHBoxLayout:
        def __init__(self): pass
        def setContentsMargins(self, *args): pass
        def addWidget(self, widget): pass
        def addStretch(self): pass
        def addLayout(self, layout): pass
    
    class QFormLayout:
        def __init__(self, parent=None): pass
        def setSpacing(self, spacing): pass
        def addRow(self, label, widget=None): pass
    
    class QLabel:
        def __init__(self, text=""): pass
        def setStyleSheet(self, style): pass
        def setText(self, text): pass
        def setFixedWidth(self, width): pass
        def setAlignment(self, alignment): pass
    
    class QLineEdit:
        Password = 1
        Normal = 0
        def __init__(self): pass
        def setEchoMode(self, mode): pass
        def setText(self, text): pass
        def setPlaceholderText(self, text): pass
        def text(self): return ""
    
    class QPushButton:
        def __init__(self, text=""): pass
        def setIcon(self, icon): pass
        def setFixedSize(self, w, h): pass
        def setCheckable(self, checkable): pass
        def setToolTip(self, tip): pass
        def setStyleSheet(self, style): pass
        def setFixedHeight(self, height): pass
        clicked = None
        toggled = None
    
    class QComboBox:
        def __init__(self): pass
        def setEditable(self, editable): pass
        def addItems(self, items): pass
        def setCurrentText(self, text): pass
        def setCurrentIndex(self, index): pass
        def currentText(self): return ""
        def findText(self, text): return -1
    
    class QSlider:
        def __init__(self, orientation): pass
        def setRange(self, min_val, max_val): pass
        def setValue(self, value): pass
        def value(self): return 0
        valueChanged = None
    
    class QSpinBox:
        def __init__(self): pass
        def setRange(self, min_val, max_val): pass
        def setValue(self, value): pass
        def setSuffix(self, suffix): pass
        def value(self): return 0
    
    class QCheckBox:
        def __init__(self, text=""): pass
        def setChecked(self, checked): pass
        def isChecked(self): return False
    
    class QTabWidget:
        def __init__(self): pass
        def addTab(self, widget, title): pass
    
    class QScrollArea:
        def __init__(self): pass
        def setWidgetResizable(self, resizable): pass
        def setHorizontalScrollBarPolicy(self, policy): pass
        def setWidget(self, widget): pass
    
    class QDialog:
        def __init__(self, parent=None): pass
        def setWindowTitle(self, title): pass
        def setModal(self, modal): pass
        def resize(self, w, h): pass
        def setStyleSheet(self, style): pass
        def exec_(self): return 0
        def accept(self): pass
        def reject(self): pass
        def findChild(self, type): return None
    
    class QDialogButtonBox:
        Ok = 1
        Cancel = 2
        Apply = 4
        def __init__(self, buttons): pass
        def button(self, button): return QPushButton()
        accepted = None
        rejected = None
    
    class QProgressDialog:
        def __init__(self, text, cancel_text, min_val, max_val, parent): pass
        def setWindowModality(self, modality): pass
        def show(self): pass
        def close(self): pass
    
    class QMessageBox:
        @staticmethod
        def question(*args): return 0
        @staticmethod
        def information(*args): pass
        @staticmethod
        def warning(*args): pass
    
    class QFileDialog:
        @staticmethod
        def getSaveFileName(*args): return ("", "")
        @staticmethod
        def getOpenFileName(*args): return ("", "")
    
    class QStyle:
        SP_DialogApplyButton = 1
        def standardIcon(self, icon): return None
    
    class Qt:
        Horizontal = 1
        AlignCenter = 1
        ScrollBarAlwaysOff = 1
        WindowModal = 1
    
    Signal = lambda *args: None


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
        
        # API Key (optional for Ollama)
        if self.provider_name.lower() != 'ollama':
            api_key_widget = self.create_api_key_widget()
            form_layout.addRow("API Key:", api_key_widget)
        else:
            # For Ollama, show API key as optional
            api_key_widget = self.create_api_key_widget()
            api_key_label = QLabel("API Key (Optional):")
            api_key_label.setStyleSheet("color: #B0B0B0; font-style: italic;")
            form_layout.addRow(api_key_label, api_key_widget)
        
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
        layout = QHBoxLayout()
        widget.setLayout(layout)
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
            
            # Perform actual connection test
            self._perform_real_connection_test(progress, settings)
            
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            QMessageBox.warning(self, "Connection Test", f"Test failed: {e}")
            
    def _perform_real_connection_test(self, progress: QProgressDialog, settings: Dict[str, Any]):
        """Perform actual connection test with real API calls."""
        import asyncio
        import threading
        import time
        
        def test_thread():
            """Run the connection test in a separate thread."""
            try:
                # Create event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Set a timeout for the entire operation
                    timeout = settings.get('timeout', 30)
                    
                    # Run the actual test with timeout
                    try:
                        success, error_msg = loop.run_until_complete(
                            asyncio.wait_for(
                                self._test_provider_connection_async(settings),
                                timeout=timeout
                            )
                        )
                        
                        # Schedule UI update on main thread
                        QTimer.singleShot(0, lambda: self.connection_test_complete(progress, success, error_msg))
                        
                    except asyncio.TimeoutError:
                        error_msg = f"Connection test timed out after {timeout} seconds"
                        QTimer.singleShot(0, lambda: self.connection_test_complete(progress, False, error_msg))
                        
                finally:
                    # Ensure all tasks are complete before closing
                    try:
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception as e:
                        logging.warning(f"Error cleaning up pending tasks: {e}")
                    finally:
                        loop.close()
                    
            except Exception as e:
                error_msg = f"Test failed: {str(e)}"
                QTimer.singleShot(0, lambda: self.connection_test_complete(progress, False, error_msg))
        
        # Start test in background thread
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()
        
        # Add a watchdog timer to ensure the UI is updated even if the thread hangs
        timeout = settings.get('timeout', 30) + 5  # Add 5 seconds buffer
        QTimer.singleShot(timeout * 1000, lambda: self._check_test_completion(progress, thread))
    
    def _check_test_completion(self, progress: QProgressDialog, thread: threading.Thread):
        """Check if the test thread has completed, force completion if it's still running."""
        if thread.is_alive():
            # Thread is still running after timeout, force completion
            self.connection_test_complete(
                progress,
                False,
                "Connection test timed out. The server may be unresponsive or blocked."
            )
    
    async def _test_provider_connection_async(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Perform async connection test for the provider."""
        try:
            if self.provider_name.lower() == 'ollama':
                return await self._test_ollama_connection(settings)
            elif self.provider_name.lower() == 'openai':
                return await self._test_openai_connection(settings)
            elif self.provider_name.lower() == 'anthropic':
                return await self._test_anthropic_connection(settings)
            elif self.provider_name.lower() == 'google':
                return await self._test_google_connection(settings)
            elif self.provider_name.lower() == 'mistral':
                return await self._test_mistral_connection(settings)
            elif self.provider_name.lower() == 'openrouter':
                return await self._test_openrouter_connection(settings)
            else:
                return False, f"Unknown provider: {self.provider_name}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    async def _test_ollama_connection(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Test Ollama connection."""
        session = None
        try:
            import aiohttp
            
            base_url = settings.get('base_url', 'http://localhost:11434')
            timeout = settings.get('timeout', 30)
            api_key = settings.get('api_key', '').strip()
            
            headers = {'Content-Type': 'application/json'}
            # Add API key if provided (optional for Ollama)
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Use connector with proper cleanup settings
            # Note: keepalive_timeout cannot be used with force_close=True
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                enable_cleanup_closed=True,
                force_close=True
            )
            
            session = aiohttp.ClientSession(headers=headers, connector=connector)
            
            # Use asyncio.wait_for for timeout instead of ClientTimeout
            response = await asyncio.wait_for(
                session.get(f'{base_url}/api/tags'),
                timeout=timeout
            )
            async with response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('models', []))
                    auth_status = "with authentication" if api_key else "without authentication"
                    return True, f"Connected successfully {auth_status}! Found {model_count} models."
                else:
                    return False, f"Ollama server responded with HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {timeout} seconds. Is Ollama running at {base_url}?"
        except aiohttp.ClientConnectorError:
            return False, f"Cannot connect to Ollama at {base_url}. Is Ollama running on the specified URL?"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
        finally:
            # Ensure session is properly closed
            if session and not session.closed:
                try:
                    await session.close()
                except Exception as e:
                    logging.warning(f"Error closing session: {e}")
    
    async def _test_openai_connection(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Test OpenAI connection."""
        session = None
        try:
            import aiohttp
            
            api_key = settings.get('api_key', '').strip()
            if not api_key:
                return False, "API key is required for OpenAI"
            
            base_url = settings.get('base_url', 'https://api.openai.com/v1')
            timeout = settings.get('timeout', 30)
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use connector with proper cleanup settings
            # Note: keepalive_timeout cannot be used with force_close=True
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                enable_cleanup_closed=True,
                force_close=True
            )
            
            session = aiohttp.ClientSession(headers=headers, connector=connector)
            
            # Use asyncio.wait_for for timeout instead of ClientTimeout
            response = await asyncio.wait_for(
                session.get(f'{base_url}/models'),
                timeout=timeout
            )
            async with response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('data', []))
                    return True, f"Connected successfully! Found {model_count} models."
                elif response.status == 401:
                    return False, "Invalid API key"
                else:
                    return False, f"OpenAI API responded with HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
        finally:
            # Ensure session is properly closed
            if session and not session.closed:
                try:
                    await session.close()
                except Exception as e:
                    logging.warning(f"Error closing session: {e}")
    
    async def _test_anthropic_connection(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Test Anthropic connection."""
        try:
            import aiohttp
            
            api_key = settings.get('api_key', '').strip()
            if not api_key:
                return False, "API key is required for Anthropic"
            
            timeout = settings.get('timeout', 30)
            
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            # Test with a minimal message
            payload = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': 'Hi'}]
            }
            
            # Use connector without ClientTimeout to avoid asyncio context issues
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                # Use asyncio.wait_for for timeout instead of ClientTimeout
                response = await asyncio.wait_for(
                    session.post('https://api.anthropic.com/v1/messages', json=payload),
                    timeout=timeout
                )
                async with response:
                    if response.status == 200:
                        return True, "Connected successfully!"
                    elif response.status == 401:
                        return False, "Invalid API key"
                    elif response.status == 400:
                        # Bad request might still indicate valid auth
                        error_data = await response.json()
                        if 'error' in error_data and 'authentication' not in error_data['error'].get('message', '').lower():
                            return True, "Connected successfully! (API key is valid)"
                        return False, f"Authentication failed: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    else:
                        return False, f"Anthropic API responded with HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def _test_google_connection(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Test Google connection."""
        try:
            import aiohttp
            
            api_key = settings.get('api_key', '').strip()
            if not api_key:
                return False, "API key is required for Google"
            
            timeout = settings.get('timeout', 30)
            
            # Test with models endpoint
            url = f'https://generativelanguage.googleapis.com/v1/models?key={api_key}'
            
            # Use connector without ClientTimeout to avoid asyncio context issues
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # Use asyncio.wait_for for timeout instead of ClientTimeout
                response = await asyncio.wait_for(
                    session.get(url),
                    timeout=timeout
                )
                async with response:
                    if response.status == 200:
                        data = await response.json()
                        model_count = len(data.get('models', []))
                        return True, f"Connected successfully! Found {model_count} models."
                    elif response.status == 403:
                        return False, "Invalid API key or insufficient permissions"
                    else:
                        return False, f"Google API responded with HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def _test_mistral_connection(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Test Mistral connection."""
        try:
            import aiohttp
            
            api_key = settings.get('api_key', '').strip()
            if not api_key:
                return False, "API key is required for Mistral"
            
            timeout = settings.get('timeout', 30)
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use connector without ClientTimeout to avoid asyncio context issues
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                # Use asyncio.wait_for for timeout instead of ClientTimeout
                response = await asyncio.wait_for(
                    session.get('https://api.mistral.ai/v1/models'),
                    timeout=timeout
                )
                async with response:
                    if response.status == 200:
                        data = await response.json()
                        model_count = len(data.get('data', []))
                        return True, f"Connected successfully! Found {model_count} models."
                    elif response.status == 401:
                        return False, "Invalid API key"
                    else:
                        return False, f"Mistral API responded with HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def _test_openrouter_connection(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Test OpenRouter connection."""
        session = None
        try:
            import aiohttp
            
            api_key = settings.get('api_key', '').strip()
            if not api_key:
                return False, "API key is required for OpenRouter"
            
            base_url = settings.get('base_url', 'https://openrouter.ai/api/v1')
            timeout = settings.get('timeout', 30)
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use connector with proper cleanup settings
            # Note: keepalive_timeout cannot be used with force_close=True
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                enable_cleanup_closed=True,
                force_close=True
            )
            
            session = aiohttp.ClientSession(headers=headers, connector=connector)
            
            # Use asyncio.wait_for for timeout instead of ClientTimeout
            response = await asyncio.wait_for(
                session.get(f'{base_url}/models'),
                timeout=timeout
            )
            async with response:
                if response.status == 200:
                    data = await response.json()
                    model_count = len(data.get('data', []))
                    return True, f"Connected successfully! Found {model_count} models."
                elif response.status == 401:
                    return False, "Invalid API key"
                else:
                    return False, f"OpenRouter API responded with HTTP {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
        finally:
            # Ensure session is properly closed
            if session and not session.closed:
                try:
                    await session.close()
                except Exception as e:
                    logging.warning(f"Error closing session: {e}")
            
    def connection_test_complete(self, progress: QProgressDialog, success: bool, error_msg: str = ""):
        """Handle connection test completion."""
        progress.close()
        
        if success:
            QMessageBox.information(
                self,
                "Connection Test",
                error_msg if error_msg else "Connection successful!"
            )
        else:
            QMessageBox.warning(
                self,
                "Connection Test",
                error_msg if error_msg else "Connection failed. Please check your settings."
            )
            
    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings from the widgets."""
        settings = {}
        
        try:
            for key, widget in self.widgets.items():
                # Check if widget is still valid before accessing
                if not self._is_widget_valid(widget):
                    continue
                    
                if isinstance(widget, QLineEdit):
                    settings[key] = widget.text()
                elif isinstance(widget, QComboBox):
                    settings[key] = widget.currentText()
                elif isinstance(widget, QSpinBox):
                    settings[key] = widget.value()
                elif isinstance(widget, QSlider):
                    settings[key] = widget.value() / 100.0
        except Exception as e:
            logging.error(f"Error getting settings from widgets: {e}")
                
        return settings
        
    def set_settings(self, settings: Dict[str, Any]):
        """Set the settings in the widgets."""
        try:
            for key, value in settings.items():
                if key in self.widgets:
                    widget = self.widgets[key]
                    
                    # Check if widget is still valid before accessing
                    if not self._is_widget_valid(widget):
                        continue
                    
                    if isinstance(widget, QLineEdit):
                        widget.setText(str(value))
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentText(str(value))
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QSlider):
                        widget.setValue(int(float(value) * 100))
        except Exception as e:
            logging.error(f"Error setting widget values: {e}")
    
    def _is_widget_valid(self, widget) -> bool:
        """Check if a Qt widget is still valid and not deleted."""
        if not HAS_QT:
            return True  # In fallback mode, widgets are always "valid"
            
        try:
            # Try to access a basic property to check if widget is still alive
            if hasattr(widget, 'isVisible'):
                widget.isVisible()
                return True
            return False
        except RuntimeError:
            # Widget has been deleted
            return False
        except Exception:
            # Other errors, assume widget is invalid
            return False


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
            # Check if dialog widgets are still valid before proceeding
            if not self._are_main_widgets_valid():
                self.logger.error("Settings dialog widgets are no longer valid")
                return
                
            self.save_settings()
            QMessageBox.information(self, "Settings", "Settings applied successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            QMessageBox.warning(self, "Settings", f"Failed to apply settings: {e}")
            
    def accept_settings(self):
        """Accept and save the settings."""
        try:
            # Check if dialog widgets are still valid before proceeding
            if not self._are_main_widgets_valid():
                self.logger.error("Settings dialog widgets are no longer valid")
                return
                
            self.save_settings()
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "Settings", f"Failed to save settings: {e}")
            
    def save_settings(self):
        """Save the current settings."""
        if not self.panel_manager:
            return
        
        try:
            # Check if main widgets are still valid
            if not self._are_main_widgets_valid():
                self.logger.error("Cannot save settings - main widgets are no longer valid")
                return
            
            # Collect general settings with widget validation
            general_settings = {}
            
            if self._is_widget_valid(self.default_provider_combo):
                general_settings['default_provider'] = self.default_provider_combo.currentText()
            if self._is_widget_valid(self.auto_save_check):
                general_settings['auto_save_history'] = self.auto_save_check.isChecked()
            if self._is_widget_valid(self.typing_indicators_check):
                general_settings['show_typing_indicators'] = self.typing_indicators_check.isChecked()
            if self._is_widget_valid(self.auto_scroll_check):
                general_settings['auto_scroll'] = self.auto_scroll_check.isChecked()
            if self._is_widget_valid(self.theme_combo):
                general_settings['theme'] = self.theme_combo.currentText()
            if self._is_widget_valid(self.log_level_combo):
                general_settings['log_level'] = self.log_level_combo.currentText()
            if self._is_widget_valid(self.enable_cache_check):
                general_settings['enable_cache'] = self.enable_cache_check.isChecked()
            if self._is_widget_valid(self.cache_size_spin):
                general_settings['cache_size_mb'] = self.cache_size_spin.value()
            if self._is_widget_valid(self.rate_limit_check):
                general_settings['enable_rate_limiting'] = self.rate_limit_check.isChecked()
            if self._is_widget_valid(self.concurrent_requests_spin):
                general_settings['max_concurrent_requests'] = self.concurrent_requests_spin.value()
            
            # Collect provider settings
            provider_settings = {}
            for provider_name, widget in self.provider_widgets.items():
                if self._is_widget_valid(widget):
                    provider_settings[provider_name] = widget.get_settings()
                
            # Save to panel manager
            self.panel_manager.update_settings(general_settings, provider_settings)
            
        except Exception as e:
            self.logger.error(f"Error during save_settings: {e}")
            raise
    
    def _is_widget_valid(self, widget):
        """Check if a Qt widget is still valid and not deleted."""
        try:
            if widget is None:
                return False
            # Try to access a basic property to check if widget is still valid
            widget.isVisible()
            return True
        except (RuntimeError, AttributeError):
            return False

    def _are_main_widgets_valid(self):
        """Check if main dialog widgets are still valid."""
        try:
            # Check key widgets that are accessed during save operations
            return (hasattr(self, 'provider_selector') and self._is_widget_valid(self.provider_selector) and
                    hasattr(self, 'default_provider_combo') and self._is_widget_valid(self.default_provider_combo))
        except Exception:
            return False
        
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