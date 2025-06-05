"""
Nuke Context Analyzer

Analyzes the current Nuke session state including node graph, selections,
viewer state, and project context to provide comprehensive information
for AI-powered assistance.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
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


class ViewerState(Enum):
    """Viewer state enumeration"""
    NONE = "none"
    RGBA = "rgba"
    RGB = "rgb"
    ALPHA = "alpha"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    LUMINANCE = "luminance"


@dataclass
class NodeInfo:
    """Information about a single node"""
    name: str
    class_name: str
    position: Tuple[float, float]
    selected: bool
    disabled: bool
    inputs: List[str]
    outputs: List[str]
    knob_values: Dict[str, Any]
    error_state: Optional[str] = None


@dataclass
class SessionContext:
    """Complete Nuke session context"""
    project_name: str
    script_path: Optional[str]
    frame_range: Tuple[int, int]
    current_frame: int
    fps: float
    format_info: Dict[str, Any]
    selected_nodes: List[str]
    viewer_node: Optional[str]
    viewer_state: ViewerState
    nodes: List[NodeInfo]
    node_graph_bounds: Tuple[float, float, float, float]
    total_nodes: int
    error_nodes: List[str]
    performance_stats: Dict[str, Any]


class NukeContextAnalyzer:
    """
    Analyzes the current Nuke session to extract comprehensive context
    for AI-powered assistance and workflow optimization.
    """
    
    def __init__(self):
        """Initialize the context analyzer"""
        if not NUKE_AVAILABLE:
            logger.warning("Nuke module not available. Context analysis will be limited.")
        
        self._cache_timeout = 5.0  # Cache context for 5 seconds
        self._last_analysis = None
        self._last_analysis_time = 0
    
    def get_session_context(self, force_refresh: bool = False) -> Optional[SessionContext]:
        """
        Get comprehensive session context
        
        Args:
            force_refresh: Force refresh of cached context
            
        Returns:
            SessionContext object or None if Nuke not available
        """
        if not NUKE_AVAILABLE:
            logger.error("Cannot analyze context: Nuke not available")
            return None
        
        try:
            import time
            current_time = time.time()
            
            # Return cached result if recent and not forcing refresh
            if (not force_refresh and 
                self._last_analysis and 
                current_time - self._last_analysis_time < self._cache_timeout):
                return self._last_analysis
            
            # Analyze current session
            context = self._analyze_session()
            
            # Cache the result
            self._last_analysis = context
            self._last_analysis_time = current_time
            
            return context
            
        except Exception as e:
            logger.error(f"Error analyzing session context: {e}")
            return None
    
    def _analyze_session(self) -> SessionContext:
        """Perform comprehensive session analysis"""
        # Get basic project info
        project_name = self._get_project_name()
        script_path = self._get_script_path()
        
        # Get timeline info
        frame_range = self._get_frame_range()
        current_frame = nuke.frame()
        fps = nuke.root()['fps'].value()
        
        # Get format info
        format_info = self._get_format_info()
        
        # Get viewer info
        viewer_node, viewer_state = self._get_viewer_info()
        
        # Analyze all nodes
        nodes = self._analyze_all_nodes()
        selected_nodes = [node.name for node in nodes if node.selected]
        error_nodes = [node.name for node in nodes if node.error_state]
        
        # Get node graph bounds
        bounds = self._get_node_graph_bounds(nodes)
        
        # Get performance stats
        performance_stats = self._get_performance_stats()
        
        return SessionContext(
            project_name=project_name,
            script_path=script_path,
            frame_range=frame_range,
            current_frame=current_frame,
            fps=fps,
            format_info=format_info,
            selected_nodes=selected_nodes,
            viewer_node=viewer_node,
            viewer_state=viewer_state,
            nodes=nodes,
            node_graph_bounds=bounds,
            total_nodes=len(nodes),
            error_nodes=error_nodes,
            performance_stats=performance_stats
        )
    
    def _get_project_name(self) -> str:
        """Get project name from script or default"""
        try:
            script_name = nuke.root().name()
            if script_name and script_name != "Root":
                return script_name.split('/')[-1].replace('.nk', '')
            return "Untitled Project"
        except:
            return "Unknown Project"
    
    def _get_script_path(self) -> Optional[str]:
        """Get current script path"""
        try:
            return nuke.root().name() if nuke.root().name() != "Root" else None
        except:
            return None
    
    def _get_frame_range(self) -> Tuple[int, int]:
        """Get project frame range"""
        try:
            root = nuke.root()
            first_frame = int(root['first_frame'].value())
            last_frame = int(root['last_frame'].value())
            return (first_frame, last_frame)
        except:
            return (1, 100)
    
    def _get_format_info(self) -> Dict[str, Any]:
        """Get project format information"""
        try:
            root_format = nuke.root()['format'].value()
            return {
                'name': root_format.name(),
                'width': root_format.width(),
                'height': root_format.height(),
                'pixel_aspect': root_format.pixelAspect(),
                'x': root_format.x(),
                'y': root_format.y(),
                'r': root_format.r(),
                't': root_format.t()
            }
        except Exception as e:
            logger.warning(f"Could not get format info: {e}")
            return {'name': 'Unknown', 'width': 1920, 'height': 1080}
    
    def _get_viewer_info(self) -> Tuple[Optional[str], ViewerState]:
        """Get current viewer information"""
        try:
            # Find active viewer
            for node in nuke.allNodes('Viewer'):
                if node.name() == nuke.activeViewer().node().name():
                    viewer_name = node.name()
                    
                    # Get viewer channels
                    channels = nuke.activeViewer().channels()
                    if 'rgba' in channels.lower():
                        state = ViewerState.RGBA
                    elif 'rgb' in channels.lower():
                        state = ViewerState.RGB
                    elif 'alpha' in channels.lower():
                        state = ViewerState.ALPHA
                    elif 'red' in channels.lower():
                        state = ViewerState.RED
                    elif 'green' in channels.lower():
                        state = ViewerState.GREEN
                    elif 'blue' in channels.lower():
                        state = ViewerState.BLUE
                    elif 'luminance' in channels.lower():
                        state = ViewerState.LUMINANCE
                    else:
                        state = ViewerState.NONE
                    
                    return viewer_name, state
            
            return None, ViewerState.NONE
            
        except Exception as e:
            logger.warning(f"Could not get viewer info: {e}")
            return None, ViewerState.NONE
    
    def _analyze_all_nodes(self) -> List[NodeInfo]:
        """Analyze all nodes in the script"""
        nodes = []
        
        try:
            for node in nuke.allNodes(recurseGroups=True):
                node_info = self._analyze_single_node(node)
                if node_info:
                    nodes.append(node_info)
        except Exception as e:
            logger.error(f"Error analyzing nodes: {e}")
        
        return nodes
    
    def _analyze_single_node(self, node) -> Optional[NodeInfo]:
        """Analyze a single node"""
        try:
            # Basic info
            name = node.name()
            class_name = node.Class()
            position = (node.xpos(), node.ypos())
            selected = node['selected'].value()
            disabled = node['disable'].value() if 'disable' in node.knobs() else False
            
            # Input/output connections
            inputs = []
            for i in range(node.inputs()):
                input_node = node.input(i)
                if input_node:
                    inputs.append(input_node.name())
                else:
                    inputs.append(None)
            
            outputs = []
            for output in node.dependent():
                outputs.append(output.name())
            
            # Get important knob values
            knob_values = self._get_important_knobs(node)
            
            # Check for errors
            error_state = None
            try:
                if hasattr(node, 'hasError') and node.hasError():
                    error_state = "Node has error"
            except:
                pass
            
            return NodeInfo(
                name=name,
                class_name=class_name,
                position=position,
                selected=selected,
                disabled=disabled,
                inputs=inputs,
                outputs=outputs,
                knob_values=knob_values,
                error_state=error_state
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing node {node.name() if hasattr(node, 'name') else 'unknown'}: {e}")
            return None
    
    def _get_important_knobs(self, node) -> Dict[str, Any]:
        """Extract important knob values from a node"""
        important_knobs = {}
        
        # Common important knobs across node types
        common_knobs = ['file', 'channels', 'operation', 'mix', 'size', 'center', 'translate', 'rotate', 'scale']
        
        try:
            for knob_name in common_knobs:
                if knob_name in node.knobs():
                    knob = node[knob_name]
                    try:
                        if knob.Class() == 'File_Knob':
                            important_knobs[knob_name] = knob.value()
                        elif knob.Class() == 'Enumeration_Knob':
                            important_knobs[knob_name] = knob.enumName(int(knob.value()))
                        else:
                            important_knobs[knob_name] = knob.value()
                    except:
                        important_knobs[knob_name] = str(knob.value())
            
            # Node-specific important knobs
            if node.Class() == 'Read':
                if 'first' in node.knobs():
                    important_knobs['first'] = node['first'].value()
                if 'last' in node.knobs():
                    important_knobs['last'] = node['last'].value()
            
            elif node.Class() == 'Write':
                if 'file_type' in node.knobs():
                    important_knobs['file_type'] = node['file_type'].enumName(int(node['file_type'].value()))
            
            elif node.Class() in ['Merge2', 'Merge']:
                if 'operation' in node.knobs():
                    important_knobs['operation'] = node['operation'].enumName(int(node['operation'].value()))
            
        except Exception as e:
            logger.warning(f"Error getting knobs for {node.name()}: {e}")
        
        return important_knobs
    
    def _get_node_graph_bounds(self, nodes: List[NodeInfo]) -> Tuple[float, float, float, float]:
        """Calculate bounding box of all nodes"""
        if not nodes:
            return (0, 0, 0, 0)
        
        min_x = min(node.position[0] for node in nodes)
        max_x = max(node.position[0] for node in nodes)
        min_y = min(node.position[1] for node in nodes)
        max_y = max(node.position[1] for node in nodes)
        
        return (min_x, min_y, max_x, max_y)
    
    def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance-related statistics"""
        stats = {
            'memory_usage': 'unknown',
            'cache_usage': 'unknown',
            'render_time': 'unknown'
        }
        
        try:
            # Try to get memory info if available
            if hasattr(nuke, 'memory'):
                stats['memory_usage'] = nuke.memory('usage')
            
            # Cache information
            if hasattr(nuke, 'cache'):
                stats['cache_usage'] = nuke.cache('usage')
                
        except Exception as e:
            logger.debug(f"Could not get performance stats: {e}")
        
        return stats
    
    def get_selected_nodes_context(self) -> List[NodeInfo]:
        """Get detailed context for currently selected nodes"""
        if not NUKE_AVAILABLE:
            return []
        
        try:
            selected_nodes = []
            for node in nuke.selectedNodes():
                node_info = self._analyze_single_node(node)
                if node_info:
                    selected_nodes.append(node_info)
            return selected_nodes
        except Exception as e:
            logger.error(f"Error getting selected nodes context: {e}")
            return []
    
    def get_node_dependencies(self, node_name: str) -> Dict[str, List[str]]:
        """Get upstream and downstream dependencies for a node"""
        if not NUKE_AVAILABLE:
            return {'upstream': [], 'downstream': []}
        
        try:
            node = nuke.toNode(node_name)
            if not node:
                return {'upstream': [], 'downstream': []}
            
            # Get upstream dependencies
            upstream = []
            self._collect_upstream_nodes(node, upstream, set())
            
            # Get downstream dependencies
            downstream = []
            self._collect_downstream_nodes(node, downstream, set())
            
            return {
                'upstream': upstream,
                'downstream': downstream
            }
            
        except Exception as e:
            logger.error(f"Error getting dependencies for {node_name}: {e}")
            return {'upstream': [], 'downstream': []}
    
    def _collect_upstream_nodes(self, node, collected: List[str], visited: set):
        """Recursively collect upstream nodes"""
        for i in range(node.inputs()):
            input_node = node.input(i)
            if input_node and input_node.name() not in visited:
                visited.add(input_node.name())
                collected.append(input_node.name())
                self._collect_upstream_nodes(input_node, collected, visited)
    
    def _collect_downstream_nodes(self, node, collected: List[str], visited: set):
        """Recursively collect downstream nodes"""
        for dependent in node.dependent():
            if dependent.name() not in visited:
                visited.add(dependent.name())
                collected.append(dependent.name())
                self._collect_downstream_nodes(dependent, collected, visited)