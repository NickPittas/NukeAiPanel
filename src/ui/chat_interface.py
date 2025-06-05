"""
Chat Interface Component

This module implements the chat UI components including message history,
input field, action buttons, and real-time interaction features.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

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
        def setup_ui(self): pass
        def setup_connections(self): pass
    
    class QVBoxLayout:
        def __init__(self, parent=None): pass
        def setContentsMargins(self, *args): pass
        def setSpacing(self, spacing): pass
        def addWidget(self, widget, stretch=0): pass
        def addLayout(self, layout): pass
        def insertWidget(self, index, widget): pass
        def count(self): return 1
    
    class QHBoxLayout:
        def __init__(self): pass
        def setContentsMargins(self, *args): pass
        def addWidget(self, widget): pass
        def addStretch(self): pass
        def addLayout(self, layout): pass
    
    class QLabel:
        def __init__(self, text=""): pass
        def setStyleSheet(self, style): pass
        def setText(self, text): pass
        def setWordWrap(self, wrap): pass
        def setTextInteractionFlags(self, flags): pass
    
    class QScrollArea:
        def __init__(self): pass
        def setWidgetResizable(self, resizable): pass
        def setHorizontalScrollBarPolicy(self, policy): pass
        def setVerticalScrollBarPolicy(self, policy): pass
        def setStyleSheet(self, style): pass
        def setWidget(self, widget): pass
        def verticalScrollBar(self): return self
        def setValue(self, value): pass
        def maximum(self): return 100
    
    class QTextEdit:
        def __init__(self): pass
        def setMaximumHeight(self, height): pass
        def setPlaceholderText(self, text): pass
        def setStyleSheet(self, style): pass
        def toPlainText(self): return ""
        def clear(self): pass
        def setPlainText(self, text): pass
        def textCursor(self): return self
        def setTextCursor(self, cursor): pass
        def installEventFilter(self, filter): pass
        def setReadOnly(self, readonly): pass
        def append(self, text): pass
        def verticalScrollBar(self): return self
        textChanged = None
    
    class QPushButton:
        def __init__(self, text=""): pass
        def setFixedHeight(self, height): pass
        def setFixedWidth(self, width): pass
        def setDefault(self, default): pass
        def setStyleSheet(self, style): pass
        def setEnabled(self, enabled): pass
        def setToolTip(self, tip): pass
        clicked = None
    
    class QTimer:
        def __init__(self): pass
        def start(self, interval): pass
        def stop(self): pass
        def singleShot(interval, callback): pass
        timeout = None
    
    class QApplication:
        @staticmethod
        def clipboard(): return type('Clipboard', (), {'setText': lambda text: None})()
    
    class QDialog:
        def __init__(self, parent=None): pass
        def setWindowTitle(self, title): pass
        def setModal(self, modal): pass
        def resize(self, w, h): pass
        def exec_(self): return 0
        def accept(self): pass
        def reject(self): pass
    
    class QListWidget:
        def __init__(self): pass
        def addItem(self, item): pass
        def currentItem(self): return None
    
    class QListWidgetItem:
        def __init__(self, text): pass
        def setToolTip(self, tip): pass
        def setData(self, role, data): pass
        def data(self, role): return None
    
    class QTextCursor:
        End = 1
        def movePosition(self, operation): pass
    
    class QEvent:
        KeyPress = 1
    
    class Qt:
        TextSelectableByMouse = 1
        ScrollBarAlwaysOff = 1
        ScrollBarAsNeeded = 1
        Key_Return = 1
        Key_Enter = 2
        ControlModifier = 1
        NoModifier = 0
        UserRole = 1
    
    Signal = lambda *args: None

from .action_preview import ActionPreviewDialog


class MessageWidget(QWidget):
    """Individual message widget for the chat interface."""
    
    def __init__(self, message: str, is_user: bool, timestamp: datetime, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.timestamp = timestamp
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the message widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Header with sender and timestamp
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        sender_label = QLabel("You" if self.is_user else "AI Assistant")
        sender_label.setStyleSheet(f"""
            font-weight: bold;
            color: {'#4CAF50' if self.is_user else '#2196F3'};
            font-size: 11px;
        """)
        header_layout.addWidget(sender_label)
        
        header_layout.addStretch()
        
        time_label = QLabel(self.timestamp.strftime("%H:%M"))
        time_label.setStyleSheet("color: #808080; font-size: 10px;")
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Message content
        self.content_label = QLabel(self.message)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.content_label.setStyleSheet(f"""
            background-color: {'#2E4A2E' if self.is_user else '#2E3A4A'};
            border: 1px solid {'#4CAF50' if self.is_user else '#2196F3'};
            border-radius: 6px;
            padding: 8px;
            color: #E0E0E0;
            font-size: 11px;
            line-height: 1.4;
        """)
        layout.addWidget(self.content_label)
        
        # Action buttons for AI messages
        if not self.is_user and self.has_actions():
            self.add_action_buttons(layout)
            
    def has_actions(self) -> bool:
        """Check if the message contains actionable content."""
        action_keywords = [
            "```python", "nuke.", "import nuke", 
            "create node", "add node", "script:",
            "def ", "class ", "function"
        ]
        return any(keyword in self.message.lower() for keyword in action_keywords)
        
    def add_action_buttons(self, layout: QVBoxLayout):
        """Add action buttons for AI messages with code."""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 4, 0, 0)
        
        # Preview action button
        preview_btn = QPushButton("Preview Action")
        preview_btn.setFixedHeight(24)
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #2196F3;
                border-radius: 3px;
                color: #2196F3;
                font-size: 10px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #2196F3;
                color: white;
            }
        """)
        preview_btn.clicked.connect(self.preview_action)
        button_layout.addWidget(preview_btn)
        
        # Copy code button
        copy_btn = QPushButton("Copy Code")
        copy_btn.setFixedHeight(24)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #5A5A5A;
                border-radius: 3px;
                color: #B0B0B0;
                font-size: 10px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
        """)
        copy_btn.clicked.connect(self.copy_code)
        button_layout.addWidget(copy_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def preview_action(self):
        """Preview the action in the message."""
        try:
            # Extract code from message
            code = self.extract_code()
            if code:
                dialog = ActionPreviewDialog(code, self)
                dialog.exec_()
        except Exception as e:
            logging.error(f"Failed to preview action: {e}")
            
    def copy_code(self):
        """Copy code from the message to clipboard."""
        try:
            code = self.extract_code()
            if code:
                clipboard = QApplication.clipboard()
                clipboard.setText(code)
                
                # Show temporary feedback
                self.show_copy_feedback()
        except Exception as e:
            logging.error(f"Failed to copy code: {e}")
            
    def extract_code(self) -> str:
        """Extract Python code from the message."""
        import re
        
        # Look for code blocks
        code_pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(code_pattern, self.message, re.DOTALL)
        
        if matches:
            return matches[0].strip()
            
        # Look for inline code with nuke references
        lines = self.message.split('\n')
        code_lines = []
        
        for line in lines:
            if any(keyword in line for keyword in ['nuke.', 'import nuke', 'def ', 'class ']):
                code_lines.append(line.strip())
                
        return '\n'.join(code_lines) if code_lines else ""
        
    def show_copy_feedback(self):
        """Show temporary feedback for copy action."""
        # Create a temporary tooltip-like feedback
        try:
            # Find the copy button
            for child in self.children():
                if isinstance(child, QWidget):
                    for button in child.findChildren(QPushButton):
                        if button.text() == "Copy Code":
                            # Store original style
                            original_style = button.styleSheet()
                            
                            # Change to success style
                            button.setText("Copied!")
                            button.setStyleSheet("""
                                QPushButton {
                                    background-color: #4CAF50;
                                    border: 1px solid #45A049;
                                    border-radius: 3px;
                                    color: white;
                                    font-size: 10px;
                                    padding: 2px 8px;
                                }
                            """)
                            
                            # Reset after 1.5 seconds
                            QTimer.singleShot(1500, lambda: self.reset_copy_button(button, original_style))
                            return
        except Exception as e:
            logging.error(f"Failed to show copy feedback: {e}")
    
    def reset_copy_button(self, button, original_style):
        """Reset the copy button to its original state."""
        button.setText("Copy Code")
        button.setStyleSheet(original_style)


class TypingIndicator(QWidget):
    """Typing indicator widget to show when AI is responding."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dots)
        self.dot_count = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the typing indicator UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.label = QLabel("AI is typing")
        self.label.setStyleSheet("""
            color: #808080;
            font-style: italic;
            font-size: 11px;
        """)
        layout.addWidget(self.label)
        layout.addStretch()
        
    def start_animation(self):
        """Start the typing animation."""
        self.timer.start(500)  # Update every 500ms
        self.show()
        
    def stop_animation(self):
        """Stop the typing animation."""
        self.timer.stop()
        self.hide()
        
    def update_dots(self):
        """Update the typing dots animation."""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.label.setText(f"AI is typing{dots}")


class ChatInterface(QWidget):
    """
    Main chat interface widget.
    
    Provides message history, input field, and interaction controls
    for the AI chat functionality.
    """
    
    # Signals
    message_sent = Signal(str)
    action_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.panel_manager = None
        self.messages: List[Dict[str, Any]] = []
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Set up the chat interface UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Message history area
        self.create_message_area(layout)
        
        # Input area
        self.create_input_area(layout)
        
    def create_message_area(self, parent_layout: QVBoxLayout):
        """Create the message history area."""
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                background-color: #2A2A2A;
            }
            QScrollBar:vertical {
                background-color: #3A3A3A;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #5A5A5A;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6A6A6A;
            }
        """)
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()  # Push messages to top
        
        self.scroll_area.setWidget(self.messages_widget)
        parent_layout.addWidget(self.scroll_area, 1)  # Stretch factor 1
        
        # Typing indicator
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()
        parent_layout.addWidget(self.typing_indicator)
        
    def create_input_area(self, parent_layout: QVBoxLayout):
        """Create the input area with text field and buttons."""
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(4)
        
        # Text input
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(80)
        self.input_text.setPlaceholderText("Ask about VFX, compositing, or request Nuke scripts...")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #3A3A3A;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 11px;
            }
            QTextEdit:focus {
                border-color: #2196F3;
            }
        """)
        input_layout.addWidget(self.input_text)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Context buttons
        self.context_btn = QPushButton("Add Context")
        self.context_btn.setFixedHeight(28)
        self.context_btn.setToolTip("Add current Nuke session context")
        button_layout.addWidget(self.context_btn)
        
        self.workflow_btn = QPushButton("Workflows")
        self.workflow_btn.setFixedHeight(28)
        self.workflow_btn.setToolTip("Browse VFX workflows")
        button_layout.addWidget(self.workflow_btn)
        
        button_layout.addStretch()
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedHeight(28)
        self.send_btn.setFixedWidth(60)
        self.send_btn.setDefault(True)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                border: 1px solid #1976D2;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #4A4A4A;
                border-color: #5A5A5A;
                color: #808080;
            }
        """)
        button_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(button_layout)
        parent_layout.addWidget(input_widget)
        
    def setup_connections(self):
        """Set up signal connections."""
        self.send_btn.clicked.connect(self.send_message)
        self.input_text.textChanged.connect(self.on_text_changed)
        self.context_btn.clicked.connect(self.add_context)
        self.workflow_btn.clicked.connect(self.show_workflows)
        
        # Handle Enter key
        self.input_text.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """Handle keyboard events for the input field."""
        if obj == self.input_text and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() == Qt.ControlModifier:
                    # Ctrl+Enter sends message
                    self.send_message()
                    return True
                elif event.modifiers() == Qt.NoModifier:
                    # Plain Enter adds new line (default behavior)
                    return False
                    
        return super().eventFilter(obj, event)
        
    def set_panel_manager(self, panel_manager):
        """Set the panel manager for AI interactions."""
        self.panel_manager = panel_manager
        
        if panel_manager:
            # Connect to panel manager signals
            panel_manager.response_received.connect(self.add_ai_message)
            panel_manager.response_started.connect(self.show_typing)
            panel_manager.response_finished.connect(self.hide_typing)
            
    def send_message(self):
        """Send the current message."""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
            
        try:
            # Add user message to chat
            self.add_user_message(message)
            
            # Clear input
            self.input_text.clear()
            
            # Send to AI if panel manager is available
            if self.panel_manager:
                self.panel_manager.send_message(message)
            else:
                self.add_ai_message("Panel manager not available. Please check configuration.")
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            self.add_ai_message(f"Error sending message: {e}")
            
    def add_user_message(self, message: str):
        """Add a user message to the chat."""
        self.add_message(message, is_user=True)
        
    def add_ai_message(self, message: str):
        """Add an AI message to the chat."""
        self.add_message(message, is_user=False)
        
    def add_message(self, message: str, is_user: bool):
        """Add a message to the chat interface."""
        timestamp = datetime.now()
        
        # Create message widget
        message_widget = MessageWidget(message, is_user, timestamp, self)
        
        # Insert before the stretch
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, message_widget)
        
        # Store message data
        self.messages.append({
            'message': message,
            'is_user': is_user,
            'timestamp': timestamp,
            'widget': message_widget
        })
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        """Scroll the message area to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def show_typing(self):
        """Show typing indicator."""
        self.typing_indicator.start_animation()
        
    def hide_typing(self):
        """Hide typing indicator."""
        self.typing_indicator.stop_animation()
        
    def on_text_changed(self):
        """Handle text input changes."""
        has_text = bool(self.input_text.toPlainText().strip())
        self.send_btn.setEnabled(has_text)
        
    def add_context(self):
        """Add current Nuke session context to the message."""
        if not self.panel_manager:
            return
            
        try:
            context = self.panel_manager.get_nuke_context()
            if context:
                current_text = self.input_text.toPlainText()
                if current_text:
                    current_text += "\n\n"
                    
                current_text += f"Current Nuke Context:\n{context}"
                self.input_text.setPlainText(current_text)
                
                # Move cursor to end
                cursor = self.input_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.input_text.setTextCursor(cursor)
                
        except Exception as e:
            self.logger.error(f"Failed to add context: {e}")
            
    def show_workflows(self):
        """Show available VFX workflows."""
        if not self.panel_manager:
            return
            
        try:
            workflows = self.panel_manager.get_available_workflows()
            
            # Create workflow selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("VFX Workflows")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Workflow list
            workflow_list = QListWidget()
            for workflow in workflows:
                item = QListWidgetItem(workflow.name)
                item.setToolTip(workflow.description)
                item.setData(Qt.UserRole, workflow)
                workflow_list.addItem(item)
                
            layout.addWidget(workflow_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            use_btn = QPushButton("Use Workflow")
            use_btn.clicked.connect(lambda: self.use_workflow(workflow_list, dialog))
            button_layout.addWidget(use_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            self.logger.error(f"Failed to show workflows: {e}")
            
    def use_workflow(self, workflow_list: QListWidget, dialog: QDialog):
        """Use the selected workflow."""
        current_item = workflow_list.currentItem()
        if not current_item:
            return
            
        workflow = current_item.data(Qt.UserRole)
        
        # Add workflow prompt to input
        prompt = f"Please help me with the {workflow.name} workflow."
        prompt += f" {workflow.description}"
            
        self.input_text.setPlainText(prompt)
        dialog.accept()
        
    def clear_history(self):
        """Clear the chat history."""
        # Remove all message widgets
        for message_data in self.messages:
            widget = message_data['widget']
            self.messages_layout.removeWidget(widget)
            widget.deleteLater()
            
        self.messages.clear()
        
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the chat history."""
        return [
            {
                'message': msg['message'],
                'is_user': msg['is_user'],
                'timestamp': msg['timestamp'].isoformat()
            }
            for msg in self.messages
        ]