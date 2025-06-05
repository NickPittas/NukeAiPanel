"""
Action Engine

Handles AI-suggested actions with preview and application capabilities.
Provides safe execution of AI-generated scripts and Nuke operations.
"""

import logging
import re
import ast
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

try:
    from PySide6.QtCore import QObject, Signal, QThread
except ImportError:
    from PySide2.QtCore import QObject, Signal, QThread

try:
    import nuke
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False

from ...nuke_ai_panel.utils.logger import setup_logger


class ActionType(Enum):
    """Types of actions that can be performed."""
    NODE_CREATION = "node_creation"
    NODE_MODIFICATION = "node_modification"
    NODE_CONNECTION = "node_connection"
    SCRIPT_EXECUTION = "script_execution"
    RENDER_OPERATION = "render_operation"
    FILE_OPERATION = "file_operation"
    UNKNOWN = "unknown"


class ActionSafety(Enum):
    """Safety levels for actions."""
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


class ActionAnalysis:
    """Analysis result for an AI-generated action."""
    
    def __init__(self):
        self.action_type = ActionType.UNKNOWN
        self.safety_level = ActionSafety.SAFE
        self.code_blocks: List[str] = []
        self.nuke_operations: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.estimated_runtime = "quick"
        self.affects_scene = False
        self.requires_confirmation = False
        self.description = ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            'action_type': self.action_type.value,
            'safety_level': self.safety_level.value,
            'code_blocks': self.code_blocks,
            'nuke_operations': self.nuke_operations,
            'warnings': self.warnings,
            'errors': self.errors,
            'estimated_runtime': self.estimated_runtime,
            'affects_scene': self.affects_scene,
            'requires_confirmation': self.requires_confirmation,
            'description': self.description
        }


class ActionExecutor(QThread):
    """Thread for executing actions safely without blocking UI."""
    
    execution_started = Signal()
    execution_progress = Signal(str)  # progress message
    execution_completed = Signal(dict)  # result data
    execution_failed = Signal(str)  # error message
    
    def __init__(self, code: str, context: Optional[Dict] = None):
        super().__init__()
        self.code = code
        self.context = context or {}
        self.logger = setup_logger(__name__)
        
    def run(self):
        """Execute the action code."""
        try:
            self.execution_started.emit()
            
            # Prepare execution environment
            exec_globals = self.prepare_execution_environment()
            
            # Execute code with progress tracking
            self.execution_progress.emit("Executing code...")
            
            # Capture stdout for logging
            import io
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                exec(self.code, exec_globals)
                output = captured_output.getvalue()
                
                result = {
                    'success': True,
                    'output': output,
                    'executed_at': datetime.now().isoformat()
                }
                
                self.execution_completed.emit(result)
                
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            self.execution_failed.emit(str(e))
            
    def prepare_execution_environment(self) -> Dict[str, Any]:
        """Prepare the execution environment with safe globals."""
        exec_globals = {
            '__builtins__': {
                # Safe built-ins only
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'print': print,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'round': round
            }
        }
        
        # Add Nuke if available
        if NUKE_AVAILABLE:
            exec_globals['nuke'] = nuke
            
        # Add context variables
        exec_globals.update(self.context)
        
        return exec_globals


class ActionEngine(QObject):
    """
    Engine for handling AI-suggested actions.
    
    Analyzes AI responses for actionable code, provides safety analysis,
    and handles safe execution of approved actions.
    """
    
    # Signals
    action_detected = Signal(dict)  # analysis data
    action_completed = Signal(str)  # success message
    action_failed = Signal(str)  # error message
    execution_progress = Signal(str)  # progress update
    
    def __init__(self, panel_manager=None):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.panel_manager = panel_manager
        
        # Execution tracking
        self.current_executor = None
        self.execution_history: List[Dict[str, Any]] = []
        
        # Safety patterns
        self.setup_safety_patterns()
        
    def setup_safety_patterns(self):
        """Set up patterns for safety analysis."""
        # Dangerous operations that should be blocked
        self.dangerous_patterns = [
            r'os\.system\(',
            r'subprocess\.',
            r'eval\(',
            r'exec\(',
            r'__import__\(',
            r'open\([^)]*["\']w["\']',  # File writing
            r'nuke\.scriptSave\(',
            r'nuke\.scriptSaveAs\(',
            r'nuke\.scriptClear\(',
            r'nuke\.scriptClose\(',
            r'import\s+os',
            r'import\s+subprocess',
            r'from\s+os\s+import',
            r'from\s+subprocess\s+import'
        ]
        
        # Operations requiring caution
        self.caution_patterns = [
            r'nuke\.render\(',
            r'nuke\.execute\(',
            r'nuke\.delete\(',
            r'nuke\.selectAll\(\)',
            r'\.removeKnob\(',
            r'nuke\.undo\(',
            r'nuke\.Undo\(',
            r'for.*nuke\.allNodes\(\)',
            r'while.*nuke\.'
        ]
        
        # Nuke operation patterns
        self.nuke_operation_patterns = {
            r'nuke\.createNode\(': 'Creates new nodes',
            r'nuke\.delete\(': 'Deletes nodes',
            r'\.setInput\(': 'Connects nodes',
            r'\.knob\(["\'][^"\']*["\']\)\.setValue\(': 'Sets knob values',
            r'nuke\.selectAll\(\)': 'Selects all nodes',
            r'nuke\.selectedNodes\(\)': 'Works with selected nodes',
            r'nuke\.allNodes\(\)': 'Works with all nodes',
            r'nuke\.render\(': 'Renders output',
            r'nuke\.execute\(': 'Executes nodes',
            r'\.setXYpos\(': 'Positions nodes',
            r'\.addKnob\(': 'Adds knobs to nodes',
            r'\.removeKnob\(': 'Removes knobs from nodes'
        }
        
    def analyze_response(self, response: str) -> Optional[ActionAnalysis]:
        """Analyze an AI response for actionable content."""
        try:
            analysis = ActionAnalysis()
            
            # Extract code blocks
            code_blocks = self.extract_code_blocks(response)
            if not code_blocks:
                return None
                
            analysis.code_blocks = code_blocks
            analysis.description = self.generate_action_description(response, code_blocks)
            
            # Analyze each code block
            for code in code_blocks:
                self.analyze_code_block(code, analysis)
                
            # Determine overall safety and requirements
            self.determine_safety_level(analysis)
            
            # Emit signal if actionable content found
            if analysis.code_blocks:
                self.action_detected.emit(analysis.to_dict())
                
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze response: {e}")
            return None
            
    def extract_code_blocks(self, text: str) -> List[str]:
        """Extract Python code blocks from text."""
        code_blocks = []
        
        # Look for code blocks with ```python or ```
        code_pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        for match in matches:
            code = match.strip()
            if code and ('nuke' in code or 'import' in code or 'def ' in code):
                code_blocks.append(code)
                
        # Look for inline code with nuke references
        if not code_blocks:
            lines = text.split('\n')
            inline_code = []
            
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in ['nuke.', 'import nuke', 'def ', 'class ']):
                    inline_code.append(line)
                    
            if inline_code:
                code_blocks.append('\n'.join(inline_code))
                
        return code_blocks
        
    def analyze_code_block(self, code: str, analysis: ActionAnalysis):
        """Analyze a single code block."""
        try:
            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    analysis.warnings.append(f"Potentially dangerous operation: {pattern}")
                    if analysis.safety_level.value < ActionSafety.DANGEROUS.value:
                        analysis.safety_level = ActionSafety.DANGEROUS
                        
            # Check for caution patterns
            for pattern in self.caution_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    analysis.warnings.append(f"Operation requires caution: {pattern}")
                    if analysis.safety_level == ActionSafety.SAFE:
                        analysis.safety_level = ActionSafety.CAUTION
                        
            # Identify Nuke operations
            for pattern, description in self.nuke_operation_patterns.items():
                if re.search(pattern, code, re.IGNORECASE):
                    if description not in analysis.nuke_operations:
                        analysis.nuke_operations.append(description)
                        analysis.affects_scene = True
                        
            # Determine action type
            if 'createNode' in code:
                analysis.action_type = ActionType.NODE_CREATION
            elif 'delete' in code:
                analysis.action_type = ActionType.NODE_MODIFICATION
            elif 'setInput' in code:
                analysis.action_type = ActionType.NODE_CONNECTION
            elif 'render' in code:
                analysis.action_type = ActionType.RENDER_OPERATION
            else:
                analysis.action_type = ActionType.SCRIPT_EXECUTION
                
            # Estimate runtime
            if any(keyword in code.lower() for keyword in ['for ', 'while ', 'allNodes()']):
                analysis.estimated_runtime = "medium"
                
            if 'render' in code.lower() or 'execute' in code.lower():
                analysis.estimated_runtime = "long"
                
            # Check syntax
            try:
                ast.parse(code)
            except SyntaxError as e:
                analysis.errors.append(f"Syntax error: {e}")
                analysis.safety_level = ActionSafety.BLOCKED
                
        except Exception as e:
            self.logger.error(f"Code block analysis failed: {e}")
            analysis.errors.append(f"Analysis failed: {e}")
            
    def determine_safety_level(self, analysis: ActionAnalysis):
        """Determine the overall safety level and requirements."""
        # Block if there are syntax errors
        if analysis.errors:
            analysis.safety_level = ActionSafety.BLOCKED
            return
            
        # Require confirmation for dangerous or scene-affecting operations
        if (analysis.safety_level in [ActionSafety.DANGEROUS, ActionSafety.CAUTION] or 
            analysis.affects_scene or 
            analysis.estimated_runtime in ["medium", "long"]):
            analysis.requires_confirmation = True
            
    def generate_action_description(self, response: str, code_blocks: List[str]) -> str:
        """Generate a human-readable description of the action."""
        try:
            # Extract description from response text
            lines = response.split('\n')
            description_lines = []
            
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.startswith('```') and 
                    not line.startswith('#') and
                    'nuke.' not in line and
                    len(line) > 10):
                    description_lines.append(line)
                    if len(description_lines) >= 3:  # Limit description length
                        break
                        
            if description_lines:
                return ' '.join(description_lines)
            else:
                return f"Execute {len(code_blocks)} code block(s)"
                
        except Exception as e:
            self.logger.error(f"Failed to generate description: {e}")
            return "Execute AI-generated code"
            
    def execute_action(self, code: str, context: Optional[Dict] = None, dry_run: bool = False) -> bool:
        """Execute an action with the given code."""
        try:
            if dry_run:
                return self.dry_run_action(code, context)
                
            # Clean up previous executor
            if self.current_executor and self.current_executor.isRunning():
                self.current_executor.terminate()
                self.current_executor.wait()
                
            # Create new executor
            self.current_executor = ActionExecutor(code, context)
            
            # Connect signals
            self.current_executor.execution_started.connect(
                lambda: self.execution_progress.emit("Starting execution...")
            )
            self.current_executor.execution_progress.connect(self.execution_progress.emit)
            self.current_executor.execution_completed.connect(self.handle_execution_success)
            self.current_executor.execution_failed.connect(self.handle_execution_failure)
            
            # Start execution
            self.current_executor.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute action: {e}")
            self.action_failed.emit(f"Execution failed: {e}")
            return False
            
    def dry_run_action(self, code: str, context: Optional[Dict] = None) -> bool:
        """Perform a dry run of the action without executing it."""
        try:
            self.execution_progress.emit("Performing dry run...")
            
            # Syntax check
            try:
                ast.parse(code)
                self.execution_progress.emit("✓ Syntax check passed")
            except SyntaxError as e:
                self.execution_progress.emit(f"✗ Syntax error: {e}")
                return False
                
            # Environment check
            if NUKE_AVAILABLE:
                self.execution_progress.emit("✓ Nuke environment available")
            else:
                self.execution_progress.emit("⚠ Nuke environment not available")
                
            # Analyze operations
            analysis = ActionAnalysis()
            self.analyze_code_block(code, analysis)
            
            if analysis.nuke_operations:
                self.execution_progress.emit("Operations that would be performed:")
                for operation in analysis.nuke_operations:
                    self.execution_progress.emit(f"  • {operation}")
                    
            self.execution_progress.emit("Dry run completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Dry run failed: {e}")
            self.execution_progress.emit(f"Dry run failed: {e}")
            return False
            
    def handle_execution_success(self, result: Dict[str, Any]):
        """Handle successful action execution."""
        try:
            # Add to execution history
            history_entry = {
                'timestamp': result['executed_at'],
                'success': True,
                'output': result.get('output', ''),
                'code_preview': self.current_executor.code[:100] + "..." if len(self.current_executor.code) > 100 else self.current_executor.code
            }
            
            self.execution_history.append(history_entry)
            
            # Emit success signal
            output = result.get('output', '')
            message = f"Action executed successfully"
            if output:
                message += f"\nOutput: {output}"
                
            self.action_completed.emit(message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle execution success: {e}")
            
    def handle_execution_failure(self, error_message: str):
        """Handle failed action execution."""
        try:
            # Add to execution history
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': error_message,
                'code_preview': self.current_executor.code[:100] + "..." if len(self.current_executor.code) > 100 else self.current_executor.code
            }
            
            self.execution_history.append(history_entry)
            
            # Emit failure signal
            self.action_failed.emit(error_message)
            
        except Exception as e:
            self.logger.error(f"Failed to handle execution failure: {e}")
            
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history."""
        return self.execution_history.copy()
        
    def clear_execution_history(self):
        """Clear the execution history."""
        self.execution_history.clear()
        
    def is_code_safe(self, code: str) -> Tuple[bool, List[str]]:
        """Check if code is safe to execute."""
        warnings = []
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                warnings.append(f"Dangerous operation detected: {pattern}")
                
        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            warnings.append(f"Syntax error: {e}")
            
        is_safe = len(warnings) == 0
        return is_safe, warnings
        
    def get_action_preview(self, code: str) -> Dict[str, Any]:
        """Get a preview of what an action would do."""
        try:
            analysis = ActionAnalysis()
            self.analyze_code_block(code, analysis)
            
            preview = {
                'description': self.generate_action_description("", [code]),
                'operations': analysis.nuke_operations,
                'safety_level': analysis.safety_level.value,
                'warnings': analysis.warnings,
                'errors': analysis.errors,
                'affects_scene': analysis.affects_scene,
                'estimated_runtime': analysis.estimated_runtime
            }
            
            return preview
            
        except Exception as e:
            self.logger.error(f"Failed to get action preview: {e}")
            return {'error': str(e)}
            
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.current_executor and self.current_executor.isRunning():
                self.current_executor.terminate()
                self.current_executor.wait()
                
        except Exception as e:
            self.logger.error(f"Error during action engine cleanup: {e}")