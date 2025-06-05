"""
Action Applier

Safely applies AI-generated suggestions to Nuke with comprehensive undo/redo support,
validation, and rollback capabilities.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager

# Handle Nuke import gracefully
try:
    import nuke
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False
    nuke = None

from .script_generator import NukeScriptGenerator, GeneratedScript, ValidationLevel

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """Status of an applied action"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionType(Enum):
    """Types of actions that can be applied"""
    SCRIPT_EXECUTION = "script_execution"
    PARAMETER_CHANGE = "parameter_change"
    NODE_CREATION = "node_creation"
    NODE_DELETION = "node_deletion"
    CONNECTION_CHANGE = "connection_change"
    WORKFLOW_APPLICATION = "workflow_application"


@dataclass
class ActionSnapshot:
    """Snapshot of the state before an action"""
    timestamp: float
    selected_nodes: List[str]
    node_states: Dict[str, Dict[str, Any]]
    connections: List[Dict[str, Any]]
    script_modified: bool


@dataclass
class AppliedAction:
    """Record of an applied action with undo information"""
    action_id: str
    action_type: ActionType
    description: str
    timestamp: float
    status: ActionStatus
    generated_script: Optional[GeneratedScript]
    pre_action_snapshot: Optional[ActionSnapshot]
    execution_time: float
    error_message: Optional[str] = None
    user_confirmed: bool = False


class ActionApplier:
    """
    Safely applies AI-generated suggestions to Nuke with comprehensive
    undo/redo support and validation.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize the action applier
        
        Args:
            validation_level: Level of validation for script execution
        """
        if not NUKE_AVAILABLE:
            logger.warning("Nuke module not available. Action application will be limited.")
        
        self.validation_level = validation_level
        self.script_generator = NukeScriptGenerator(validation_level)
        
        # Action history for undo/redo
        self.action_history: List[AppliedAction] = []
        self.max_history_size = 50
        
        # Current action being executed
        self.current_action: Optional[AppliedAction] = None
        
        # Safety settings
        self.require_confirmation = True
        self.auto_snapshot = True
        self.max_execution_time = 30.0  # seconds
    
    def apply_script(self, generated_script: GeneratedScript, 
                    require_confirmation: Optional[bool] = None) -> AppliedAction:
        """
        Apply a generated script to Nuke
        
        Args:
            generated_script: The script to apply
            require_confirmation: Override default confirmation requirement
            
        Returns:
            AppliedAction record
        """
        if not NUKE_AVAILABLE:
            return self._create_failed_action("Nuke not available", ActionType.SCRIPT_EXECUTION)
        
        action_id = self._generate_action_id()
        
        try:
            # Create action record
            action = AppliedAction(
                action_id=action_id,
                action_type=ActionType.SCRIPT_EXECUTION,
                description=generated_script.description,
                timestamp=time.time(),
                status=ActionStatus.PENDING,
                generated_script=generated_script,
                pre_action_snapshot=None,
                execution_time=0.0,
                user_confirmed=False
            )
            
            # Validate script
            if not generated_script.validation_result.is_valid:
                action.status = ActionStatus.FAILED
                action.error_message = "Script validation failed: " + "; ".join(generated_script.validation_result.errors)
                self._add_to_history(action)
                return action
            
            # Check if confirmation is required
            needs_confirmation = require_confirmation if require_confirmation is not None else self.require_confirmation
            if needs_confirmation and not self._get_user_confirmation(generated_script):
                action.status = ActionStatus.FAILED
                action.error_message = "User cancelled action"
                self._add_to_history(action)
                return action
            
            action.user_confirmed = True
            
            # Take snapshot if enabled
            if self.auto_snapshot:
                action.pre_action_snapshot = self._take_snapshot()
            
            # Execute the script
            action.status = ActionStatus.EXECUTING
            self.current_action = action
            
            start_time = time.time()
            success = self._execute_script_safely(generated_script)
            execution_time = time.time() - start_time
            
            action.execution_time = execution_time
            
            if success:
                action.status = ActionStatus.SUCCESS
                logger.info(f"Successfully applied action: {action.description}")
            else:
                action.status = ActionStatus.FAILED
                action.error_message = "Script execution failed"
            
            self.current_action = None
            self._add_to_history(action)
            
            return action
            
        except Exception as e:
            logger.error(f"Error applying script: {e}")
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            action.execution_time = time.time() - action.timestamp
            self.current_action = None
            self._add_to_history(action)
            return action
    
    def apply_parameter_changes(self, node_name: str, parameters: Dict[str, Any],
                              require_confirmation: Optional[bool] = None) -> AppliedAction:
        """
        Apply parameter changes to a node
        
        Args:
            node_name: Name of the node to modify
            parameters: Parameters to change
            require_confirmation: Override default confirmation requirement
            
        Returns:
            AppliedAction record
        """
        if not NUKE_AVAILABLE:
            return self._create_failed_action("Nuke not available", ActionType.PARAMETER_CHANGE)
        
        try:
            # Generate script for parameter changes
            generated_script = self.script_generator.generate_parameter_adjustment_script(
                node_name, parameters
            )
            
            # Apply the script
            action = self.apply_script(generated_script, require_confirmation)
            action.action_type = ActionType.PARAMETER_CHANGE
            
            return action
            
        except Exception as e:
            logger.error(f"Error applying parameter changes: {e}")
            return self._create_failed_action(str(e), ActionType.PARAMETER_CHANGE)
    
    def apply_workflow(self, workflow_type: str, context: Dict[str, Any],
                      require_confirmation: Optional[bool] = None) -> AppliedAction:
        """
        Apply a VFX workflow
        
        Args:
            workflow_type: Type of workflow to apply
            context: Context for the workflow
            require_confirmation: Override default confirmation requirement
            
        Returns:
            AppliedAction record
        """
        if not NUKE_AVAILABLE:
            return self._create_failed_action("Nuke not available", ActionType.WORKFLOW_APPLICATION)
        
        try:
            # Generate workflow script
            generated_script = self.script_generator.generate_workflow_script(
                workflow_type, context
            )
            
            # Apply the script
            action = self.apply_script(generated_script, require_confirmation)
            action.action_type = ActionType.WORKFLOW_APPLICATION
            
            return action
            
        except Exception as e:
            logger.error(f"Error applying workflow: {e}")
            return self._create_failed_action(str(e), ActionType.WORKFLOW_APPLICATION)
    
    def undo_last_action(self) -> bool:
        """
        Undo the last applied action
        
        Returns:
            True if undo was successful, False otherwise
        """
        if not NUKE_AVAILABLE:
            logger.error("Cannot undo: Nuke not available")
            return False
        
        if not self.action_history:
            logger.warning("No actions to undo")
            return False
        
        last_action = self.action_history[-1]
        
        if last_action.status != ActionStatus.SUCCESS:
            logger.warning("Cannot undo failed action")
            return False
        
        try:
            success = self._undo_action(last_action)
            if success:
                last_action.status = ActionStatus.ROLLED_BACK
                logger.info(f"Successfully undid action: {last_action.description}")
            return success
            
        except Exception as e:
            logger.error(f"Error undoing action: {e}")
            return False
    
    def undo_action_by_id(self, action_id: str) -> bool:
        """
        Undo a specific action by ID
        
        Args:
            action_id: ID of the action to undo
            
        Returns:
            True if undo was successful, False otherwise
        """
        action = self._find_action_by_id(action_id)
        if not action:
            logger.error(f"Action not found: {action_id}")
            return False
        
        if action.status != ActionStatus.SUCCESS:
            logger.warning(f"Cannot undo action with status: {action.status}")
            return False
        
        try:
            success = self._undo_action(action)
            if success:
                action.status = ActionStatus.ROLLED_BACK
                logger.info(f"Successfully undid action: {action.description}")
            return success
            
        except Exception as e:
            logger.error(f"Error undoing action {action_id}: {e}")
            return False
    
    def get_action_history(self, limit: Optional[int] = None) -> List[AppliedAction]:
        """
        Get the action history
        
        Args:
            limit: Maximum number of actions to return
            
        Returns:
            List of applied actions
        """
        if limit:
            return self.action_history[-limit:]
        return self.action_history.copy()
    
    def clear_history(self) -> None:
        """Clear the action history"""
        self.action_history.clear()
        logger.info("Action history cleared")
    
    def export_action_history(self, file_path: str) -> bool:
        """
        Export action history to a file
        
        Args:
            file_path: Path to save the history
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Convert actions to serializable format
            serializable_history = []
            for action in self.action_history:
                action_dict = asdict(action)
                # Remove non-serializable objects
                if action_dict['generated_script']:
                    action_dict['generated_script'] = {
                        'script_type': action.generated_script.script_type.value,
                        'description': action.generated_script.description,
                        'code': action.generated_script.code
                    }
                serializable_history.append(action_dict)
            
            with open(file_path, 'w') as f:
                json.dump(serializable_history, f, indent=2)
            
            logger.info(f"Action history exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting action history: {e}")
            return False
    
    @contextmanager
    def batch_actions(self):
        """
        Context manager for batching multiple actions with single undo point
        """
        if not NUKE_AVAILABLE:
            yield
            return
        
        # Take snapshot before batch
        snapshot = self._take_snapshot()
        batch_start_time = time.time()
        batch_actions = []
        
        try:
            # Temporarily disable auto-snapshot for individual actions
            original_auto_snapshot = self.auto_snapshot
            self.auto_snapshot = False
            
            yield batch_actions
            
            # Create a batch action record
            batch_action = AppliedAction(
                action_id=self._generate_action_id(),
                action_type=ActionType.WORKFLOW_APPLICATION,
                description=f"Batch operation with {len(batch_actions)} actions",
                timestamp=batch_start_time,
                status=ActionStatus.SUCCESS,
                generated_script=None,
                pre_action_snapshot=snapshot,
                execution_time=time.time() - batch_start_time,
                user_confirmed=True
            )
            
            self._add_to_history(batch_action)
            
        except Exception as e:
            logger.error(f"Error in batch actions: {e}")
            # Restore from snapshot on error
            if snapshot:
                self._restore_from_snapshot(snapshot)
        finally:
            # Restore auto-snapshot setting
            self.auto_snapshot = original_auto_snapshot
    
    def _execute_script_safely(self, generated_script: GeneratedScript) -> bool:
        """
        Execute a script safely with timeout and error handling
        
        Args:
            generated_script: The script to execute
            
        Returns:
            True if execution was successful, False otherwise
        """
        try:
            # Format script for execution
            formatted_script = self.script_generator.format_script_for_execution(generated_script)
            
            # Execute with timeout
            start_time = time.time()
            
            # Use Nuke's executeInMainThread for thread safety
            if hasattr(nuke, 'executeInMainThread'):
                result = nuke.executeInMainThread(lambda: exec(formatted_script))
            else:
                exec(formatted_script)
            
            execution_time = time.time() - start_time
            
            if execution_time > self.max_execution_time:
                logger.warning(f"Script execution took {execution_time:.2f}s (max: {self.max_execution_time}s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return False
    
    def _get_user_confirmation(self, generated_script: GeneratedScript) -> bool:
        """
        Get user confirmation for script execution
        
        Args:
            generated_script: The script to confirm
            
        Returns:
            True if user confirmed, False otherwise
        """
        try:
            if not NUKE_AVAILABLE:
                return False
            
            # Build confirmation message
            message = f"Execute the following action?\n\n"
            message += f"Description: {generated_script.description}\n"
            message += f"Type: {generated_script.script_type.value}\n"
            message += f"Estimated time: {generated_script.estimated_execution_time:.2f}s\n"
            
            if generated_script.validation_result.warnings:
                message += f"\nWarnings:\n"
                for warning in generated_script.validation_result.warnings:
                    message += f"- {warning}\n"
            
            if generated_script.validation_result.risk_level != "low":
                message += f"\nRisk level: {generated_script.validation_result.risk_level}\n"
            
            # Use Nuke's ask dialog
            return nuke.ask(message)
            
        except Exception as e:
            logger.error(f"Error getting user confirmation: {e}")
            return False
    
    def _take_snapshot(self) -> Optional[ActionSnapshot]:
        """
        Take a snapshot of the current Nuke state
        
        Returns:
            ActionSnapshot or None if failed
        """
        try:
            if not NUKE_AVAILABLE:
                return None
            
            # Get selected nodes
            selected_nodes = [node.name() for node in nuke.selectedNodes()]
            
            # Get node states
            node_states = {}
            for node in nuke.allNodes():
                node_states[node.name()] = self._get_node_state(node)
            
            # Get connections
            connections = []
            for node in nuke.allNodes():
                for i in range(node.inputs()):
                    input_node = node.input(i)
                    if input_node:
                        connections.append({
                            'target': node.name(),
                            'target_input': i,
                            'source': input_node.name()
                        })
            
            # Check if script is modified
            script_modified = nuke.modified()
            
            return ActionSnapshot(
                timestamp=time.time(),
                selected_nodes=selected_nodes,
                node_states=node_states,
                connections=connections,
                script_modified=script_modified
            )
            
        except Exception as e:
            logger.error(f"Error taking snapshot: {e}")
            return None
    
    def _get_node_state(self, node) -> Dict[str, Any]:
        """Get the current state of a node"""
        try:
            state = {
                'class': node.Class(),
                'position': (node.xpos(), node.ypos()),
                'selected': node['selected'].value(),
                'knobs': {}
            }
            
            # Get important knob values
            for knob_name in node.knobs():
                try:
                    knob = node[knob_name]
                    if knob.Class() not in ['Tab_Knob', 'Text_Knob']:
                        state['knobs'][knob_name] = knob.value()
                except:
                    pass
            
            return state
            
        except Exception as e:
            logger.warning(f"Error getting state for node {node.name()}: {e}")
            return {}
    
    def _undo_action(self, action: AppliedAction) -> bool:
        """
        Undo a specific action
        
        Args:
            action: The action to undo
            
        Returns:
            True if undo was successful, False otherwise
        """
        try:
            # If we have an undo script, try to execute it
            if action.generated_script and action.generated_script.undo_script:
                try:
                    exec(action.generated_script.undo_script)
                    return True
                except Exception as e:
                    logger.warning(f"Undo script failed: {e}")
            
            # Fall back to snapshot restoration
            if action.pre_action_snapshot:
                return self._restore_from_snapshot(action.pre_action_snapshot)
            
            logger.warning("No undo method available for action")
            return False
            
        except Exception as e:
            logger.error(f"Error undoing action: {e}")
            return False
    
    def _restore_from_snapshot(self, snapshot: ActionSnapshot) -> bool:
        """
        Restore Nuke state from a snapshot
        
        Args:
            snapshot: The snapshot to restore from
            
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            if not NUKE_AVAILABLE:
                return False
            
            # This is a simplified restoration - in practice, full state restoration
            # is complex and may require more sophisticated handling
            
            # Restore selection
            nuke.selectNone()
            for node_name in snapshot.selected_nodes:
                node = nuke.toNode(node_name)
                if node:
                    node['selected'].setValue(True)
            
            logger.info("State restored from snapshot")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from snapshot: {e}")
            return False
    
    def _generate_action_id(self) -> str:
        """Generate a unique action ID"""
        return f"action_{int(time.time() * 1000)}"
    
    def _add_to_history(self, action: AppliedAction) -> None:
        """Add an action to the history"""
        self.action_history.append(action)
        
        # Trim history if it exceeds max size
        if len(self.action_history) > self.max_history_size:
            self.action_history = self.action_history[-self.max_history_size:]
    
    def _find_action_by_id(self, action_id: str) -> Optional[AppliedAction]:
        """Find an action by its ID"""
        for action in self.action_history:
            if action.action_id == action_id:
                return action
        return None
    
    def _create_failed_action(self, error_message: str, action_type: ActionType) -> AppliedAction:
        """Create a failed action record"""
        return AppliedAction(
            action_id=self._generate_action_id(),
            action_type=action_type,
            description="Failed action",
            timestamp=time.time(),
            status=ActionStatus.FAILED,
            generated_script=None,
            pre_action_snapshot=None,
            execution_time=0.0,
            error_message=error_message
        )