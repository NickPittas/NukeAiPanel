"""
Workflow Database

Manages common VFX workflows and patterns, providing structured knowledge
about industry-standard compositing approaches and techniques.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowCategory(Enum):
    """Categories of VFX workflows"""
    COMPOSITING = "compositing"
    KEYING = "keying"
    COLOR = "color"
    TRACKING = "tracking"
    CLEANUP = "cleanup"
    CG_INTEGRATION = "cg_integration"
    EFFECTS = "effects"
    FINISHING = "finishing"


class ComplexityLevel(Enum):
    """Complexity levels for workflows"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    step_number: int
    title: str
    description: str
    node_type: str
    parameters: Dict[str, Any]
    connections: List[Tuple[str, int]]  # (source_step_id, input_index)
    notes: List[str]
    alternatives: List[str]


@dataclass
class Workflow:
    """A complete VFX workflow"""
    id: str
    name: str
    category: WorkflowCategory
    complexity: ComplexityLevel
    description: str
    use_cases: List[str]
    prerequisites: List[str]
    steps: List[WorkflowStep]
    tips: List[str]
    common_issues: List[str]
    variations: List[str]
    estimated_time: str
    quality_checkpoints: List[str]


@dataclass
class WorkflowTemplate:
    """Template for creating workflows"""
    template_id: str
    name: str
    category: WorkflowCategory
    node_sequence: List[str]
    default_parameters: Dict[str, Dict[str, Any]]
    connection_pattern: List[Tuple[int, int, int]]  # (source_index, target_index, input_index)
    customization_points: List[str]


class WorkflowDatabase:
    """
    Database of VFX workflows and patterns with search and recommendation capabilities.
    """
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize the workflow database
        
        Args:
            data_directory: Directory containing workflow data files
        """
        self.data_directory = Path(data_directory) if data_directory else Path("data/workflows")
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.categories: Dict[WorkflowCategory, List[str]] = {}
        
        # Initialize with built-in workflows
        self._initialize_builtin_workflows()
        
        # Load additional workflows from data directory
        self._load_workflows_from_files()
    
    def _initialize_builtin_workflows(self):
        """Initialize built-in workflows"""
        
        # Basic Compositing Workflow
        basic_comp = Workflow(
            id="basic_compositing",
            name="Basic Compositing",
            category=WorkflowCategory.COMPOSITING,
            complexity=ComplexityLevel.BEGINNER,
            description="Standard two-layer compositing with background and foreground elements",
            use_cases=[
                "Simple over composites",
                "Adding elements to backgrounds",
                "Basic layer blending"
            ],
            prerequisites=["Understanding of alpha channels", "Basic Nuke navigation"],
            steps=[
                WorkflowStep(
                    step_number=1,
                    title="Load Background",
                    description="Load the background plate or element",
                    node_type="Read",
                    parameters={"file": "", "first": 1, "last": 100},
                    connections=[],
                    notes=["Ensure correct frame range", "Check color space"],
                    alternatives=["Constant node for solid colors"]
                ),
                WorkflowStep(
                    step_number=2,
                    title="Load Foreground",
                    description="Load the foreground element with alpha",
                    node_type="Read",
                    parameters={"file": "", "channels": "rgba"},
                    connections=[],
                    notes=["Verify alpha channel presence", "Check premultiplication"],
                    alternatives=["Generated elements", "Keyed footage"]
                ),
                WorkflowStep(
                    step_number=3,
                    title="Composite Layers",
                    description="Merge foreground over background",
                    node_type="Merge2",
                    parameters={"operation": "over", "mix": 1.0},
                    connections=[("step_1", 0), ("step_2", 1)],
                    notes=["Over operation respects alpha", "Adjust mix for transparency"],
                    alternatives=["Plus", "Screen", "Multiply operations"]
                ),
                WorkflowStep(
                    step_number=4,
                    title="Output",
                    description="Connect to viewer or write node",
                    node_type="Viewer",
                    parameters={},
                    connections=[("step_3", 0)],
                    notes=["Check final result", "Verify edge quality"],
                    alternatives=["Write node for rendering"]
                )
            ],
            tips=[
                "Always check alpha channels in the viewer",
                "Use premultiplication when working with CG elements",
                "Consider edge treatment for better integration"
            ],
            common_issues=[
                "Black edges from unpremultiplied alpha",
                "Color shifts from incorrect color spaces",
                "Aliasing from poor edge quality"
            ],
            variations=[
                "Multi-layer compositing",
                "Additive compositing",
                "Screen compositing"
            ],
            estimated_time="5-10 minutes",
            quality_checkpoints=[
                "Clean alpha edges",
                "Proper color integration",
                "No artifacts or halos"
            ]
        )
        
        # Advanced Keying Workflow
        advanced_keying = Workflow(
            id="advanced_keying",
            name="Advanced Green Screen Keying",
            category=WorkflowCategory.KEYING,
            complexity=ComplexityLevel.ADVANCED,
            description="Professional green screen keying with edge refinement and spill suppression",
            use_cases=[
                "Professional green screen removal",
                "Complex keying with hair detail",
                "Motion blur preservation"
            ],
            prerequisites=[
                "Understanding of keying principles",
                "Knowledge of edge treatment",
                "Color theory basics"
            ],
            steps=[
                WorkflowStep(
                    step_number=1,
                    title="Source Analysis",
                    description="Analyze the green screen footage",
                    node_type="Read",
                    parameters={"file": "", "channels": "rgba"},
                    connections=[],
                    notes=["Check for even lighting", "Identify problem areas"],
                    alternatives=["Multiple angle analysis"]
                ),
                WorkflowStep(
                    step_number=2,
                    title="Primary Key",
                    description="Create initial key with Keyer node",
                    node_type="Keyer",
                    parameters={"operation": "luminance key", "range": [0.5, 1.0]},
                    connections=[("step_1", 0)],
                    notes=["Start conservative", "Focus on core areas"],
                    alternatives=["Primatte", "IBKColour"]
                ),
                WorkflowStep(
                    step_number=3,
                    title="Edge Refinement",
                    description="Refine edges with erosion and blur",
                    node_type="FilterErode",
                    parameters={"size": -0.5, "filter": "gaussian"},
                    connections=[("step_2", 0)],
                    notes=["Negative values erode", "Preserve fine detail"],
                    alternatives=["Dilate for expansion"]
                ),
                WorkflowStep(
                    step_number=4,
                    title="Edge Softening",
                    description="Soften edges with controlled blur",
                    node_type="Blur",
                    parameters={"size": 1.0, "filter": "gaussian"},
                    connections=[("step_3", 0)],
                    notes=["Match original edge softness", "Avoid over-blurring"],
                    alternatives=["Defocus for depth-based blur"]
                ),
                WorkflowStep(
                    step_number=5,
                    title="Spill Suppression",
                    description="Remove green spill from subject",
                    node_type="HueCorrect",
                    parameters={"saturation": 0.0, "hue_range": "green"},
                    connections=[("step_1", 0)],
                    notes=["Target green hues only", "Preserve skin tones"],
                    alternatives=["Despill node", "ColorCorrect"]
                ),
                WorkflowStep(
                    step_number=6,
                    title="Final Composite",
                    description="Premultiply and composite final result",
                    node_type="Premult",
                    parameters={},
                    connections=[("step_5", 0), ("step_4", 1)],
                    notes=["Ensures proper edge blending", "Check for artifacts"],
                    alternatives=["Unpremult if needed"]
                )
            ],
            tips=[
                "Always work in linear color space for keying",
                "Use multiple keying passes for complex subjects",
                "Consider light wrap for better integration",
                "Test with different backgrounds"
            ],
            common_issues=[
                "Green spill on subject",
                "Loss of fine detail like hair",
                "Inconsistent edge quality",
                "Motion blur artifacts"
            ],
            variations=[
                "Blue screen keying",
                "Difference keying",
                "Luminance keying",
                "Multi-pass keying"
            ],
            estimated_time="30-60 minutes",
            quality_checkpoints=[
                "Clean matte with no holes",
                "Natural edge transition",
                "No visible spill",
                "Preserved fine detail"
            ]
        )
        
        # CG Integration Workflow
        cg_integration = Workflow(
            id="cg_integration",
            name="CG Element Integration",
            category=WorkflowCategory.CG_INTEGRATION,
            complexity=ComplexityLevel.INTERMEDIATE,
            description="Integrate CG renders with live action plates using multiple passes",
            use_cases=[
                "Adding CG objects to live action",
                "Vehicle integration",
                "Creature compositing",
                "Environment extensions"
            ],
            prerequisites=[
                "Understanding of render passes",
                "Knowledge of lighting principles",
                "Basic color correction skills"
            ],
            steps=[
                WorkflowStep(
                    step_number=1,
                    title="Load Beauty Pass",
                    description="Load the main CG beauty render",
                    node_type="Read",
                    parameters={"file": "", "channels": "rgba"},
                    connections=[],
                    notes=["Check for proper alpha", "Verify color space"],
                    alternatives=["Combine separate RGB and alpha"]
                ),
                WorkflowStep(
                    step_number=2,
                    title="Load Background Plate",
                    description="Load the live action background",
                    node_type="Read",
                    parameters={"file": "", "channels": "rgb"},
                    connections=[],
                    notes=["Match frame range", "Check resolution"],
                    alternatives=["Environment matte painting"]
                ),
                WorkflowStep(
                    step_number=3,
                    title="Load Shadow Pass",
                    description="Load CG shadow pass for ground interaction",
                    node_type="Read",
                    parameters={"file": "", "channels": "rgba"},
                    connections=[],
                    notes=["Shadows should be in alpha", "Check density"],
                    alternatives=["Generate shadows in comp"]
                ),
                WorkflowStep(
                    step_number=4,
                    title="Composite Shadows",
                    description="Multiply shadows onto background",
                    node_type="Merge2",
                    parameters={"operation": "multiply", "mix": 0.8},
                    connections=[("step_2", 0), ("step_3", 1)],
                    notes=["Adjust mix for shadow density", "Use alpha as mask"],
                    alternatives=["Color burn for darker shadows"]
                ),
                WorkflowStep(
                    step_number=5,
                    title="Color Match CG",
                    description="Match CG lighting to plate",
                    node_type="ColorCorrect",
                    parameters={"gain": [1.0, 1.0, 1.0, 1.0], "gamma": [1.0, 1.0, 1.0, 1.0]},
                    connections=[("step_1", 0)],
                    notes=["Match highlights and shadows", "Preserve material properties"],
                    alternatives=["Grade node for more control"]
                ),
                WorkflowStep(
                    step_number=6,
                    title="Final Composite",
                    description="Composite color-matched CG over shadowed background",
                    node_type="Merge2",
                    parameters={"operation": "over", "mix": 1.0},
                    connections=[("step_4", 0), ("step_5", 1)],
                    notes=["Check edge integration", "Verify alpha blending"],
                    alternatives=["Plus for additive elements"]
                )
            ],
            tips=[
                "Use reference spheres for lighting matching",
                "Consider atmospheric perspective for distant objects",
                "Add subtle motion blur for realism",
                "Use depth passes for atmospheric effects"
            ],
            common_issues=[
                "Lighting mismatch between CG and plate",
                "Unrealistic shadow integration",
                "Color space inconsistencies",
                "Missing atmospheric effects"
            ],
            variations=[
                "Multi-pass beauty reconstruction",
                "Reflection pass integration",
                "Subsurface scattering compositing",
                "Volumetric effects integration"
            ],
            estimated_time="45-90 minutes",
            quality_checkpoints=[
                "Realistic lighting integration",
                "Convincing shadow interaction",
                "Proper color matching",
                "Natural atmospheric effects"
            ]
        )
        
        # Add workflows to database
        self.workflows[basic_comp.id] = basic_comp
        self.workflows[advanced_keying.id] = advanced_keying
        self.workflows[cg_integration.id] = cg_integration
        
        # Update categories
        self._update_categories()
    
    def _load_workflows_from_files(self):
        """Load workflows from JSON files in data directory"""
        try:
            if not self.data_directory.exists():
                logger.info(f"Workflow data directory not found: {self.data_directory}")
                return
            
            for file_path in self.data_directory.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'workflows' in data:
                        for workflow_data in data['workflows']:
                            workflow = self._deserialize_workflow(workflow_data)
                            if workflow:
                                self.workflows[workflow.id] = workflow
                    
                    if 'templates' in data:
                        for template_data in data['templates']:
                            template = self._deserialize_template(template_data)
                            if template:
                                self.templates[template.template_id] = template
                                
                except Exception as e:
                    logger.error(f"Error loading workflow file {file_path}: {e}")
            
            self._update_categories()
            logger.info(f"Loaded {len(self.workflows)} workflows from files")
            
        except Exception as e:
            logger.error(f"Error loading workflows from directory: {e}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def get_all_workflows(self) -> List[Workflow]:
        """
        Get all available workflows.
        
        Returns:
            List of all workflows in the database
        """
        return list(self.workflows.values())
    
    def search_workflows(self, query: str, category: Optional[WorkflowCategory] = None,
                        complexity: Optional[ComplexityLevel] = None) -> List[Workflow]:
        """
        Search workflows by query, category, and complexity
        
        Args:
            query: Search query (searches name, description, use cases)
            category: Filter by category
            complexity: Filter by complexity level
            
        Returns:
            List of matching workflows
        """
        results = []
        query_lower = query.lower() if query else ""
        
        for workflow in self.workflows.values():
            # Category filter
            if category and workflow.category != category:
                continue
            
            # Complexity filter
            if complexity and workflow.complexity != complexity:
                continue
            
            # Text search
            if query_lower:
                searchable_text = (
                    workflow.name.lower() + " " +
                    workflow.description.lower() + " " +
                    " ".join(workflow.use_cases).lower()
                )
                if query_lower not in searchable_text:
                    continue
            
            results.append(workflow)
        
        # Sort by relevance (exact name matches first)
        if query_lower:
            results.sort(key=lambda w: (
                0 if query_lower in w.name.lower() else 1,
                w.complexity.value,
                w.name
            ))
        
        return results
    
    def get_workflows_by_category(self, category: WorkflowCategory) -> List[Workflow]:
        """Get all workflows in a category"""
        return [w for w in self.workflows.values() if w.category == category]
    
    def get_workflows_by_complexity(self, complexity: ComplexityLevel) -> List[Workflow]:
        """Get all workflows at a complexity level"""
        return [w for w in self.workflows.values() if w.complexity == complexity]
    
    def recommend_workflows(self, context: Dict[str, Any]) -> List[Workflow]:
        """
        Recommend workflows based on context
        
        Args:
            context: Context information (selected nodes, project type, etc.)
            
        Returns:
            List of recommended workflows
        """
        recommendations = []
        
        # Extract context information
        selected_nodes = context.get('selected_nodes', [])
        node_types = context.get('node_types', [])
        project_stage = context.get('project_stage', '')
        user_level = context.get('user_level', 'intermediate')
        
        # Recommend based on selected nodes
        if 'Read' in node_types and len(selected_nodes) == 1:
            # Single read node - suggest basic workflows
            recommendations.extend(self.get_workflows_by_complexity(ComplexityLevel.BEGINNER))
        
        if 'Keyer' in node_types:
            # Keying nodes present - suggest keying workflows
            recommendations.extend(self.get_workflows_by_category(WorkflowCategory.KEYING))
        
        if any(node_type in ['ColorCorrect', 'Grade'] for node_type in node_types):
            # Color nodes present - suggest color workflows
            recommendations.extend(self.get_workflows_by_category(WorkflowCategory.COLOR))
        
        # Recommend based on project stage
        if 'integration' in project_stage.lower():
            recommendations.extend(self.get_workflows_by_category(WorkflowCategory.CG_INTEGRATION))
        
        if 'cleanup' in project_stage.lower():
            recommendations.extend(self.get_workflows_by_category(WorkflowCategory.CLEANUP))
        
        # Filter by user level
        complexity_map = {
            'beginner': [ComplexityLevel.BEGINNER],
            'intermediate': [ComplexityLevel.BEGINNER, ComplexityLevel.INTERMEDIATE],
            'advanced': [ComplexityLevel.BEGINNER, ComplexityLevel.INTERMEDIATE, ComplexityLevel.ADVANCED],
            'expert': list(ComplexityLevel)
        }
        
        allowed_complexity = complexity_map.get(user_level, [ComplexityLevel.INTERMEDIATE])
        recommendations = [w for w in recommendations if w.complexity in allowed_complexity]
        
        # Remove duplicates and sort
        seen = set()
        unique_recommendations = []
        for workflow in recommendations:
            if workflow.id not in seen:
                seen.add(workflow.id)
                unique_recommendations.append(workflow)
        
        # Sort by complexity and relevance
        unique_recommendations.sort(key=lambda w: (w.complexity.value, w.name))
        
        return unique_recommendations[:10]  # Limit to top 10
    
    def get_workflow_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID"""
        return self.templates.get(template_id)
    
    def create_workflow_from_template(self, template_id: str, 
                                    customizations: Dict[str, Any]) -> Optional[Workflow]:
        """
        Create a workflow instance from a template
        
        Args:
            template_id: ID of the template to use
            customizations: Custom parameters and settings
            
        Returns:
            Workflow instance or None if template not found
        """
        template = self.get_workflow_template(template_id)
        if not template:
            return None
        
        try:
            # Create workflow steps from template
            steps = []
            for i, node_type in enumerate(template.node_sequence):
                # Get default parameters for this node type
                default_params = template.default_parameters.get(node_type, {})
                
                # Apply customizations
                custom_params = customizations.get(f'step_{i+1}', {})
                parameters = {**default_params, **custom_params}
                
                # Determine connections
                connections = []
                for source_idx, target_idx, input_idx in template.connection_pattern:
                    if target_idx == i:
                        connections.append((f'step_{source_idx+1}', input_idx))
                
                step = WorkflowStep(
                    step_number=i+1,
                    title=f"{node_type} Setup",
                    description=f"Configure {node_type} node",
                    node_type=node_type,
                    parameters=parameters,
                    connections=connections,
                    notes=[],
                    alternatives=[]
                )
                steps.append(step)
            
            # Create workflow
            workflow = Workflow(
                id=f"{template_id}_instance_{int(time.time())}",
                name=f"{template.name} (Custom)",
                category=template.category,
                complexity=ComplexityLevel.INTERMEDIATE,
                description=f"Custom workflow based on {template.name}",
                use_cases=[],
                prerequisites=[],
                steps=steps,
                tips=[],
                common_issues=[],
                variations=[],
                estimated_time="Variable",
                quality_checkpoints=[]
            )
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow from template: {e}")
            return None
    
    def export_workflow(self, workflow_id: str, file_path: str) -> bool:
        """
        Export a workflow to a JSON file
        
        Args:
            workflow_id: ID of workflow to export
            file_path: Path to save the file
            
        Returns:
            True if export was successful, False otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        try:
            workflow_data = asdict(workflow)
            
            with open(file_path, 'w') as f:
                json.dump({'workflows': [workflow_data]}, f, indent=2, default=str)
            
            logger.info(f"Workflow exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting workflow: {e}")
            return False
    
    def _deserialize_workflow(self, data: Dict[str, Any]) -> Optional[Workflow]:
        """Deserialize workflow from dictionary"""
        try:
            # Convert enum strings back to enums
            data['category'] = WorkflowCategory(data['category'])
            data['complexity'] = ComplexityLevel(data['complexity'])
            
            # Convert steps
            steps = []
            for step_data in data['steps']:
                step = WorkflowStep(**step_data)
                steps.append(step)
            data['steps'] = steps
            
            return Workflow(**data)
            
        except Exception as e:
            logger.error(f"Error deserializing workflow: {e}")
            return None
    
    def _deserialize_template(self, data: Dict[str, Any]) -> Optional[WorkflowTemplate]:
        """Deserialize template from dictionary"""
        try:
            data['category'] = WorkflowCategory(data['category'])
            return WorkflowTemplate(**data)
            
        except Exception as e:
            logger.error(f"Error deserializing template: {e}")
            return None
    
    def _update_categories(self):
        """Update category mappings"""
        self.categories.clear()
        for workflow in self.workflows.values():
            if workflow.category not in self.categories:
                self.categories[workflow.category] = []
            self.categories[workflow.category].append(workflow.id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'total_workflows': len(self.workflows),
            'total_templates': len(self.templates),
            'categories': {cat.value: len(workflows) for cat, workflows in self.categories.items()},
            'complexity_distribution': {}
        }
        
        # Calculate complexity distribution
        for complexity in ComplexityLevel:
            count = len([w for w in self.workflows.values() if w.complexity == complexity])
            stats['complexity_distribution'][complexity.value] = count
        
        return stats