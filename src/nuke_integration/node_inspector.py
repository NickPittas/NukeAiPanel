"""
Node Inspector

Deep analysis of node connections, parameters, and data flow within Nuke.
Provides detailed insights into node relationships, data types, and optimization opportunities.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
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


class DataType(Enum):
    """Data types flowing through node connections"""
    RGBA = "rgba"
    RGB = "rgb"
    ALPHA = "alpha"
    DEPTH = "depth"
    MOTION = "motion"
    NORMALS = "normals"
    POSITION = "position"
    UV = "uv"
    UNKNOWN = "unknown"


class ConnectionType(Enum):
    """Types of node connections"""
    IMAGE = "image"
    MASK = "mask"
    DEPTH = "depth"
    MOTION = "motion"
    AUXILIARY = "auxiliary"


@dataclass
class ConnectionInfo:
    """Information about a node connection"""
    source_node: str
    target_node: str
    source_output: int
    target_input: int
    connection_type: ConnectionType
    data_type: DataType
    channels: List[str]
    format_info: Dict[str, Any]


@dataclass
class NodeAnalysis:
    """Comprehensive analysis of a single node"""
    name: str
    class_name: str
    category: str
    description: str
    input_connections: List[ConnectionInfo]
    output_connections: List[ConnectionInfo]
    parameters: Dict[str, Any]
    performance_impact: str
    optimization_suggestions: List[str]
    potential_issues: List[str]
    data_flow_role: str


@dataclass
class GraphAnalysis:
    """Analysis of the entire node graph"""
    total_nodes: int
    node_categories: Dict[str, int]
    connection_count: int
    data_flow_paths: List[List[str]]
    bottlenecks: List[str]
    optimization_opportunities: List[str]
    complexity_score: float
    render_order: List[str]


class NodeInspector:
    """
    Deep analysis of node connections, parameters, and data flow.
    Provides insights for optimization and workflow improvement.
    """
    
    def __init__(self):
        """Initialize the node inspector"""
        if not NUKE_AVAILABLE:
            logger.warning("Nuke module not available. Node inspection will be limited.")
        
        # Node categories for classification
        self.node_categories = {
            'input': ['Read', 'Constant', 'CheckerBoard', 'Noise', 'Ramp'],
            'output': ['Write', 'Viewer'],
            'color': ['ColorCorrect', 'Grade', 'Gamma', 'Invert', 'Clamp', 'Saturation'],
            'filter': ['Blur', 'Sharpen', 'Median', 'Dilate', 'Erode'],
            'transform': ['Transform', 'CornerPin', 'GridWarp', 'SplineWarp', 'Tracker'],
            'composite': ['Merge2', 'Merge', 'Over', 'Plus', 'Multiply', 'Screen'],
            'matte': ['Keyer', 'Primatte', 'IBKColour', 'IBKGizmo', 'Shuffle'],
            'time': ['TimeOffset', 'FrameHold', 'Retime', 'OFlow'],
            'utility': ['Dot', 'NoOp', 'Switch', 'Copy', 'Remove'],
            '3d': ['Camera', 'Light', 'Geometry', 'Scene', 'ScanlineRender'],
            'deep': ['DeepRead', 'DeepWrite', 'DeepMerge', 'DeepToImage'],
            'particle': ['ParticleSystem', 'ParticleRender', 'ParticleEmitter']
        }
    
    def analyze_node(self, node_name: str) -> Optional[NodeAnalysis]:
        """
        Perform comprehensive analysis of a single node
        
        Args:
            node_name: Name of the node to analyze
            
        Returns:
            NodeAnalysis object or None if node not found
        """
        if not NUKE_AVAILABLE:
            logger.error("Cannot analyze node: Nuke not available")
            return None
        
        try:
            node = nuke.toNode(node_name)
            if not node:
                logger.error(f"Node '{node_name}' not found")
                return None
            
            return self._analyze_single_node(node)
            
        except Exception as e:
            logger.error(f"Error analyzing node {node_name}: {e}")
            return None
    
    def analyze_selected_nodes(self) -> List[NodeAnalysis]:
        """Analyze all currently selected nodes"""
        if not NUKE_AVAILABLE:
            return []
        
        try:
            analyses = []
            for node in nuke.selectedNodes():
                analysis = self._analyze_single_node(node)
                if analysis:
                    analyses.append(analysis)
            return analyses
        except Exception as e:
            logger.error(f"Error analyzing selected nodes: {e}")
            return []
    
    def analyze_graph(self) -> Optional[GraphAnalysis]:
        """
        Analyze the entire node graph for optimization opportunities
        
        Returns:
            GraphAnalysis object or None if analysis fails
        """
        if not NUKE_AVAILABLE:
            logger.error("Cannot analyze graph: Nuke not available")
            return None
        
        try:
            all_nodes = nuke.allNodes(recurseGroups=True)
            
            # Basic statistics
            total_nodes = len(all_nodes)
            node_categories = self._categorize_nodes(all_nodes)
            
            # Connection analysis
            connections = self._analyze_all_connections(all_nodes)
            connection_count = len(connections)
            
            # Data flow analysis
            data_flow_paths = self._trace_data_flow_paths(all_nodes)
            
            # Performance analysis
            bottlenecks = self._identify_bottlenecks(all_nodes)
            optimization_opportunities = self._find_optimization_opportunities(all_nodes)
            
            # Complexity scoring
            complexity_score = self._calculate_complexity_score(all_nodes, connections)
            
            # Render order
            render_order = self._determine_render_order(all_nodes)
            
            return GraphAnalysis(
                total_nodes=total_nodes,
                node_categories=node_categories,
                connection_count=connection_count,
                data_flow_paths=data_flow_paths,
                bottlenecks=bottlenecks,
                optimization_opportunities=optimization_opportunities,
                complexity_score=complexity_score,
                render_order=render_order
            )
            
        except Exception as e:
            logger.error(f"Error analyzing graph: {e}")
            return None
    
    def _analyze_single_node(self, node) -> NodeAnalysis:
        """Perform detailed analysis of a single node"""
        name = node.name()
        class_name = node.Class()
        category = self._get_node_category(class_name)
        description = self._get_node_description(class_name)
        
        # Analyze connections
        input_connections = self._analyze_input_connections(node)
        output_connections = self._analyze_output_connections(node)
        
        # Extract parameters
        parameters = self._extract_node_parameters(node)
        
        # Performance analysis
        performance_impact = self._assess_performance_impact(node)
        
        # Generate suggestions
        optimization_suggestions = self._generate_optimization_suggestions(node)
        potential_issues = self._identify_potential_issues(node)
        
        # Determine data flow role
        data_flow_role = self._determine_data_flow_role(node)
        
        return NodeAnalysis(
            name=name,
            class_name=class_name,
            category=category,
            description=description,
            input_connections=input_connections,
            output_connections=output_connections,
            parameters=parameters,
            performance_impact=performance_impact,
            optimization_suggestions=optimization_suggestions,
            potential_issues=potential_issues,
            data_flow_role=data_flow_role
        )
    
    def _get_node_category(self, class_name: str) -> str:
        """Determine the category of a node based on its class"""
        for category, classes in self.node_categories.items():
            if class_name in classes:
                return category
        return 'other'
    
    def _get_node_description(self, class_name: str) -> str:
        """Get a description of what the node does"""
        descriptions = {
            'Read': 'Reads image sequences or single frames from disk',
            'Write': 'Writes image sequences or single frames to disk',
            'Merge2': 'Composites two or more images using various blend modes',
            'ColorCorrect': 'Adjusts color properties like lift, gamma, gain, and saturation',
            'Grade': 'Primary color correction tool for adjusting exposure and color balance',
            'Blur': 'Applies various types of blur effects to images',
            'Transform': 'Applies geometric transformations like translate, rotate, and scale',
            'Keyer': 'Extracts alpha mattes based on color or luminance values',
            'Viewer': 'Displays images in the viewer for review and analysis',
            'Constant': 'Generates solid color images',
            'Dot': 'Organizational node for routing connections without processing',
            'NoOp': 'Pass-through node that can hold expressions and metadata'
        }
        return descriptions.get(class_name, f'{class_name} node')
    
    def _analyze_input_connections(self, node) -> List[ConnectionInfo]:
        """Analyze all input connections to a node"""
        connections = []
        
        try:
            for i in range(node.inputs()):
                input_node = node.input(i)
                if input_node:
                    connection = self._create_connection_info(
                        input_node, node, 0, i
                    )
                    if connection:
                        connections.append(connection)
        except Exception as e:
            logger.warning(f"Error analyzing input connections for {node.name()}: {e}")
        
        return connections
    
    def _analyze_output_connections(self, node) -> List[ConnectionInfo]:
        """Analyze all output connections from a node"""
        connections = []
        
        try:
            for dependent in node.dependent():
                # Find which input this connection goes to
                for i in range(dependent.inputs()):
                    if dependent.input(i) == node:
                        connection = self._create_connection_info(
                            node, dependent, 0, i
                        )
                        if connection:
                            connections.append(connection)
                        break
        except Exception as e:
            logger.warning(f"Error analyzing output connections for {node.name()}: {e}")
        
        return connections
    
    def _create_connection_info(self, source_node, target_node, source_output: int, target_input: int) -> Optional[ConnectionInfo]:
        """Create connection information between two nodes"""
        try:
            # Determine connection type
            connection_type = self._determine_connection_type(target_node, target_input)
            
            # Determine data type
            data_type = self._determine_data_type(source_node)
            
            # Get channel information
            channels = self._get_connection_channels(source_node)
            
            # Get format information
            format_info = self._get_connection_format(source_node)
            
            return ConnectionInfo(
                source_node=source_node.name(),
                target_node=target_node.name(),
                source_output=source_output,
                target_input=target_input,
                connection_type=connection_type,
                data_type=data_type,
                channels=channels,
                format_info=format_info
            )
            
        except Exception as e:
            logger.warning(f"Error creating connection info: {e}")
            return None
    
    def _determine_connection_type(self, node, input_index: int) -> ConnectionType:
        """Determine the type of connection based on the target node and input"""
        class_name = node.Class()
        
        # Common patterns for different connection types
        if class_name in ['Merge2', 'Merge']:
            if input_index == 0:
                return ConnectionType.IMAGE  # A input
            elif input_index == 1:
                return ConnectionType.IMAGE  # B input
            elif input_index == 2:
                return ConnectionType.MASK   # Mask input
        
        elif class_name in ['Copy', 'Shuffle']:
            if input_index == 0:
                return ConnectionType.IMAGE
            else:
                return ConnectionType.AUXILIARY
        
        elif 'mask' in str(input_index).lower():
            return ConnectionType.MASK
        
        elif 'depth' in str(input_index).lower():
            return ConnectionType.DEPTH
        
        elif 'motion' in str(input_index).lower():
            return ConnectionType.MOTION
        
        return ConnectionType.IMAGE
    
    def _determine_data_type(self, node) -> DataType:
        """Determine the data type output by a node"""
        class_name = node.Class()
        
        if class_name in ['Read', 'Constant']:
            # Check channels knob if available
            if 'channels' in node.knobs():
                channels = node['channels'].value()
                if 'rgba' in channels.lower():
                    return DataType.RGBA
                elif 'rgb' in channels.lower():
                    return DataType.RGB
                elif 'alpha' in channels.lower():
                    return DataType.ALPHA
                elif 'depth' in channels.lower():
                    return DataType.DEPTH
        
        elif class_name in ['Keyer', 'Primatte']:
            return DataType.ALPHA
        
        elif 'depth' in class_name.lower():
            return DataType.DEPTH
        
        elif 'motion' in class_name.lower():
            return DataType.MOTION
        
        return DataType.RGBA  # Default assumption
    
    def _get_connection_channels(self, node) -> List[str]:
        """Get the channels available from a node"""
        try:
            if 'channels' in node.knobs():
                channels_value = node['channels'].value()
                if isinstance(channels_value, str):
                    return [channels_value]
                else:
                    return ['rgba']  # Default
            return ['rgba']
        except:
            return ['rgba']
    
    def _get_connection_format(self, node) -> Dict[str, Any]:
        """Get format information from a node"""
        try:
            if hasattr(node, 'format') and node.format():
                fmt = node.format()
                return {
                    'width': fmt.width(),
                    'height': fmt.height(),
                    'pixel_aspect': fmt.pixelAspect(),
                    'name': fmt.name()
                }
        except:
            pass
        
        return {'width': 'unknown', 'height': 'unknown', 'pixel_aspect': 1.0, 'name': 'unknown'}
    
    def _extract_node_parameters(self, node) -> Dict[str, Any]:
        """Extract important parameters from a node"""
        parameters = {}
        
        try:
            # Get all knobs
            for knob_name in node.knobs():
                knob = node[knob_name]
                
                # Skip certain knob types
                if knob.Class() in ['Tab_Knob', 'Text_Knob']:
                    continue
                
                try:
                    if knob.Class() == 'File_Knob':
                        parameters[knob_name] = knob.value()
                    elif knob.Class() == 'Enumeration_Knob':
                        parameters[knob_name] = {
                            'value': knob.value(),
                            'enum_name': knob.enumName(int(knob.value()))
                        }
                    elif knob.Class() in ['Double_Knob', 'Int_Knob']:
                        parameters[knob_name] = knob.value()
                    elif knob.Class() == 'Boolean_Knob':
                        parameters[knob_name] = bool(knob.value())
                    elif knob.Class() == 'String_Knob':
                        parameters[knob_name] = knob.value()
                    else:
                        parameters[knob_name] = str(knob.value())
                except:
                    parameters[knob_name] = 'error_reading_value'
                    
        except Exception as e:
            logger.warning(f"Error extracting parameters from {node.name()}: {e}")
        
        return parameters
    
    def _assess_performance_impact(self, node) -> str:
        """Assess the performance impact of a node"""
        class_name = node.Class()
        
        # High impact nodes
        high_impact = ['Blur', 'MotionBlur', 'ZDefocus', 'Convolve', 'Median', 'VectorBlur']
        if class_name in high_impact:
            return 'high'
        
        # Medium impact nodes
        medium_impact = ['ColorCorrect', 'Grade', 'Transform', 'CornerPin', 'Merge2']
        if class_name in medium_impact:
            return 'medium'
        
        # Low impact nodes
        low_impact = ['Dot', 'NoOp', 'Constant', 'Shuffle', 'Copy']
        if class_name in low_impact:
            return 'low'
        
        return 'medium'  # Default
    
    def _generate_optimization_suggestions(self, node) -> List[str]:
        """Generate optimization suggestions for a node"""
        suggestions = []
        class_name = node.Class()
        
        try:
            # Blur optimization
            if class_name == 'Blur':
                if 'size' in node.knobs():
                    size = node['size'].value()
                    if size > 50:
                        suggestions.append("Consider using a smaller blur size or multiple blur nodes for better performance")
                
                if 'quality' in node.knobs():
                    quality = node['quality'].value()
                    if quality > 15:
                        suggestions.append("High quality setting may impact performance - consider reducing if acceptable")
            
            # Transform optimization
            elif class_name == 'Transform':
                if 'filter' in node.knobs():
                    filter_type = node['filter'].enumName(int(node['filter'].value()))
                    if filter_type in ['cubic', 'keys']:
                        suggestions.append("Consider using 'impulse' or 'linear' filter for better performance")
            
            # Read node optimization
            elif class_name == 'Read':
                if 'file' in node.knobs():
                    file_path = node['file'].value()
                    if file_path.endswith('.exr'):
                        suggestions.append("EXR files can be slow - consider using proxy files for interactive work")
            
            # General suggestions
            if 'disable' in node.knobs() and not node['disable'].value():
                if len(node.dependent()) == 0:
                    suggestions.append("Node has no outputs - consider disabling if not needed")
            
        except Exception as e:
            logger.warning(f"Error generating suggestions for {node.name()}: {e}")
        
        return suggestions
    
    def _identify_potential_issues(self, node) -> List[str]:
        """Identify potential issues with a node"""
        issues = []
        
        try:
            # Check for errors
            if hasattr(node, 'hasError') and node.hasError():
                issues.append("Node has an error state")
            
            # Check for missing inputs
            for i in range(node.inputs()):
                if not node.input(i):
                    issues.append(f"Input {i} is not connected")
            
            # Check file nodes
            if node.Class() == 'Read':
                if 'file' in node.knobs():
                    file_path = node['file'].value()
                    if not file_path:
                        issues.append("No file specified")
                    elif '#' not in file_path and '%' not in file_path:
                        issues.append("File path may not support sequences")
            
            # Check for disabled nodes in critical paths
            if 'disable' in node.knobs() and node['disable'].value():
                if len(node.dependent()) > 0:
                    issues.append("Disabled node with active outputs")
            
        except Exception as e:
            logger.warning(f"Error identifying issues for {node.name()}: {e}")
        
        return issues
    
    def _determine_data_flow_role(self, node) -> str:
        """Determine the role of a node in the data flow"""
        class_name = node.Class()
        
        if class_name in ['Read', 'Constant']:
            return 'source'
        elif class_name in ['Write', 'Viewer']:
            return 'sink'
        elif class_name in ['Merge2', 'Merge', 'Plus', 'Multiply']:
            return 'compositor'
        elif class_name in ['ColorCorrect', 'Grade', 'Gamma']:
            return 'color_processor'
        elif class_name in ['Blur', 'Sharpen', 'Median']:
            return 'filter'
        elif class_name in ['Transform', 'CornerPin']:
            return 'transformer'
        elif class_name in ['Dot', 'NoOp']:
            return 'utility'
        else:
            return 'processor'
    
    def _categorize_nodes(self, nodes) -> Dict[str, int]:
        """Categorize all nodes and count them"""
        categories = {}
        
        for node in nodes:
            category = self._get_node_category(node.Class())
            categories[category] = categories.get(category, 0) + 1
        
        return categories
    
    def _analyze_all_connections(self, nodes) -> List[ConnectionInfo]:
        """Analyze all connections in the graph"""
        connections = []
        
        for node in nodes:
            node_connections = self._analyze_input_connections(node)
            connections.extend(node_connections)
        
        return connections
    
    def _trace_data_flow_paths(self, nodes) -> List[List[str]]:
        """Trace major data flow paths through the graph"""
        paths = []
        
        try:
            # Find source nodes (Read, Constant, etc.)
            source_nodes = [node for node in nodes if node.Class() in ['Read', 'Constant', 'CheckerBoard']]
            
            # Trace from each source to sinks
            for source in source_nodes:
                path = self._trace_path_from_node(source)
                if len(path) > 1:  # Only include paths with multiple nodes
                    paths.append(path)
        
        except Exception as e:
            logger.warning(f"Error tracing data flow paths: {e}")
        
        return paths
    
    def _trace_path_from_node(self, node, visited: Optional[Set] = None) -> List[str]:
        """Trace the path from a node to its outputs"""
        if visited is None:
            visited = set()
        
        if node.name() in visited:
            return [node.name()]
        
        visited.add(node.name())
        path = [node.name()]
        
        # Follow the primary output (first dependent)
        dependents = node.dependent()
        if dependents:
            next_path = self._trace_path_from_node(dependents[0], visited.copy())
            path.extend(next_path[1:])  # Skip the first node (current node)
        
        return path
    
    def _identify_bottlenecks(self, nodes) -> List[str]:
        """Identify potential performance bottlenecks"""
        bottlenecks = []
        
        for node in nodes:
            # High-impact nodes with many dependents
            if (self._assess_performance_impact(node) == 'high' and 
                len(node.dependent()) > 3):
                bottlenecks.append(f"{node.name()} - High impact node with many outputs")
            
            # Nodes with many inputs
            if node.inputs() > 5:
                bottlenecks.append(f"{node.name()} - Node with many inputs ({node.inputs()})")
        
        return bottlenecks
    
    def _find_optimization_opportunities(self, nodes) -> List[str]:
        """Find graph-level optimization opportunities"""
        opportunities = []
        
        # Look for redundant operations
        class_counts = {}
        for node in nodes:
            class_name = node.Class()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        for class_name, count in class_counts.items():
            if count > 5 and class_name in ['ColorCorrect', 'Grade']:
                opportunities.append(f"Many {class_name} nodes ({count}) - consider consolidating")
        
        # Look for long chains
        for node in nodes:
            if node.Class() == 'Dot':
                # Count consecutive dots
                dot_chain = self._count_consecutive_dots(node)
                if dot_chain > 3:
                    opportunities.append(f"Long chain of Dot nodes starting at {node.name()}")
        
        return opportunities
    
    def _count_consecutive_dots(self, node, count: int = 1) -> int:
        """Count consecutive Dot nodes in a chain"""
        dependents = node.dependent()
        if len(dependents) == 1 and dependents[0].Class() == 'Dot':
            return self._count_consecutive_dots(dependents[0], count + 1)
        return count
    
    def _calculate_complexity_score(self, nodes, connections) -> float:
        """Calculate a complexity score for the graph"""
        try:
            node_count = len(nodes)
            connection_count = len(connections)
            
            # Base complexity from node and connection counts
            base_score = (node_count * 0.1) + (connection_count * 0.05)
            
            # Add complexity for high-impact nodes
            high_impact_nodes = sum(1 for node in nodes if self._assess_performance_impact(node) == 'high')
            complexity_bonus = high_impact_nodes * 0.5
            
            # Add complexity for branching
            branching_nodes = sum(1 for node in nodes if len(node.dependent()) > 2)
            branching_bonus = branching_nodes * 0.3
            
            total_score = base_score + complexity_bonus + branching_bonus
            
            # Normalize to 0-10 scale
            return min(total_score, 10.0)
            
        except Exception as e:
            logger.warning(f"Error calculating complexity score: {e}")
            return 5.0  # Default medium complexity
    
    def _determine_render_order(self, nodes) -> List[str]:
        """Determine the optimal render order for nodes"""
        try:
            # Simple topological sort based on dependencies
            visited = set()
            order = []
            
            def visit(node):
                if node.name() in visited:
                    return
                visited.add(node.name())
                
                # Visit all inputs first
                for i in range(node.inputs()):
                    input_node = node.input(i)
                    if input_node:
                        visit(input_node)
                
                order.append(node.name())
            
            # Start with output nodes (Write, Viewer)
            output_nodes = [node for node in nodes if node.Class() in ['Write', 'Viewer']]
            for node in output_nodes:
                visit(node)
            
            # Visit any remaining nodes
            for node in nodes:
                if node.name() not in visited:
                    visit(node)
            
            return order
            
        except Exception as e:
            logger.warning(f"Error determining render order: {e}")
            return [node.name() for node in nodes]