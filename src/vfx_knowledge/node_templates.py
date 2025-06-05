"""
Node Templates Manager

Pre-built node combinations and setups for common VFX operations,
providing ready-to-use templates for efficient workflow creation.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Categories of node templates"""
    KEYING = "keying"
    COLOR_CORRECTION = "color_correction"
    COMPOSITING = "compositing"
    EFFECTS = "effects"
    UTILITY = "utility"
    CG_INTEGRATION = "cg_integration"
    CLEANUP = "cleanup"
    TRACKING = "tracking"


class TemplateComplexity(Enum):
    """Complexity levels for templates"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class NodeTemplate:
    """A single node in a template"""
    id: str
    node_type: str
    name: str
    position: Tuple[int, int]
    parameters: Dict[str, Any]
    notes: str


@dataclass
class ConnectionTemplate:
    """A connection between nodes in a template"""
    source_id: str
    target_id: str
    input_index: int
    output_index: int = 0


@dataclass
class Template:
    """A complete node template"""
    id: str
    name: str
    category: TemplateCategory
    complexity: TemplateComplexity
    description: str
    use_cases: List[str]
    nodes: List[NodeTemplate]
    connections: List[ConnectionTemplate]
    inputs: List[str]  # Node IDs that accept external inputs
    outputs: List[str]  # Node IDs that provide outputs
    parameters: Dict[str, Any]  # Template-level parameters
    tips: List[str]
    requirements: List[str]
    variations: List[str]


@dataclass
class TemplateInstance:
    """An instantiated template with actual node names"""
    template_id: str
    instance_id: str
    node_mapping: Dict[str, str]  # template_id -> actual_node_name
    created_nodes: List[str]
    customizations: Dict[str, Any]


class NodeTemplateManager:
    """
    Manages pre-built node templates for common VFX operations.
    """
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize the node template manager
        
        Args:
            data_directory: Directory containing template data files
        """
        self.data_directory = data_directory
        self.templates: Dict[str, Template] = {}
        self.instances: Dict[str, TemplateInstance] = {}
        
        # Initialize built-in templates
        self._initialize_builtin_templates()
        
        # Load additional templates from files
        if data_directory:
            self._load_templates_from_files()
    
    def _initialize_builtin_templates(self):
        """Initialize built-in node templates"""
        
        # Basic Keying Template
        basic_keying = Template(
            id="basic_keying",
            name="Basic Green Screen Key",
            category=TemplateCategory.KEYING,
            complexity=TemplateComplexity.SIMPLE,
            description="Simple green screen keying setup with edge cleanup",
            use_cases=[
                "Basic green screen removal",
                "Clean background plates",
                "Simple compositing tasks"
            ],
            nodes=[
                NodeTemplate(
                    id="source",
                    node_type="Read",
                    name="GS_Source",
                    position=(0, 0),
                    parameters={"file": "", "channels": "rgba"},
                    notes="Green screen source footage"
                ),
                NodeTemplate(
                    id="keyer",
                    node_type="Keyer",
                    name="Primary_Key",
                    position=(0, 100),
                    parameters={
                        "operation": "luminance key",
                        "range": [0.5, 1.0],
                        "tolerance": 0.1
                    },
                    notes="Primary keying operation"
                ),
                NodeTemplate(
                    id="erode",
                    node_type="FilterErode",
                    name="Edge_Cleanup",
                    position=(0, 200),
                    parameters={"size": -0.5, "filter": "gaussian"},
                    notes="Clean up key edges"
                ),
                NodeTemplate(
                    id="blur",
                    node_type="Blur",
                    name="Edge_Soften",
                    position=(0, 300),
                    parameters={"size": 1.0, "filter": "gaussian"},
                    notes="Soften key edges"
                ),
                NodeTemplate(
                    id="premult",
                    node_type="Premult",
                    name="Final_Premult",
                    position=(0, 400),
                    parameters={},
                    notes="Premultiply for compositing"
                )
            ],
            connections=[
                ConnectionTemplate("source", "keyer", 0),
                ConnectionTemplate("keyer", "erode", 0),
                ConnectionTemplate("erode", "blur", 0),
                ConnectionTemplate("source", "premult", 0),
                ConnectionTemplate("blur", "premult", 1)
            ],
            inputs=["source"],
            outputs=["premult"],
            parameters={
                "key_tolerance": 0.1,
                "edge_size": -0.5,
                "blur_amount": 1.0
            },
            tips=[
                "Start with conservative key settings",
                "Adjust edge cleanup based on source quality",
                "Check result against different backgrounds"
            ],
            requirements=["Green screen footage with good separation"],
            variations=["Blue screen version", "Luminance key version"]
        )
        
        # Advanced Keying Template
        advanced_keying = Template(
            id="advanced_keying",
            name="Professional Keying Setup",
            category=TemplateCategory.KEYING,
            complexity=TemplateComplexity.COMPLEX,
            description="Professional keying workflow with spill suppression and edge refinement",
            use_cases=[
                "High-end keying work",
                "Complex hair and transparency",
                "Professional compositing"
            ],
            nodes=[
                NodeTemplate(
                    id="source",
                    node_type="Read",
                    name="GS_Source",
                    position=(0, 0),
                    parameters={"file": "", "channels": "rgba"},
                    notes="Green screen source"
                ),
                NodeTemplate(
                    id="primary_key",
                    node_type="Keyer",
                    name="Primary_Key",
                    position=(0, 100),
                    parameters={"operation": "luminance key"},
                    notes="Conservative primary key"
                ),
                NodeTemplate(
                    id="secondary_key",
                    node_type="Keyer",
                    name="Secondary_Key",
                    position=(200, 100),
                    parameters={"operation": "luminance key"},
                    notes="Aggressive secondary key"
                ),
                NodeTemplate(
                    id="key_mix",
                    node_type="Merge2",
                    name="Key_Combine",
                    position=(100, 200),
                    parameters={"operation": "max"},
                    notes="Combine key passes"
                ),
                NodeTemplate(
                    id="edge_erode",
                    node_type="FilterErode",
                    name="Edge_Erode",
                    position=(100, 300),
                    parameters={"size": -1.0},
                    notes="Erode key edges"
                ),
                NodeTemplate(
                    id="edge_blur",
                    node_type="Blur",
                    name="Edge_Blur",
                    position=(100, 400),
                    parameters={"size": 2.0},
                    notes="Blur key edges"
                ),
                NodeTemplate(
                    id="spill_suppress",
                    node_type="HueCorrect",
                    name="Spill_Suppress",
                    position=(300, 200),
                    parameters={"saturation": 0.0},
                    notes="Remove green spill"
                ),
                NodeTemplate(
                    id="final_premult",
                    node_type="Premult",
                    name="Final_Output",
                    position=(200, 500),
                    parameters={},
                    notes="Final premultiplied output"
                )
            ],
            connections=[
                ConnectionTemplate("source", "primary_key", 0),
                ConnectionTemplate("source", "secondary_key", 0),
                ConnectionTemplate("primary_key", "key_mix", 0),
                ConnectionTemplate("secondary_key", "key_mix", 1),
                ConnectionTemplate("key_mix", "edge_erode", 0),
                ConnectionTemplate("edge_erode", "edge_blur", 0),
                ConnectionTemplate("source", "spill_suppress", 0),
                ConnectionTemplate("spill_suppress", "final_premult", 0),
                ConnectionTemplate("edge_blur", "final_premult", 1)
            ],
            inputs=["source"],
            outputs=["final_premult"],
            parameters={
                "primary_tolerance": 0.05,
                "secondary_tolerance": 0.15,
                "edge_treatment": -1.0,
                "spill_amount": 0.0
            },
            tips=[
                "Use two-pass keying for complex subjects",
                "Adjust spill suppression carefully",
                "Test with various background colors"
            ],
            requirements=["High-quality green screen footage"],
            variations=["Hair-specific version", "Motion blur preservation"]
        )
        
        # Color Correction Template
        color_correction = Template(
            id="color_correction_stack",
            name="Professional Color Correction",
            category=TemplateCategory.COLOR_CORRECTION,
            complexity=TemplateComplexity.MODERATE,
            description="Complete color correction workflow with primary and secondary adjustments",
            use_cases=[
                "Shot matching",
                "Color grading",
                "Exposure correction",
                "Creative color work"
            ],
            nodes=[
                NodeTemplate(
                    id="source",
                    node_type="Read",
                    name="Source_Plate",
                    position=(0, 0),
                    parameters={"file": ""},
                    notes="Source footage"
                ),
                NodeTemplate(
                    id="primary_grade",
                    node_type="Grade",
                    name="Primary_Grade",
                    position=(0, 100),
                    parameters={
                        "blackpoint": [0.0, 0.0, 0.0, 0.0],
                        "whitepoint": [1.0, 1.0, 1.0, 1.0]
                    },
                    notes="Primary color correction"
                ),
                NodeTemplate(
                    id="secondary_cc",
                    node_type="ColorCorrect",
                    name="Secondary_CC",
                    position=(0, 200),
                    parameters={
                        "saturation": 1.0,
                        "contrast": 1.0,
                        "gamma": [1.0, 1.0, 1.0, 1.0]
                    },
                    notes="Secondary adjustments"
                ),
                NodeTemplate(
                    id="final_gamma",
                    node_type="Gamma",
                    name="Final_Gamma",
                    position=(0, 300),
                    parameters={"value": [1.0, 1.0, 1.0, 1.0]},
                    notes="Final gamma adjustment"
                ),
                NodeTemplate(
                    id="clamp",
                    node_type="Clamp",
                    name="Output_Clamp",
                    position=(0, 400),
                    parameters={"minimum": 0.0, "maximum": 1.0},
                    notes="Clamp output values"
                )
            ],
            connections=[
                ConnectionTemplate("source", "primary_grade", 0),
                ConnectionTemplate("primary_grade", "secondary_cc", 0),
                ConnectionTemplate("secondary_cc", "final_gamma", 0),
                ConnectionTemplate("final_gamma", "clamp", 0)
            ],
            inputs=["source"],
            outputs=["clamp"],
            parameters={
                "exposure_adjust": 0.0,
                "contrast_boost": 1.0,
                "saturation_level": 1.0
            },
            tips=[
                "Start with exposure and contrast",
                "Use secondary CC for creative adjustments",
                "Always clamp final output"
            ],
            requirements=["Properly exposed source material"],
            variations=["HDR version", "Log color space version"]
        )
        
        # CG Integration Template
        cg_integration = Template(
            id="cg_integration_basic",
            name="Basic CG Integration",
            category=TemplateCategory.CG_INTEGRATION,
            complexity=TemplateComplexity.MODERATE,
            description="Standard CG element integration with shadows and color matching",
            use_cases=[
                "Adding CG objects to plates",
                "Vehicle integration",
                "Product placement",
                "Environment extensions"
            ],
            nodes=[
                NodeTemplate(
                    id="bg_plate",
                    node_type="Read",
                    name="BG_Plate",
                    position=(0, 0),
                    parameters={"file": ""},
                    notes="Background live action plate"
                ),
                NodeTemplate(
                    id="cg_beauty",
                    node_type="Read",
                    name="CG_Beauty",
                    position=(200, 0),
                    parameters={"file": "", "channels": "rgba"},
                    notes="CG beauty pass"
                ),
                NodeTemplate(
                    id="cg_shadow",
                    node_type="Read",
                    name="CG_Shadow",
                    position=(400, 0),
                    parameters={"file": "", "channels": "rgba"},
                    notes="CG shadow pass"
                ),
                NodeTemplate(
                    id="shadow_comp",
                    node_type="Merge2",
                    name="Shadow_Comp",
                    position=(200, 100),
                    parameters={"operation": "multiply", "mix": 0.8},
                    notes="Composite shadows"
                ),
                NodeTemplate(
                    id="cg_grade",
                    node_type="ColorCorrect",
                    name="CG_Grade",
                    position=(200, 200),
                    parameters={"gain": [1.0, 1.0, 1.0, 1.0]},
                    notes="Match CG to plate"
                ),
                NodeTemplate(
                    id="final_comp",
                    node_type="Merge2",
                    name="Final_Comp",
                    position=(200, 300),
                    parameters={"operation": "over"},
                    notes="Final composite"
                )
            ],
            connections=[
                ConnectionTemplate("bg_plate", "shadow_comp", 0),
                ConnectionTemplate("cg_shadow", "shadow_comp", 1),
                ConnectionTemplate("cg_beauty", "cg_grade", 0),
                ConnectionTemplate("shadow_comp", "final_comp", 0),
                ConnectionTemplate("cg_grade", "final_comp", 1)
            ],
            inputs=["bg_plate", "cg_beauty", "cg_shadow"],
            outputs=["final_comp"],
            parameters={
                "shadow_density": 0.8,
                "cg_exposure": 0.0,
                "integration_quality": "high"
            },
            tips=[
                "Match lighting direction carefully",
                "Adjust shadow density for realism",
                "Consider atmospheric perspective"
            ],
            requirements=["Separated CG passes", "Clean background plate"],
            variations=["Multi-pass version", "Reflection integration"]
        )
        
        # Cleanup Template
        cleanup_template = Template(
            id="basic_cleanup",
            name="Basic Cleanup Setup",
            category=TemplateCategory.CLEANUP,
            complexity=TemplateComplexity.SIMPLE,
            description="Standard cleanup workflow with paint and tracking",
            use_cases=[
                "Wire removal",
                "Rig removal",
                "Unwanted object cleanup",
                "Stabilization"
            ],
            nodes=[
                NodeTemplate(
                    id="source",
                    node_type="Read",
                    name="Source_Plate",
                    position=(0, 0),
                    parameters={"file": ""},
                    notes="Source footage to clean"
                ),
                NodeTemplate(
                    id="tracker",
                    node_type="Tracker",
                    name="Stabilize_Track",
                    position=(0, 100),
                    parameters={"reference_frame": 1},
                    notes="Tracking for stabilization"
                ),
                NodeTemplate(
                    id="transform",
                    node_type="Transform",
                    name="Stabilize_Transform",
                    position=(0, 200),
                    parameters={},
                    notes="Apply stabilization"
                ),
                NodeTemplate(
                    id="rotopaint",
                    node_type="RotoPaint",
                    name="Cleanup_Paint",
                    position=(0, 300),
                    parameters={},
                    notes="Paint out unwanted elements"
                ),
                NodeTemplate(
                    id="reverse_transform",
                    node_type="Transform",
                    name="Reverse_Stabilize",
                    position=(0, 400),
                    parameters={},
                    notes="Remove stabilization"
                )
            ],
            connections=[
                ConnectionTemplate("source", "tracker", 0),
                ConnectionTemplate("source", "transform", 0),
                ConnectionTemplate("transform", "rotopaint", 0),
                ConnectionTemplate("rotopaint", "reverse_transform", 0)
            ],
            inputs=["source"],
            outputs=["reverse_transform"],
            parameters={
                "stabilize_strength": 1.0,
                "paint_method": "clone"
            },
            tips=[
                "Stabilize before painting for easier work",
                "Use multiple paint layers for complex cleanup",
                "Always reverse stabilization at the end"
            ],
            requirements=["Trackable features in footage"],
            variations=["3D tracking version", "Planar tracking version"]
        )
        
        # Add templates to dictionary
        templates = [
            basic_keying, advanced_keying, color_correction,
            cg_integration, cleanup_template
        ]
        
        for template in templates:
            self.templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get a template by ID"""
        return self.templates.get(template_id)
    
    def search_templates(self, query: str, category: Optional[TemplateCategory] = None,
                        complexity: Optional[TemplateComplexity] = None) -> List[Template]:
        """
        Search templates by query, category, and complexity
        
        Args:
            query: Search query
            category: Filter by category
            complexity: Filter by complexity
            
        Returns:
            List of matching templates
        """
        results = []
        query_lower = query.lower() if query else ""
        
        for template in self.templates.values():
            # Category filter
            if category and template.category != category:
                continue
            
            # Complexity filter
            if complexity and template.complexity != complexity:
                continue
            
            # Text search
            if query_lower:
                searchable_text = (
                    template.name.lower() + " " +
                    template.description.lower() + " " +
                    " ".join(template.use_cases).lower()
                )
                if query_lower not in searchable_text:
                    continue
            
            results.append(template)
        
        return results
    
    def get_templates_by_category(self, category: TemplateCategory) -> List[Template]:
        """Get all templates in a category"""
        return [t for t in self.templates.values() if t.category == category]
    
    def instantiate_template(self, template_id: str, 
                           customizations: Optional[Dict[str, Any]] = None) -> Optional[TemplateInstance]:
        """
        Create an instance of a template with actual nodes
        
        Args:
            template_id: ID of template to instantiate
            customizations: Custom parameters and settings
            
        Returns:
            TemplateInstance or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        try:
            # Handle Nuke import gracefully
            try:
                import nuke
                NUKE_AVAILABLE = True
            except ImportError:
                NUKE_AVAILABLE = False
                logger.warning("Nuke not available - template instantiation limited")
                return None
            
            if not NUKE_AVAILABLE:
                return None
            
            customizations = customizations or {}
            instance_id = f"{template_id}_{int(time.time())}"
            node_mapping = {}
            created_nodes = []
            
            # Create nodes
            for node_template in template.nodes:
                # Apply customizations
                node_params = node_template.parameters.copy()
                custom_params = customizations.get(node_template.id, {})
                node_params.update(custom_params)
                
                # Create the node
                node = nuke.createNode(node_template.node_type)
                node.setName(node_template.name)
                node.setXYpos(node_template.position[0], node_template.position[1])
                
                # Set parameters
                for param_name, param_value in node_params.items():
                    if param_name in node.knobs():
                        try:
                            node[param_name].setValue(param_value)
                        except Exception as e:
                            logger.warning(f"Could not set parameter {param_name}: {e}")
                
                # Add note if provided
                if node_template.notes and 'note_font_size' in node.knobs():
                    node['label'].setValue(node_template.notes)
                
                node_mapping[node_template.id] = node.name()
                created_nodes.append(node.name())
            
            # Create connections
            for conn in template.connections:
                try:
                    source_node = nuke.toNode(node_mapping[conn.source_id])
                    target_node = nuke.toNode(node_mapping[conn.target_id])
                    
                    if source_node and target_node:
                        target_node.setInput(conn.input_index, source_node)
                except Exception as e:
                    logger.warning(f"Could not create connection: {e}")
            
            # Create instance record
            instance = TemplateInstance(
                template_id=template_id,
                instance_id=instance_id,
                node_mapping=node_mapping,
                created_nodes=created_nodes,
                customizations=customizations
            )
            
            self.instances[instance_id] = instance
            
            logger.info(f"Template {template_id} instantiated as {instance_id}")
            return instance
            
        except Exception as e:
            logger.error(f"Error instantiating template: {e}")
            return None
    
    def delete_instance(self, instance_id: str) -> bool:
        """
        Delete a template instance and its nodes
        
        Args:
            instance_id: ID of instance to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        try:
            # Handle Nuke import gracefully
            try:
                import nuke
                NUKE_AVAILABLE = True
            except ImportError:
                NUKE_AVAILABLE = False
                return False
            
            if not NUKE_AVAILABLE:
                return False
            
            # Delete nodes
            for node_name in instance.created_nodes:
                node = nuke.toNode(node_name)
                if node:
                    nuke.delete(node)
            
            # Remove instance record
            del self.instances[instance_id]
            
            logger.info(f"Template instance {instance_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template instance: {e}")
            return False
    
    def get_instance(self, instance_id: str) -> Optional[TemplateInstance]:
        """Get a template instance by ID"""
        return self.instances.get(instance_id)
    
    def list_instances(self) -> List[TemplateInstance]:
        """Get all template instances"""
        return list(self.instances.values())
    
    def export_template(self, template_id: str, file_path: str) -> bool:
        """
        Export a template to a JSON file
        
        Args:
            template_id: ID of template to export
            file_path: Path to save the file
            
        Returns:
            True if export was successful, False otherwise
        """
        template = self.get_template(template_id)
        if not template:
            return False
        
        try:
            template_data = asdict(template)
            
            # Convert enums to strings
            template_data['category'] = template.category.value
            template_data['complexity'] = template.complexity.value
            
            with open(file_path, 'w') as f:
                json.dump({'templates': [template_data]}, f, indent=2)
            
            logger.info(f"Template exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting template: {e}")
            return False
    
    def _load_templates_from_files(self):
        """Load templates from JSON files"""
        try:
            from pathlib import Path
            
            data_dir = Path(self.data_directory)
            if not data_dir.exists():
                return
            
            for file_path in data_dir.glob("*_templates.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'templates' in data:
                        for template_data in data['templates']:
                            template = self._deserialize_template(template_data)
                            if template:
                                self.templates[template.id] = template
                                
                except Exception as e:
                    logger.error(f"Error loading template file {file_path}: {e}")
            
            logger.info(f"Loaded {len(self.templates)} templates")
            
        except Exception as e:
            logger.error(f"Error loading templates from files: {e}")
    
    def _deserialize_template(self, data: Dict[str, Any]) -> Optional[Template]:
        """Deserialize template from dictionary"""
        try:
            # Convert enum strings back to enums
            data['category'] = TemplateCategory(data['category'])
            data['complexity'] = TemplateComplexity(data['complexity'])
            
            # Convert nodes
            nodes = []
            for node_data in data['nodes']:
                node = NodeTemplate(**node_data)
                nodes.append(node)
            data['nodes'] = nodes
            
            # Convert connections
            connections = []
            for conn_data in data['connections']:
                conn = ConnectionTemplate(**conn_data)
                connections.append(conn)
            data['connections'] = connections
            
            return Template(**data)
            
        except Exception as e:
            logger.error(f"Error deserializing template: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get template manager statistics"""
        stats = {
            'total_templates': len(self.templates),
            'total_instances': len(self.instances),
            'categories': {},
            'complexity_distribution': {}
        }
        
        # Calculate category distribution
        for category in TemplateCategory:
            count = len([t for t in self.templates.values() if t.category == category])
            stats['categories'][category.value] = count
        
        # Calculate complexity distribution
        for complexity in TemplateComplexity:
            count = len([t for t in self.templates.values() if t.complexity == complexity])
            stats['complexity_distribution'][complexity.value] = count
        
        return stats