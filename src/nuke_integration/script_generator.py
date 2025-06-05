"""
Nuke Script Generator

Generates safe Nuke Python scripts from AI suggestions with validation,
error handling, and rollback capabilities.
"""

import logging
import re
import ast
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum

# Handle Nuke import gracefully
try:
    import nuke
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False
    nuke = None

logger = logging.getLogger(__name__)


class ScriptType(Enum):
    """Types of scripts that can be generated"""
    NODE_CREATION = "node_creation"
    NODE_MODIFICATION = "node_modification"
    CONNECTION_SETUP = "connection_setup"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    WORKFLOW_AUTOMATION = "workflow_automation"
    UTILITY = "utility"


class ValidationLevel(Enum):
    """Validation levels for script safety"""
    STRICT = "strict"      # Only allow safe, well-known operations
    MODERATE = "moderate"  # Allow most operations with validation
    PERMISSIVE = "permissive"  # Allow most operations with minimal validation


@dataclass
class ScriptValidationResult:
    """Result of script validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    risk_level: str


@dataclass
class GeneratedScript:
    """A generated Nuke script with metadata"""
    script_type: ScriptType
    code: str
    description: str
    validation_result: ScriptValidationResult
    estimated_execution_time: float
    dependencies: List[str]
    undo_script: Optional[str] = None


class NukeScriptGenerator:
    """
    Generates safe Nuke Python scripts from AI suggestions with comprehensive
    validation and safety checks.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize the script generator
        
        Args:
            validation_level: Level of validation to apply to generated scripts
        """
        if not NUKE_AVAILABLE:
            logger.warning("Nuke module not available. Script generation will be limited.")
        
        self.validation_level = validation_level
        
        # Safe Nuke functions that are generally allowed
        self.safe_functions = {
            # Node creation and manipulation
            'nuke.createNode', 'nuke.delete', 'nuke.toNode', 'nuke.selectedNodes',
            'nuke.allNodes', 'nuke.selectAll', 'nuke.selectNone',
            
            # Parameter access
            'node.knob', 'node.knobs', 'node.setName', 'node.name',
            
            # Connection operations
            'node.setInput', 'node.input', 'node.inputs', 'node.dependent',
            
            # Viewer and playback
            'nuke.activeViewer', 'nuke.frame', 'nuke.execute',
            
            # File operations (read-only)
            'nuke.filename', 'nuke.root',
            
            # Utility functions
            'nuke.message', 'nuke.ask', 'nuke.getInput'
        }
        
        # Dangerous functions that require special handling
        self.dangerous_functions = {
            'nuke.scriptSave', 'nuke.scriptSaveAs', 'nuke.scriptClear',
            'nuke.scriptOpen', 'nuke.render', 'nuke.renderProgress',
            'os.system', 'subprocess', 'eval', 'exec', 'compile',
            '__import__', 'open', 'file'
        }
        
        # Common node types and their safe parameters
        self.node_parameters = {
            'Read': ['file', 'first', 'last', 'origfirst', 'origlast', 'frame_mode', 'frame'],
            'Write': ['file', 'file_type', 'first', 'last', 'use_limit'],
            'Merge2': ['operation', 'mix', 'screen_alpha', 'bbox'],
            'ColorCorrect': ['saturation', 'contrast', 'gamma', 'gain', 'offset'],
            'Grade': ['whitepoint', 'blackpoint', 'white', 'black', 'multiply', 'add', 'gamma'],
            'Transform': ['translate', 'rotate', 'scale', 'skewX', 'skewY', 'center'],
            'Blur': ['size', 'filter', 'quality', 'crop'],
            'Constant': ['color', 'format']
        }
    
    def generate_node_creation_script(self, node_type: str, parameters: Dict[str, Any], 
                                    position: Optional[Tuple[int, int]] = None) -> GeneratedScript:
        """
        Generate a script to create a new node with specified parameters
        
        Args:
            node_type: Type of node to create
            parameters: Parameters to set on the node
            position: Optional position for the node
            
        Returns:
            GeneratedScript object
        """
        try:
            # Build the script
            script_lines = []
            script_lines.append(f"# Create {node_type} node")
            script_lines.append(f"node = nuke.createNode('{node_type}')")
            
            # Set position if specified
            if position:
                script_lines.append(f"node.setXYpos({position[0]}, {position[1]})")
            
            # Set parameters
            for param, value in parameters.items():
                if self._is_safe_parameter(node_type, param):
                    if isinstance(value, str):
                        script_lines.append(f"node['{param}'].setValue('{value}')")
                    else:
                        script_lines.append(f"node['{param}'].setValue({value})")
            
            script_lines.append("# Node creation complete")
            script = '\n'.join(script_lines)
            
            # Validate the script
            validation_result = self._validate_script(script)
            
            # Generate undo script
            undo_script = "nuke.delete(node)"
            
            return GeneratedScript(
                script_type=ScriptType.NODE_CREATION,
                code=script,
                description=f"Create {node_type} node with specified parameters",
                validation_result=validation_result,
                estimated_execution_time=0.1,
                dependencies=[],
                undo_script=undo_script
            )
            
        except Exception as e:
            logger.error(f"Error generating node creation script: {e}")
            return self._create_error_script(str(e))
    
    def generate_connection_script(self, connections: List[Tuple[str, str, int]]) -> GeneratedScript:
        """
        Generate a script to create connections between nodes
        
        Args:
            connections: List of (source_node, target_node, input_index) tuples
            
        Returns:
            GeneratedScript object
        """
        try:
            script_lines = []
            script_lines.append("# Create node connections")
            
            undo_lines = []
            undo_lines.append("# Undo connections")
            
            for source_name, target_name, input_index in connections:
                # Validate node names
                if not self._is_valid_node_name(source_name) or not self._is_valid_node_name(target_name):
                    continue
                
                script_lines.append(f"source_node = nuke.toNode('{source_name}')")
                script_lines.append(f"target_node = nuke.toNode('{target_name}')")
                script_lines.append("if source_node and target_node:")
                script_lines.append(f"    target_node.setInput({input_index}, source_node)")
                
                # Add undo operation
                undo_lines.append(f"target_node = nuke.toNode('{target_name}')")
                undo_lines.append("if target_node:")
                undo_lines.append(f"    target_node.setInput({input_index}, None)")
            
            script_lines.append("# Connections complete")
            script = '\n'.join(script_lines)
            undo_script = '\n'.join(undo_lines)
            
            # Validate the script
            validation_result = self._validate_script(script)
            
            return GeneratedScript(
                script_type=ScriptType.CONNECTION_SETUP,
                code=script,
                description=f"Create {len(connections)} node connections",
                validation_result=validation_result,
                estimated_execution_time=0.05 * len(connections),
                dependencies=[],
                undo_script=undo_script
            )
            
        except Exception as e:
            logger.error(f"Error generating connection script: {e}")
            return self._create_error_script(str(e))
    
    def generate_parameter_adjustment_script(self, node_name: str, 
                                           parameters: Dict[str, Any]) -> GeneratedScript:
        """
        Generate a script to adjust node parameters
        
        Args:
            node_name: Name of the node to modify
            parameters: Parameters to adjust
            
        Returns:
            GeneratedScript object
        """
        try:
            if not self._is_valid_node_name(node_name):
                raise ValueError(f"Invalid node name: {node_name}")
            
            script_lines = []
            script_lines.append(f"# Adjust parameters for {node_name}")
            script_lines.append(f"node = nuke.toNode('{node_name}')")
            script_lines.append("if node:")
            
            undo_lines = []
            undo_lines.append(f"# Restore original parameters for {node_name}")
            undo_lines.append(f"node = nuke.toNode('{node_name}')")
            undo_lines.append("if node:")
            
            for param, value in parameters.items():
                if self._is_safe_parameter_name(param):
                    script_lines.append(f"    if '{param}' in node.knobs():")
                    
                    # Store original value for undo
                    undo_lines.append(f"    if '{param}' in node.knobs():")
                    undo_lines.append(f"        original_value = node['{param}'].value()")
                    
                    if isinstance(value, str):
                        script_lines.append(f"        node['{param}'].setValue('{value}')")
                    elif isinstance(value, (list, tuple)):
                        script_lines.append(f"        node['{param}'].setValue({list(value)})")
                    else:
                        script_lines.append(f"        node['{param}'].setValue({value})")
            
            script_lines.append("    print(f'Parameters updated for {node.name()}')")
            script_lines.append("else:")
            script_lines.append(f"    print('Node {node_name} not found')")
            
            script = '\n'.join(script_lines)
            undo_script = '\n'.join(undo_lines)
            
            # Validate the script
            validation_result = self._validate_script(script)
            
            return GeneratedScript(
                script_type=ScriptType.PARAMETER_ADJUSTMENT,
                code=script,
                description=f"Adjust parameters for {node_name}",
                validation_result=validation_result,
                estimated_execution_time=0.05,
                dependencies=[node_name],
                undo_script=undo_script
            )
            
        except Exception as e:
            logger.error(f"Error generating parameter adjustment script: {e}")
            return self._create_error_script(str(e))
    
    def generate_workflow_script(self, workflow_type: str, context: Dict[str, Any]) -> GeneratedScript:
        """
        Generate a script for common VFX workflows
        
        Args:
            workflow_type: Type of workflow (e.g., 'basic_comp', 'keying_setup')
            context: Context information for the workflow
            
        Returns:
            GeneratedScript object
        """
        try:
            if workflow_type == 'basic_comp':
                return self._generate_basic_comp_workflow(context)
            elif workflow_type == 'keying_setup':
                return self._generate_keying_workflow(context)
            elif workflow_type == 'color_correction':
                return self._generate_color_correction_workflow(context)
            elif workflow_type == 'cleanup_nodes':
                return self._generate_cleanup_workflow(context)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
                
        except Exception as e:
            logger.error(f"Error generating workflow script: {e}")
            return self._create_error_script(str(e))
    
    def _generate_basic_comp_workflow(self, context: Dict[str, Any]) -> GeneratedScript:
        """Generate a basic compositing workflow"""
        script_lines = []
        script_lines.append("# Basic Compositing Workflow")
        script_lines.append("")
        
        # Create background
        script_lines.append("# Create background")
        script_lines.append("bg = nuke.createNode('Read')")
        script_lines.append("bg.setName('Background')")
        script_lines.append("bg.setXYpos(0, 0)")
        
        # Create foreground
        script_lines.append("")
        script_lines.append("# Create foreground")
        script_lines.append("fg = nuke.createNode('Read')")
        script_lines.append("fg.setName('Foreground')")
        script_lines.append("fg.setXYpos(200, 0)")
        
        # Create merge
        script_lines.append("")
        script_lines.append("# Create merge")
        script_lines.append("merge = nuke.createNode('Merge2')")
        script_lines.append("merge.setInput(0, bg)  # A input")
        script_lines.append("merge.setInput(1, fg)  # B input")
        script_lines.append("merge.setXYpos(100, 100)")
        
        # Create viewer
        script_lines.append("")
        script_lines.append("# Create viewer")
        script_lines.append("viewer = nuke.createNode('Viewer')")
        script_lines.append("viewer.setInput(0, merge)")
        script_lines.append("viewer.setXYpos(100, 200)")
        
        script = '\n'.join(script_lines)
        validation_result = self._validate_script(script)
        
        return GeneratedScript(
            script_type=ScriptType.WORKFLOW_AUTOMATION,
            code=script,
            description="Basic compositing workflow with background, foreground, and merge",
            validation_result=validation_result,
            estimated_execution_time=0.5,
            dependencies=[],
            undo_script="nuke.selectAll(); nuke.delete()"
        )
    
    def _generate_keying_workflow(self, context: Dict[str, Any]) -> GeneratedScript:
        """Generate a keying workflow"""
        script_lines = []
        script_lines.append("# Keying Workflow")
        script_lines.append("")
        
        # Create source
        script_lines.append("# Create source plate")
        script_lines.append("source = nuke.createNode('Read')")
        script_lines.append("source.setName('Source_Plate')")
        script_lines.append("source.setXYpos(0, 0)")
        
        # Create keyer
        script_lines.append("")
        script_lines.append("# Create keyer")
        script_lines.append("keyer = nuke.createNode('Keyer')")
        script_lines.append("keyer.setInput(0, source)")
        script_lines.append("keyer.setXYpos(0, 100)")
        
        # Create edge operations
        script_lines.append("")
        script_lines.append("# Edge cleanup")
        script_lines.append("erode = nuke.createNode('FilterErode')")
        script_lines.append("erode.setInput(0, keyer)")
        script_lines.append("erode['size'].setValue(-0.5)")
        script_lines.append("erode.setXYpos(0, 200)")
        
        script_lines.append("")
        script_lines.append("blur = nuke.createNode('Blur')")
        script_lines.append("blur.setInput(0, erode)")
        script_lines.append("blur['size'].setValue(1.0)")
        script_lines.append("blur.setXYpos(0, 300)")
        
        # Create premult
        script_lines.append("")
        script_lines.append("# Premultiply")
        script_lines.append("premult = nuke.createNode('Premult')")
        script_lines.append("premult.setInput(0, source)")
        script_lines.append("premult.setInput(1, blur)")
        script_lines.append("premult.setXYpos(0, 400)")
        
        script = '\n'.join(script_lines)
        validation_result = self._validate_script(script)
        
        return GeneratedScript(
            script_type=ScriptType.WORKFLOW_AUTOMATION,
            code=script,
            description="Keying workflow with edge cleanup and premultiplication",
            validation_result=validation_result,
            estimated_execution_time=0.8,
            dependencies=[],
            undo_script="nuke.selectAll(); nuke.delete()"
        )
    
    def _generate_color_correction_workflow(self, context: Dict[str, Any]) -> GeneratedScript:
        """Generate a color correction workflow"""
        script_lines = []
        script_lines.append("# Color Correction Workflow")
        script_lines.append("")
        
        # Get selected node or create read
        script_lines.append("# Get input")
        script_lines.append("selected = nuke.selectedNodes()")
        script_lines.append("if selected:")
        script_lines.append("    input_node = selected[0]")
        script_lines.append("else:")
        script_lines.append("    input_node = nuke.createNode('Read')")
        script_lines.append("    input_node.setName('Source')")
        
        # Primary correction
        script_lines.append("")
        script_lines.append("# Primary color correction")
        script_lines.append("grade = nuke.createNode('Grade')")
        script_lines.append("grade.setInput(0, input_node)")
        script_lines.append("grade.setName('Primary_Grade')")
        
        # Secondary correction
        script_lines.append("")
        script_lines.append("# Secondary color correction")
        script_lines.append("cc = nuke.createNode('ColorCorrect')")
        script_lines.append("cc.setInput(0, grade)")
        script_lines.append("cc.setName('Secondary_CC')")
        
        # Final adjustments
        script_lines.append("")
        script_lines.append("# Final adjustments")
        script_lines.append("gamma = nuke.createNode('Gamma')")
        script_lines.append("gamma.setInput(0, cc)")
        script_lines.append("gamma.setName('Final_Gamma')")
        
        script = '\n'.join(script_lines)
        validation_result = self._validate_script(script)
        
        return GeneratedScript(
            script_type=ScriptType.WORKFLOW_AUTOMATION,
            code=script,
            description="Color correction workflow with primary, secondary, and final adjustments",
            validation_result=validation_result,
            estimated_execution_time=0.3,
            dependencies=[],
            undo_script="# Select created nodes and delete\nfor node in [grade, cc, gamma]: nuke.delete(node)"
        )
    
    def _generate_cleanup_workflow(self, context: Dict[str, Any]) -> GeneratedScript:
        """Generate a node cleanup workflow"""
        script_lines = []
        script_lines.append("# Node Cleanup Workflow")
        script_lines.append("")
        
        script_lines.append("# Remove unused nodes")
        script_lines.append("removed_count = 0")
        script_lines.append("for node in nuke.allNodes():")
        script_lines.append("    if len(node.dependent()) == 0 and node.Class() not in ['Viewer', 'Write']:")
        script_lines.append("        nuke.delete(node)")
        script_lines.append("        removed_count += 1")
        script_lines.append("")
        
        script_lines.append("# Organize Dot nodes")
        script_lines.append("dot_nodes = [n for n in nuke.allNodes() if n.Class() == 'Dot']")
        script_lines.append("for dot in dot_nodes:")
        script_lines.append("    if dot.input(0) and len(dot.dependent()) == 1:")
        script_lines.append("        # Check if dot is redundant")
        script_lines.append("        input_node = dot.input(0)")
        script_lines.append("        output_node = dot.dependent()[0]")
        script_lines.append("        if abs(input_node.xpos() - output_node.xpos()) < 50:")
        script_lines.append("            # Remove redundant dot")
        script_lines.append("            for i in range(output_node.inputs()):")
        script_lines.append("                if output_node.input(i) == dot:")
        script_lines.append("                    output_node.setInput(i, input_node)")
        script_lines.append("                    break")
        script_lines.append("            nuke.delete(dot)")
        script_lines.append("")
        
        script_lines.append("print(f'Cleanup complete. Removed {removed_count} unused nodes.')")
        
        script = '\n'.join(script_lines)
        validation_result = self._validate_script(script)
        
        return GeneratedScript(
            script_type=ScriptType.UTILITY,
            code=script,
            description="Clean up unused nodes and optimize node graph",
            validation_result=validation_result,
            estimated_execution_time=1.0,
            dependencies=[],
            undo_script="# Cleanup operations cannot be easily undone"
        )
    
    def _validate_script(self, script: str) -> ScriptValidationResult:
        """
        Validate a script for safety and correctness
        
        Args:
            script: The script code to validate
            
        Returns:
            ScriptValidationResult object
        """
        errors = []
        warnings = []
        suggestions = []
        risk_level = "low"
        
        try:
            # Parse the script to check for syntax errors
            try:
                ast.parse(script)
            except SyntaxError as e:
                errors.append(f"Syntax error: {e}")
                return ScriptValidationResult(False, errors, warnings, suggestions, "high")
            
            # Check for dangerous functions
            for dangerous_func in self.dangerous_functions:
                if dangerous_func in script:
                    if self.validation_level == ValidationLevel.STRICT:
                        errors.append(f"Dangerous function not allowed: {dangerous_func}")
                        risk_level = "high"
                    else:
                        warnings.append(f"Potentially dangerous function: {dangerous_func}")
                        risk_level = "medium"
            
            # Check for eval/exec usage
            if re.search(r'\b(eval|exec)\s*\(', script):
                errors.append("Dynamic code execution (eval/exec) not allowed")
                risk_level = "high"
            
            # Check for file system operations
            if re.search(r'\b(open|file)\s*\(', script):
                if self.validation_level == ValidationLevel.STRICT:
                    errors.append("File operations not allowed in strict mode")
                    risk_level = "high"
                else:
                    warnings.append("File operations detected - ensure paths are safe")
                    risk_level = "medium"
            
            # Check for import statements
            if re.search(r'\b(import|from)\s+', script):
                if self.validation_level == ValidationLevel.STRICT:
                    errors.append("Import statements not allowed in strict mode")
                else:
                    warnings.append("Import statements detected - verify module safety")
            
            # Check for proper error handling
            if 'nuke.toNode' in script and 'if' not in script:
                suggestions.append("Consider adding null checks for nuke.toNode() calls")
            
            # Check for hardcoded paths
            if re.search(r'["\'][A-Za-z]:[\\\/]', script):
                warnings.append("Hardcoded file paths detected - consider using relative paths")
            
            # Performance suggestions
            if script.count('nuke.allNodes()') > 1:
                suggestions.append("Multiple nuke.allNodes() calls - consider caching the result")
            
            is_valid = len(errors) == 0
            
            return ScriptValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Error validating script: {e}")
            return ScriptValidationResult(
                is_valid=False,
                errors=[f"Validation error: {e}"],
                warnings=[],
                suggestions=[],
                risk_level="high"
            )
    
    def _is_safe_parameter(self, node_type: str, parameter: str) -> bool:
        """Check if a parameter is safe to set for a node type"""
        if node_type in self.node_parameters:
            return parameter in self.node_parameters[node_type]
        
        # Common safe parameters for all nodes
        safe_params = ['name', 'label', 'note', 'selected', 'xpos', 'ypos']
        return parameter in safe_params
    
    def _is_safe_parameter_name(self, parameter: str) -> bool:
        """Check if a parameter name is safe (no injection attacks)"""
        # Only allow alphanumeric characters, underscores, and dots
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', parameter) is not None
    
    def _is_valid_node_name(self, node_name: str) -> bool:
        """Check if a node name is valid and safe"""
        # Only allow alphanumeric characters, underscores, and hyphens
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', node_name) is not None
    
    def _create_error_script(self, error_message: str) -> GeneratedScript:
        """Create an error script when generation fails"""
        return GeneratedScript(
            script_type=ScriptType.UTILITY,
            code=f"# Error generating script: {error_message}\nprint('Script generation failed: {error_message}')",
            description=f"Error: {error_message}",
            validation_result=ScriptValidationResult(
                is_valid=False,
                errors=[error_message],
                warnings=[],
                suggestions=[],
                risk_level="high"
            ),
            estimated_execution_time=0.0,
            dependencies=[],
            undo_script=None
        )
    
    def format_script_for_execution(self, generated_script: GeneratedScript) -> str:
        """
        Format a generated script for safe execution with error handling
        
        Args:
            generated_script: The generated script to format
            
        Returns:
            Formatted script with error handling
        """
        if not generated_script.validation_result.is_valid:
            return "# Script validation failed - execution not recommended"
        
        formatted_lines = []
        formatted_lines.append("# Auto-generated Nuke script")
        formatted_lines.append(f"# Description: {generated_script.description}")
        formatted_lines.append(f"# Type: {generated_script.script_type.value}")
        formatted_lines.append("")
        
        formatted_lines.append("try:")
        # Indent the original script
        for line in generated_script.code.split('\n'):
            if line.strip():
                formatted_lines.append(f"    {line}")
            else:
                formatted_lines.append("")
        
        formatted_lines.append("")
        formatted_lines.append("except Exception as e:")
        formatted_lines.append("    nuke.message(f'Script execution error: {e}')")
        formatted_lines.append("    print(f'Error: {e}')")
        
        return '\n'.join(formatted_lines)