"""
Panel Manager

Main orchestrator that coordinates all components of the Nuke AI Panel,
including AI providers, session management, and UI interactions.
"""

import logging
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from PySide6.QtCore import QObject, Signal, QThread, QTimer
except ImportError:
    from PySide2.QtCore import QObject, Signal, QThread, QTimer

try:
    import nuke
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False

from ..nuke_integration.context_analyzer import NukeContextAnalyzer
from ..nuke_integration.script_generator import ScriptGenerator
from ..nuke_integration.action_applier import ActionApplier
from ..vfx_knowledge.prompt_engine import PromptEngine
from ..vfx_knowledge.workflow_database import WorkflowDatabase
from ..vfx_knowledge.best_practices import BestPracticesEngine

from ...nuke_ai_panel.core.provider_manager import ProviderManager
from ...nuke_ai_panel.core.config import ConfigManager
from ...nuke_ai_panel.utils.logger import setup_logger

from .session_manager import SessionManager
from .action_engine import ActionEngine


class AIResponseWorker(QThread):
    """Worker thread for AI API calls to prevent UI blocking."""
    
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, provider_manager, message, context=None):
        super().__init__()
        self.provider_manager = provider_manager
        self.message = message
        self.context = context
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Execute the AI request in a separate thread."""
        try:
            # Prepare the full prompt with context
            full_prompt = self.message
            if self.context:
                full_prompt = f"Context: {self.context}\n\nUser: {self.message}"
                
            # Get response from AI provider
            response = self.provider_manager.generate_response(full_prompt)
            self.response_ready.emit(response)
            
        except Exception as e:
            self.logger.error(f"AI response worker failed: {e}")
            self.error_occurred.emit(str(e))


class PanelManager(QObject):
    """
    Main panel manager that orchestrates all AI panel functionality.
    
    Coordinates between UI components, AI providers, Nuke integration,
    and VFX knowledge systems to provide a seamless user experience.
    """
    
    # Signals
    status_changed = Signal(str, str)  # message, type
    provider_changed = Signal(str, str)  # provider, model
    response_received = Signal(str)
    response_started = Signal()
    response_finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = setup_logger(__name__)
        
        # Core components
        self.config_manager = None
        self.provider_manager = None
        self.session_manager = None
        self.action_engine = None
        
        # Nuke integration components
        self.context_analyzer = None
        self.script_generator = None
        self.action_applier = None
        
        # VFX knowledge components
        self.prompt_engine = None
        self.workflow_database = None
        self.best_practices = None
        
        # Worker thread for AI requests
        self.ai_worker = None
        
        # Initialize components
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize all panel manager components."""
        try:
            self.logger.info("Initializing panel manager components...")
            
            # Core components
            self.config_manager = ConfigManager()
            self.provider_manager = ProviderManager(self.config_manager)
            self.session_manager = SessionManager(self)
            self.action_engine = ActionEngine(self)
            
            # Nuke integration components
            if NUKE_AVAILABLE:
                self.context_analyzer = NukeContextAnalyzer()
                self.script_generator = ScriptGenerator()
                self.action_applier = ActionApplier()
            else:
                self.logger.warning("Nuke not available - integration features disabled")
                
            # VFX knowledge components
            self.prompt_engine = PromptEngine()
            self.workflow_database = WorkflowDatabase()
            self.best_practices = BestPracticesEngine()
            
            # Connect signals
            self.setup_signal_connections()
            
            self.logger.info("Panel manager initialized successfully")
            self.status_changed.emit("Panel manager ready", "success")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize panel manager: {e}")
            self.status_changed.emit(f"Initialization failed: {e}", "error")
            raise
            
    def setup_signal_connections(self):
        """Set up signal connections between components."""
        try:
            # Session manager signals
            if self.session_manager:
                self.session_manager.session_updated.connect(
                    lambda: self.status_changed.emit("Session updated", "info")
                )
                
            # Action engine signals
            if self.action_engine:
                self.action_engine.action_completed.connect(
                    lambda msg: self.status_changed.emit(msg, "success")
                )
                self.action_engine.action_failed.connect(
                    lambda msg: self.error_occurred.emit(msg)
                )
                
        except Exception as e:
            self.logger.error(f"Failed to setup signal connections: {e}")
            
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        try:
            if self.provider_manager:
                return self.provider_manager.get_available_providers()
            return []
        except Exception as e:
            self.logger.error(f"Failed to get providers: {e}")
            return []
            
    def get_available_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider."""
        try:
            if self.provider_manager:
                return self.provider_manager.get_available_models(provider_name)
            return []
        except Exception as e:
            self.logger.error(f"Failed to get models for {provider_name}: {e}")
            return []
            
    def get_default_provider(self) -> str:
        """Get the default AI provider."""
        try:
            if self.config_manager:
                return self.config_manager.get('default_provider', 'openai')
            return 'openai'
        except Exception as e:
            self.logger.error(f"Failed to get default provider: {e}")
            return 'openai'
            
    def get_default_model(self, provider_name: str) -> str:
        """Get the default model for a provider."""
        try:
            if self.provider_manager:
                return self.provider_manager.get_default_model(provider_name)
            return ""
        except Exception as e:
            self.logger.error(f"Failed to get default model: {e}")
            return ""
            
    def set_current_provider(self, provider_name: str):
        """Set the current AI provider."""
        try:
            if self.provider_manager:
                self.provider_manager.set_current_provider(provider_name)
                self.provider_changed.emit(provider_name, "")
                self.status_changed.emit(f"Provider changed to {provider_name}", "info")
        except Exception as e:
            self.logger.error(f"Failed to set provider: {e}")
            self.error_occurred.emit(f"Failed to set provider: {e}")
            
    def set_current_model(self, model_name: str):
        """Set the current model for the active provider."""
        try:
            if self.provider_manager:
                current_provider = self.provider_manager.get_current_provider()
                self.provider_manager.set_current_model(model_name)
                self.provider_changed.emit(current_provider, model_name)
                self.status_changed.emit(f"Model changed to {model_name}", "info")
        except Exception as e:
            self.logger.error(f"Failed to set model: {e}")
            self.error_occurred.emit(f"Failed to set model: {e}")
            
    def is_provider_connected(self) -> bool:
        """Check if the current provider is connected and ready."""
        try:
            if self.provider_manager:
                return self.provider_manager.is_connected()
            return False
        except Exception as e:
            self.logger.error(f"Failed to check provider connection: {e}")
            return False
            
    def send_message(self, message: str):
        """Send a message to the AI and handle the response."""
        try:
            if not self.provider_manager:
                self.error_occurred.emit("Provider manager not available")
                return
                
            if not self.is_provider_connected():
                self.error_occurred.emit("AI provider not connected")
                return
                
            # Add message to session
            if self.session_manager:
                self.session_manager.add_user_message(message)
                
            # Get current Nuke context if available
            context = self.get_nuke_context()
            
            # Enhance message with VFX knowledge
            enhanced_message = self.enhance_message_with_knowledge(message, context)
            
            # Start AI response worker
            self.start_ai_response(enhanced_message, context)
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.error_occurred.emit(f"Failed to send message: {e}")
            
    def enhance_message_with_knowledge(self, message: str, context: Optional[str] = None) -> str:
        """Enhance the user message with VFX knowledge and context."""
        try:
            enhanced_message = message
            
            # Add VFX context through prompt engine
            if self.prompt_engine:
                enhanced_message = self.prompt_engine.enhance_prompt(message, context)
                
            # Add best practices if relevant
            if self.best_practices:
                practices = self.best_practices.get_relevant_practices(message)
                if practices:
                    enhanced_message += f"\n\nRelevant best practices: {practices}"
                    
            return enhanced_message
            
        except Exception as e:
            self.logger.error(f"Failed to enhance message: {e}")
            return message
            
    def start_ai_response(self, message: str, context: Optional[str] = None):
        """Start AI response in worker thread."""
        try:
            # Clean up previous worker
            if self.ai_worker and self.ai_worker.isRunning():
                self.ai_worker.terminate()
                self.ai_worker.wait()
                
            # Create new worker
            self.ai_worker = AIResponseWorker(self.provider_manager, message, context)
            self.ai_worker.response_ready.connect(self.handle_ai_response)
            self.ai_worker.error_occurred.connect(self.handle_ai_error)
            
            # Signal response started
            self.response_started.emit()
            self.status_changed.emit("AI is thinking...", "info")
            
            # Start worker
            self.ai_worker.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start AI response: {e}")
            self.error_occurred.emit(f"Failed to start AI response: {e}")
            
    def handle_ai_response(self, response: str):
        """Handle AI response from worker thread."""
        try:
            # Add response to session
            if self.session_manager:
                self.session_manager.add_ai_message(response)
                
            # Check if response contains actionable code
            if self.action_engine:
                self.action_engine.analyze_response(response)
                
            # Emit response
            self.response_received.emit(response)
            self.response_finished.emit()
            self.status_changed.emit("Response received", "success")
            
        except Exception as e:
            self.logger.error(f"Failed to handle AI response: {e}")
            self.error_occurred.emit(f"Failed to handle response: {e}")
            
    def handle_ai_error(self, error_message: str):
        """Handle AI response error."""
        self.response_finished.emit()
        self.error_occurred.emit(error_message)
        self.status_changed.emit(f"AI error: {error_message}", "error")
        
    def get_nuke_context(self) -> Optional[str]:
        """Get current Nuke session context."""
        try:
            if not NUKE_AVAILABLE or not self.context_analyzer:
                return None
                
            context = self.context_analyzer.get_full_context()
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get Nuke context: {e}")
            return None
            
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get available VFX workflows."""
        try:
            if self.workflow_database:
                return self.workflow_database.get_all_workflows()
            return []
        except Exception as e:
            self.logger.error(f"Failed to get workflows: {e}")
            return []
            
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get the current chat history."""
        try:
            if self.session_manager:
                return self.session_manager.get_history()
            return []
        except Exception as e:
            self.logger.error(f"Failed to get chat history: {e}")
            return []
            
    def clear_session(self):
        """Clear the current chat session."""
        try:
            if self.session_manager:
                self.session_manager.clear_session()
                self.status_changed.emit("Session cleared", "info")
        except Exception as e:
            self.logger.error(f"Failed to clear session: {e}")
            
    def export_chat_history(self, filename: str):
        """Export chat history to a file."""
        try:
            if not self.session_manager:
                return
                
            history = self.session_manager.get_history()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Nuke AI Panel Chat History\n")
                f.write(f"Exported: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in history:
                    timestamp = entry.get('timestamp', '')
                    sender = "User" if entry.get('is_user', False) else "AI"
                    message = entry.get('message', '')
                    
                    f.write(f"[{timestamp}] {sender}:\n")
                    f.write(f"{message}\n\n")
                    f.write("-" * 30 + "\n\n")
                    
            self.status_changed.emit(f"History exported to {filename}", "success")
            
        except Exception as e:
            self.logger.error(f"Failed to export chat history: {e}")
            self.error_occurred.emit(f"Export failed: {e}")
            
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        try:
            if self.config_manager:
                return self.config_manager.get_all_config()
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get config: {e}")
            return {}
            
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        try:
            if self.config_manager:
                return self.config_manager.get_provider_config(provider_name)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get provider config: {e}")
            return {}
            
    def update_settings(self, general_settings: Dict[str, Any], provider_settings: Dict[str, Any]):
        """Update panel settings."""
        try:
            if self.config_manager:
                # Update general settings
                for key, value in general_settings.items():
                    self.config_manager.set(key, value)
                    
                # Update provider settings
                for provider, settings in provider_settings.items():
                    self.config_manager.update_provider_config(provider, settings)
                    
                # Save configuration
                self.config_manager.save_config()
                
                # Reinitialize provider manager with new settings
                if self.provider_manager:
                    self.provider_manager.reload_config()
                    
                self.status_changed.emit("Settings updated", "success")
                
        except Exception as e:
            self.logger.error(f"Failed to update settings: {e}")
            self.error_occurred.emit(f"Settings update failed: {e}")
            
    def export_settings(self, filename: str):
        """Export settings to a file."""
        try:
            if self.config_manager:
                config = self.config_manager.get_all_config()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                    
                self.status_changed.emit(f"Settings exported to {filename}", "success")
                
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            self.error_occurred.emit(f"Export failed: {e}")
            
    def import_settings(self, filename: str):
        """Import settings from a file."""
        try:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Settings file not found: {filename}")
                
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            if self.config_manager:
                self.config_manager.load_from_dict(config)
                self.config_manager.save_config()
                
                # Reinitialize components
                if self.provider_manager:
                    self.provider_manager.reload_config()
                    
                self.status_changed.emit("Settings imported successfully", "success")
                
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            self.error_occurred.emit(f"Import failed: {e}")
            
    def cleanup(self):
        """Clean up resources when panel is closed."""
        try:
            self.logger.info("Cleaning up panel manager...")
            
            # Stop AI worker if running
            if self.ai_worker and self.ai_worker.isRunning():
                self.ai_worker.terminate()
                self.ai_worker.wait()
                
            # Save session if needed
            if self.session_manager:
                self.session_manager.save_session()
                
            # Clean up components
            if self.provider_manager:
                self.provider_manager.cleanup()
                
            self.logger.info("Panel manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")