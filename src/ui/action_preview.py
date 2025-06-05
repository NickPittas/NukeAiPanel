"""
Action Preview Dialog Component

This module implements the preview and apply UI for AI-suggested actions
with validation and safe execution capabilities.
"""

import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

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
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False


class CodeHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code in the preview."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()
        
    def setup_highlighting_rules(self):
        """Set up syntax highlighting rules for Python code."""
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            "\\bdef\\b", "\\bclass\\b", "\\bif\\b", "\\belse\\b", "\\belif\\b",
            "\\bfor\\b", "\\bwhile\\b", "\\btry\\b", "\\bexcept\\b", "\\bfinally\\b",
            "\\bimport\\b", "\\bfrom\\b", "\\breturn\\b", "\\byield\\b", "\\bwith\\b",
            "\\bas\\b", "\\bin\\b", "\\bis\\b", "\\bnot\\b", "\\band\\b", "\\bor\\b"
        ]
        
        for pattern in keywords:
            self.highlighting_rules.append((QRegExp(pattern), keyword_format))
            
        # Nuke-specific keywords
        nuke_format = QTextCharFormat()
        nuke_format.setForeground(QColor("#4EC9B0"))
        nuke_format.setFontWeight(QFont.Bold)
        
        nuke_patterns = [
            "\\bnuke\\.", "\\bNode\\b", "\\bKnob\\b", "\\bRoot\\b"
        ]
        
        for pattern in nuke_patterns:
            self.highlighting_rules.append((QRegExp(pattern), nuke_format))
            
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("'.*'"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp("#[^\n]*"), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\.?[0-9]*\\b"), number_format))
        
    def highlightBlock(self, text):
        """Apply highlighting to a block of text."""
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class ActionAnalyzer:
    """Analyzes AI-generated code for safety and functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyze the provided code and return safety/functionality info."""
        analysis = {
            'is_safe': True,
            'warnings': [],
            'errors': [],
            'actions': [],
            'nuke_operations': [],
            'estimated_runtime': 'Quick',
            'affects_scene': False
        }
        
        try:
            # Check for dangerous operations
            dangerous_patterns = [
                r'os\.system\(',
                r'subprocess\.',
                r'eval\(',
                r'exec\(',
                r'__import__\(',
                r'open\([^)]*["\']w["\']',  # File writing
                r'nuke\.scriptSave\(',
                r'nuke\.scriptSaveAs\(',
                r'nuke\.scriptClear\('
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    analysis['is_safe'] = False
                    analysis['warnings'].append(f"Potentially dangerous operation detected: {pattern}")
                    
            # Identify Nuke operations
            nuke_patterns = {
                r'nuke\.createNode\(': 'Creates new nodes',
                r'nuke\.delete\(': 'Deletes nodes',
                r'\.setInput\(': 'Connects nodes',
                r'\.knob\(["\'][^"\']*["\']\)\.setValue\(': 'Sets knob values',
                r'nuke\.selectAll\(\)': 'Selects all nodes',
                r'nuke\.selectedNodes\(\)': 'Works with selected nodes',
                r'nuke\.allNodes\(\)': 'Works with all nodes',
                r'nuke\.render\(': 'Renders output'
            }
            
            for pattern, description in nuke_patterns.items():
                if re.search(pattern, code, re.IGNORECASE):
                    analysis['nuke_operations'].append(description)
                    analysis['affects_scene'] = True
                    
            # Estimate runtime complexity
            if any(keyword in code.lower() for keyword in ['for ', 'while ', 'render']):
                analysis['estimated_runtime'] = 'Medium'
                
            if 'render' in code.lower() or 'allNodes()' in code:
                analysis['estimated_runtime'] = 'Long'
                
            # Check for syntax errors (basic check)
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                analysis['errors'].append(f"Syntax error: {e}")
                analysis['is_safe'] = False
                
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            analysis['errors'].append(f"Analysis failed: {e}")
            
        return analysis


class ActionPreviewDialog(QDialog):
    """
    Dialog for previewing and applying AI-suggested actions.
    
    Provides code preview, safety analysis, and controlled execution
    of AI-generated Nuke scripts and actions.
    """
    
    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.code = code
        self.analyzer = ActionAnalyzer()
        self.analysis = None
        
        self.setup_ui()
        self.analyze_code()
        
    def setup_ui(self):
        """Set up the action preview dialog UI."""
        self.setWindowTitle("Action Preview")
        self.setModal(True)
        self.resize(700, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("AI-Generated Action Preview")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Safety indicator
        self.safety_indicator = QLabel("●")
        self.safety_indicator.setStyleSheet("color: #808080; font-size: 16px;")
        header_layout.addWidget(self.safety_indicator)
        
        layout.addLayout(header_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Code preview tab
        self.create_code_tab()
        
        # Analysis tab
        self.create_analysis_tab()
        
        # Execution log tab
        self.create_log_tab()
        
        # Action buttons
        self.create_action_buttons(layout)
        
        # Apply styling
        self.apply_styling()
        
    def create_code_tab(self):
        """Create the code preview tab."""
        code_widget = QWidget()
        layout = QVBoxLayout(code_widget)
        
        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setPlainText(self.code)
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        
        # Apply syntax highlighting
        self.highlighter = CodeHighlighter(self.code_editor.document())
        
        layout.addWidget(self.code_editor)
        
        # Code actions
        code_actions_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit Code")
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        code_actions_layout.addWidget(self.edit_btn)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_code)
        code_actions_layout.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("Save to File")
        self.save_btn.clicked.connect(self.save_code)
        code_actions_layout.addWidget(self.save_btn)
        
        code_actions_layout.addStretch()
        layout.addLayout(code_actions_layout)
        
        self.tab_widget.addTab(code_widget, "Code")
        
    def create_analysis_tab(self):
        """Create the code analysis tab."""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        
        # Analysis results
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("""
            QTextEdit {
                background-color: #2A2A2A;
                color: #E0E0E0;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.analysis_text)
        
        self.tab_widget.addTab(analysis_widget, "Analysis")
        
    def create_log_tab(self):
        """Create the execution log tab."""
        log_widget = QWidget()
        layout = QVBoxLayout(log_widget)
        
        # Execution log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A1A;
                color: #C0C0C0;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(self.clear_log_btn)
        
        log_controls.addStretch()
        layout.addLayout(log_controls)
        
        self.tab_widget.addTab(log_widget, "Execution Log")
        
    def create_action_buttons(self, parent_layout: QVBoxLayout):
        """Create the main action buttons."""
        button_layout = QHBoxLayout()
        
        # Dry run button
        self.dry_run_btn = QPushButton("Dry Run")
        self.dry_run_btn.setToolTip("Test the code without making changes")
        self.dry_run_btn.clicked.connect(self.dry_run)
        button_layout.addWidget(self.dry_run_btn)
        
        # Apply button
        self.apply_btn = QPushButton("Apply Action")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: 1px solid #45A049;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #3D8B40;
            }
            QPushButton:disabled {
                background-color: #4A4A4A;
                border-color: #5A5A5A;
                color: #808080;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_action)
        button_layout.addWidget(self.apply_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        parent_layout.addLayout(button_layout)
        
    def apply_styling(self):
        """Apply dialog styling."""
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #5A5A5A;
                border-radius: 4px;
                color: #E0E0E0;
                padding: 6px 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
                border-color: #6A6A6A;
            }
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
        """)
        
    def analyze_code(self):
        """Analyze the code and update the UI."""
        try:
            self.analysis = self.analyzer.analyze_code(self.code)
            self.update_analysis_display()
            self.update_safety_indicator()
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            self.log_message(f"Analysis failed: {e}", "error")
            
    def update_analysis_display(self):
        """Update the analysis tab with results."""
        if not self.analysis:
            return
            
        analysis_html = "<h3>Code Analysis Results</h3>"
        
        # Safety status
        safety_color = "#4CAF50" if self.analysis['is_safe'] else "#F44336"
        safety_text = "SAFE" if self.analysis['is_safe'] else "UNSAFE"
        analysis_html += f"<p><b>Safety Status:</b> <span style='color: {safety_color};'>{safety_text}</span></p>"
        
        # Warnings
        if self.analysis['warnings']:
            analysis_html += "<h4>Warnings:</h4><ul>"
            for warning in self.analysis['warnings']:
                analysis_html += f"<li style='color: #FF9800;'>{warning}</li>"
            analysis_html += "</ul>"
            
        # Errors
        if self.analysis['errors']:
            analysis_html += "<h4>Errors:</h4><ul>"
            for error in self.analysis['errors']:
                analysis_html += f"<li style='color: #F44336;'>{error}</li>"
            analysis_html += "</ul>"
            
        # Nuke operations
        if self.analysis['nuke_operations']:
            analysis_html += "<h4>Nuke Operations:</h4><ul>"
            for operation in self.analysis['nuke_operations']:
                analysis_html += f"<li style='color: #2196F3;'>{operation}</li>"
            analysis_html += "</ul>"
            
        # Runtime estimate
        runtime_color = {"Quick": "#4CAF50", "Medium": "#FF9800", "Long": "#F44336"}
        runtime = self.analysis['estimated_runtime']
        analysis_html += f"<p><b>Estimated Runtime:</b> <span style='color: {runtime_color.get(runtime, '#E0E0E0')};'>{runtime}</span></p>"
        
        # Scene impact
        impact_text = "Yes" if self.analysis['affects_scene'] else "No"
        impact_color = "#FF9800" if self.analysis['affects_scene'] else "#4CAF50"
        analysis_html += f"<p><b>Affects Scene:</b> <span style='color: {impact_color};'>{impact_text}</span></p>"
        
        self.analysis_text.setHtml(analysis_html)
        
    def update_safety_indicator(self):
        """Update the safety indicator in the header."""
        if not self.analysis:
            return
            
        if self.analysis['is_safe']:
            self.safety_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
            self.safety_indicator.setToolTip("Code appears safe to execute")
        else:
            self.safety_indicator.setStyleSheet("color: #F44336; font-size: 16px;")
            self.safety_indicator.setToolTip("Code may be unsafe - review warnings")
            
        # Disable apply button if unsafe
        self.apply_btn.setEnabled(self.analysis['is_safe'])
        
    def toggle_edit_mode(self):
        """Toggle between read-only and edit mode for code."""
        if self.code_editor.isReadOnly():
            self.code_editor.setReadOnly(False)
            self.edit_btn.setText("Lock Code")
            self.log_message("Code editing enabled", "info")
        else:
            self.code_editor.setReadOnly(True)
            self.edit_btn.setText("Edit Code")
            
            # Re-analyze if code was modified
            new_code = self.code_editor.toPlainText()
            if new_code != self.code:
                self.code = new_code
                self.analyze_code()
                self.log_message("Code modified - re-analyzing", "info")
                
    def copy_code(self):
        """Copy code to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code_editor.toPlainText())
        self.log_message("Code copied to clipboard", "info")
        
    def save_code(self):
        """Save code to a file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Code",
                f"nuke_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                "Python Files (*.py);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.code_editor.toPlainText())
                    
                self.log_message(f"Code saved to {filename}", "success")
                
        except Exception as e:
            self.logger.error(f"Failed to save code: {e}")
            self.log_message(f"Save failed: {e}", "error")
            
    def dry_run(self):
        """Perform a dry run of the code."""
        self.log_message("Starting dry run...", "info")
        
        try:
            # Switch to log tab
            self.tab_widget.setCurrentIndex(2)
            
            # For now, just validate syntax and show what would happen
            code = self.code_editor.toPlainText()
            
            # Syntax check
            try:
                compile(code, '<string>', 'exec')
                self.log_message("✓ Syntax check passed", "success")
            except SyntaxError as e:
                self.log_message(f"✗ Syntax error: {e}", "error")
                return
                
            # Simulate execution analysis
            if NUKE_AVAILABLE:
                self.log_message("✓ Nuke environment available", "success")
            else:
                self.log_message("⚠ Nuke environment not available", "warning")
                
            # Show what operations would be performed
            if self.analysis and self.analysis['nuke_operations']:
                self.log_message("Operations that would be performed:", "info")
                for operation in self.analysis['nuke_operations']:
                    self.log_message(f"  • {operation}", "info")
                    
            self.log_message("Dry run completed", "success")
            
        except Exception as e:
            self.logger.error(f"Dry run failed: {e}")
            self.log_message(f"Dry run failed: {e}", "error")
            
    def apply_action(self):
        """Apply the action by executing the code."""
        if not self.analysis or not self.analysis['is_safe']:
            QMessageBox.warning(self, "Unsafe Code", "Cannot execute unsafe code.")
            return
            
        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Apply Action",
            "Are you sure you want to execute this code?\n\n"
            "This will modify your Nuke scene.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        self.log_message("Executing code...", "info")
        
        try:
            # Switch to log tab
            self.tab_widget.setCurrentIndex(2)
            
            code = self.code_editor.toPlainText()
            
            if NUKE_AVAILABLE:
                # Execute in Nuke context
                exec(code, {'nuke': nuke})
                self.log_message("✓ Code executed successfully", "success")
                
                # Close dialog on success
                QTimer.singleShot(1000, self.accept)
                
            else:
                self.log_message("⚠ Nuke not available - code not executed", "warning")
                
        except Exception as e:
            self.logger.error(f"Code execution failed: {e}")
            self.log_message(f"✗ Execution failed: {e}", "error")
            
            QMessageBox.critical(
                self,
                "Execution Error",
                f"Code execution failed:\n\n{e}"
            )
            
    def log_message(self, message: str, level: str = "info"):
        """Add a message to the execution log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": "#C0C0C0",
            "success": "#4CAF50",
            "warning": "#FF9800", 
            "error": "#F44336"
        }
        
        color = colors.get(level, "#C0C0C0")
        
        # Add to log
        self.log_text.append(f"<span style='color: #808080;'>[{timestamp}]</span> "
                            f"<span style='color: {color};'>{message}</span>")
        
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """Clear the execution log."""
        self.log_text.clear()
        self.log_message("Log cleared", "info")