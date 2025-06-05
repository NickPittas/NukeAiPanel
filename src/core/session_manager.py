"""
Session Manager

Manages chat sessions, context, and AI interactions for the Nuke AI Panel.
Handles conversation history, context persistence, and session state.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from PySide6.QtCore import QObject, Signal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    # Create minimal fallback classes for testing
    class QObject:
        def __init__(self, parent=None): pass
    
    Signal = lambda *args: type('Signal', (), {
        'emit': lambda *args: None,
        'connect': lambda callback: None
    })()

from nuke_ai_panel.utils.logger import setup_logging


class ChatSession:
    """Represents a single chat session with history and context."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or self.generate_session_id()
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.messages: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def add_message(self, message: str, is_user: bool, metadata: Optional[Dict] = None):
        """Add a message to the session."""
        message_data = {
            'message': message,
            'is_user': is_user,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.messages.append(message_data)
        self.last_updated = datetime.now()
        
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in the session."""
        return self.messages.copy()
        
    def get_context_summary(self) -> str:
        """Get a summary of the session context."""
        if not self.messages:
            return "No conversation history"
            
        user_messages = [msg for msg in self.messages if msg['is_user']]
        ai_messages = [msg for msg in self.messages if not msg['is_user']]
        
        summary = f"Session: {self.session_id}\n"
        summary += f"Messages: {len(user_messages)} user, {len(ai_messages)} AI\n"
        summary += f"Started: {self.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        summary += f"Last updated: {self.last_updated.strftime('%Y-%m-%d %H:%M')}"
        
        return summary
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'messages': self.messages,
            'context': self.context,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        """Create session from dictionary."""
        session = cls(data['session_id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_updated = datetime.fromisoformat(data['last_updated'])
        session.messages = data.get('messages', [])
        session.context = data.get('context', {})
        session.metadata = data.get('metadata', {})
        return session


class SessionManager(QObject):
    """
    Manages chat sessions and conversation context.
    
    Handles session creation, persistence, context management,
    and conversation history for the AI panel.
    """
    
    # Signals
    session_updated = Signal()
    session_changed = Signal(str)  # session_id
    context_updated = Signal(dict)
    
    def __init__(self, panel_manager=None):
        super().__init__()
        self.logger = None
        self._setup_logger()
        self.panel_manager = panel_manager
        
        # Current session
        self.current_session: Optional[ChatSession] = None
        
        # Session storage
        self.sessions_dir = self.get_sessions_directory()
        self.ensure_sessions_directory()
        
        # Configuration
        self.max_sessions = 50
        self.max_messages_per_session = 1000
        self.auto_save = True
        
        # Initialize with new session
        self.create_new_session()
    
    def _setup_logger(self):
        """Set up logger with robust fallback mechanisms."""
        try:
            # Try to set up global logging first
            setup_logging()
            self.logger = logging.getLogger(__name__)
            
            # Ensure logger is properly configured
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
                
        except Exception as e:
            # Fallback: Create a basic logger if setup_logging fails
            try:
                self.logger = logging.getLogger(__name__)
                if not self.logger.handlers:
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
                    self.logger.setLevel(logging.INFO)
            except Exception as fallback_error:
                # Ultimate fallback: Create a minimal logger manually
                try:
                    self.logger = logging.getLogger('session_manager_fallback')
                    handler = logging.StreamHandler()
                    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
                    self.logger.addHandler(handler)
                    self.logger.setLevel(logging.INFO)
                except Exception:
                    # Absolute final fallback - create minimal logger without error logging
                    self.logger = logging.getLogger('emergency_session_logger')
                    try:
                        self.logger.addHandler(logging.StreamHandler())
                        self.logger.setLevel(logging.ERROR)
                    except Exception:
                        # If even this fails, create a mock logger
                        self.logger = type('MockLogger', (), {
                            'info': lambda msg: print(f"[SESSION_INFO] {msg}"),
                            'warning': lambda msg: print(f"[SESSION_WARNING] {msg}"),
                            'error': lambda msg: print(f"[SESSION_ERROR] {msg}"),
                            'debug': lambda msg: print(f"[SESSION_DEBUG] {msg}"),
                            'critical': lambda msg: print(f"[SESSION_CRITICAL] {msg}")
                        })()
        
        # Final safety check
        if self.logger is None:
            # Create absolute minimal mock logger
            self.logger = type('MockLogger', (), {
                'info': lambda msg: print(f"[SESSION_INFO] {msg}"),
                'warning': lambda msg: print(f"[SESSION_WARNING] {msg}"),
                'error': lambda msg: print(f"[SESSION_ERROR] {msg}"),
                'debug': lambda msg: print(f"[SESSION_DEBUG] {msg}"),
                'critical': lambda msg: print(f"[SESSION_CRITICAL] {msg}")
            })()
    
    def _safe_log(self, level, message):
        """Safely log a message with fallback to print if logger fails."""
        try:
            if self.logger:
                getattr(self.logger, level)(message)
            else:
                print(f"[SESSION_{level.upper()}] {message}")
        except Exception:
            print(f"[SESSION_{level.upper()}] {message}")
        
    def get_sessions_directory(self) -> str:
        """Get the directory for storing sessions."""
        try:
            # Try to use Nuke's user directory if available
            import nuke
            nuke_dir = os.path.expanduser("~/.nuke")
            sessions_dir = os.path.join(nuke_dir, "ai_panel_sessions")
        except ImportError:
            # Fallback to user home directory
            sessions_dir = os.path.expanduser("~/.nuke_ai_panel/sessions")
            
        return sessions_dir
        
    def ensure_sessions_directory(self):
        """Ensure the sessions directory exists."""
        try:
            os.makedirs(self.sessions_dir, exist_ok=True)
        except Exception as e:
            self._safe_log("error", f"Failed to create sessions directory: {e}")
            # Fallback to temp directory
            import tempfile
            self.sessions_dir = os.path.join(tempfile.gettempdir(), "nuke_ai_sessions")
            os.makedirs(self.sessions_dir, exist_ok=True)
            
    def create_new_session(self) -> str:
        """Create a new chat session."""
        try:
            # Save current session if it exists
            if self.current_session and self.auto_save:
                self.save_session()
                
            # Create new session
            self.current_session = ChatSession()
            
            # Add initial context
            self.update_nuke_context()
            
            self._safe_log("info", f"Created new session: {self.current_session.session_id}")
            self.session_changed.emit(self.current_session.session_id)
            
            return self.current_session.session_id
            
        except Exception as e:
            self._safe_log("error", f"Failed to create new session: {e}")
            raise
            
    def load_session(self, session_id: str) -> bool:
        """Load an existing session."""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                self._safe_log("warning", f"Session file not found: {session_file}")
                return False
                
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            # Save current session first
            if self.current_session and self.auto_save:
                self.save_session()
                
            # Load the requested session
            self.current_session = ChatSession.from_dict(session_data)
            
            self._safe_log("info", f"Loaded session: {session_id}")
            self.session_changed.emit(session_id)
            
            return True
            
        except Exception as e:
            self._safe_log("error", f"Failed to load session {session_id}: {e}")
            return False
            
    def save_session(self, session: Optional[ChatSession] = None) -> bool:
        """Save a session to disk."""
        try:
            target_session = session or self.current_session
            if not target_session:
                return False
                
            session_file = os.path.join(self.sessions_dir, f"{target_session.session_id}.json")
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(target_session.to_dict(), f, indent=2, ensure_ascii=False)
                
            self._safe_log("debug", f"Saved session: {target_session.session_id}")
            return True
            
        except Exception as e:
            self._safe_log("error", f"Failed to save session: {e}")
            return False
            
    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available sessions."""
        try:
            sessions = []
            
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith('.json'):
                    session_file = os.path.join(self.sessions_dir, filename)
                    
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                            
                        sessions.append({
                            'session_id': session_data['session_id'],
                            'created_at': session_data['created_at'],
                            'last_updated': session_data['last_updated'],
                            'message_count': len(session_data.get('messages', []))
                        })
                        
                    except Exception as e:
                        self._safe_log("warning", f"Failed to read session file {filename}: {e}")
                        
            # Sort by last updated (newest first)
            sessions.sort(key=lambda x: x['last_updated'], reverse=True)
            
            return sessions
            
        except Exception as e:
            self._safe_log("error", f"Failed to get available sessions: {e}")
            return []
            
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if os.path.exists(session_file):
                os.remove(session_file)
                self._safe_log("info", f"Deleted session: {session_id}")
                
                # If this was the current session, create a new one
                if self.current_session and self.current_session.session_id == session_id:
                    self.create_new_session()
                    
                return True
            else:
                self._safe_log("warning", f"Session file not found for deletion: {session_id}")
                return False
                
        except Exception as e:
            self._safe_log("error", f"Failed to delete session {session_id}: {e}")
            return False
            
    def add_user_message(self, message: str, metadata: Optional[Dict] = None):
        """Add a user message to the current session."""
        try:
            if not self.current_session:
                self.create_new_session()
                
            self.current_session.add_message(message, True, metadata)
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_session()
                
            self.session_updated.emit()
            
        except Exception as e:
            self._safe_log("error", f"Failed to add user message: {e}")
            
    def add_ai_message(self, message: str, metadata: Optional[Dict] = None):
        """Add an AI message to the current session."""
        try:
            if not self.current_session:
                self.create_new_session()
                
            self.current_session.add_message(message, False, metadata)
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_session()
                
            self.session_updated.emit()
            
        except Exception as e:
            self._safe_log("error", f"Failed to add AI message: {e}")
            
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the current session's message history."""
        try:
            if self.current_session:
                return self.current_session.get_messages()
            return []
        except Exception as e:
            self._safe_log("error", f"Failed to get history: {e}")
            return []
            
    def get_context(self) -> Dict[str, Any]:
        """Get the current session's context."""
        try:
            if self.current_session:
                return self.current_session.context.copy()
            return {}
        except Exception as e:
            self._safe_log("error", f"Failed to get context: {e}")
            return {}
            
    def update_context(self, context_data: Dict[str, Any]):
        """Update the current session's context."""
        try:
            if not self.current_session:
                self.create_new_session()
                
            self.current_session.context.update(context_data)
            self.current_session.last_updated = datetime.now()
            
            # Auto-save if enabled
            if self.auto_save:
                self.save_session()
                
            self.context_updated.emit(self.current_session.context)
            
        except Exception as e:
            self._safe_log("error", f"Failed to update context: {e}")
            
    def update_nuke_context(self):
        """Update context with current Nuke session information."""
        try:
            if not self.panel_manager:
                return
                
            nuke_context = self.panel_manager.get_nuke_context()
            if nuke_context:
                context_data = {
                    'nuke_context': nuke_context,
                    'context_updated_at': datetime.now().isoformat()
                }
                self.update_context(context_data)
                
        except Exception as e:
            self._safe_log("error", f"Failed to update Nuke context: {e}")
            
    def clear_session(self):
        """Clear the current session."""
        try:
            if self.current_session:
                self.current_session.messages.clear()
                self.current_session.context.clear()
                self.current_session.last_updated = datetime.now()
                
                # Auto-save if enabled
                if self.auto_save:
                    self.save_session()
                    
                self.session_updated.emit()
                
        except Exception as e:
            self._safe_log("error", f"Failed to clear session: {e}")
            
    def get_conversation_summary(self, max_messages: int = 10) -> str:
        """Get a summary of recent conversation for context."""
        try:
            if not self.current_session or not self.current_session.messages:
                return "No conversation history"
                
            recent_messages = self.current_session.messages[-max_messages:]
            
            summary = "Recent conversation:\n"
            for msg in recent_messages:
                sender = "User" if msg['is_user'] else "AI"
                message = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
                summary += f"{sender}: {message}\n"
                
            return summary
            
        except Exception as e:
            self._safe_log("error", f"Failed to get conversation summary: {e}")
            return "Error getting conversation summary"
            
    def cleanup_old_sessions(self):
        """Clean up old sessions to prevent storage bloat."""
        try:
            sessions = self.get_available_sessions()
            
            if len(sessions) > self.max_sessions:
                # Sort by last updated and remove oldest
                sessions_to_delete = sessions[self.max_sessions:]
                
                for session_info in sessions_to_delete:
                    self.delete_session(session_info['session_id'])
                    
                self._safe_log("info", f"Cleaned up {len(sessions_to_delete)} old sessions")
                
        except Exception as e:
            self._safe_log("error", f"Failed to cleanup old sessions: {e}")
            
    def export_session(self, session_id: str, filename: str) -> bool:
        """Export a session to a file."""
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                return False
                
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            # Create readable export format
            export_data = {
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'session_id': session_id,
                    'created_at': session_data['created_at'],
                    'last_updated': session_data['last_updated']
                },
                'conversation': []
            }
            
            for msg in session_data.get('messages', []):
                export_data['conversation'].append({
                    'timestamp': msg['timestamp'],
                    'sender': 'User' if msg['is_user'] else 'AI Assistant',
                    'message': msg['message']
                })
                
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            self._safe_log("error", f"Failed to export session: {e}")
            return False
            
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self.current_session.session_id if self.current_session else None
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about the current session."""
        try:
            if not self.current_session:
                return {}
                
            messages = self.current_session.messages
            user_messages = [msg for msg in messages if msg['is_user']]
            ai_messages = [msg for msg in messages if not msg['is_user']]
            
            return {
                'session_id': self.current_session.session_id,
                'total_messages': len(messages),
                'user_messages': len(user_messages),
                'ai_messages': len(ai_messages),
                'created_at': self.current_session.created_at.isoformat(),
                'last_updated': self.current_session.last_updated.isoformat(),
                'duration_minutes': (datetime.now() - self.current_session.created_at).total_seconds() / 60
            }
            
        except Exception as e:
            self._safe_log("error", f"Failed to get session stats: {e}")
            return {}