"""
Nuke Integration Example

Demonstrates how to use the Nuke AI Panel integration system
for analyzing sessions, generating scripts, and applying AI suggestions.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nuke_integration.context_analyzer import NukeContextAnalyzer
from nuke_integration.node_inspector import NodeInspector
from nuke_integration.script_generator import NukeScriptGenerator, ValidationLevel
from nuke_integration.action_applier import ActionApplier
from vfx_knowledge.prompt_engine import VFXPromptEngine, PromptType, AIProvider, PromptContext
from vfx_knowledge.workflow_database import WorkflowDatabase
from vfx_knowledge.best_practices import BestPracticesEngine
from vfx_knowledge.node_templates import NodeTemplateManager


def main():
    """Main example function demonstrating the integration system"""
    
    print("=== Nuke AI Panel Integration Example ===\n")
    
    # Initialize components
    print("1. Initializing components...")
    context_analyzer = NukeContextAnalyzer()
    node_inspector = NodeInspector()
    script_generator = NukeScriptGenerator(ValidationLevel.MODERATE)
    action_applier = ActionApplier(ValidationLevel.MODERATE)
    prompt_engine = VFXPromptEngine()
    workflow_db = WorkflowDatabase()
    best_practices = BestPracticesEngine()
    template_manager = NodeTemplateManager()
    
    print("✓ All components initialized\n")
    
    # Example 1: Session Analysis
    print("2. Session Analysis Example...")
    session_context = context_analyzer.get_session_context()
    
    if session_context:
        print(f"✓ Session analyzed: {session_context.project_name}")
        print(f"  - Total nodes: {session_context.total_nodes}")
        print(f"  - Selected nodes: {len(session_context.selected_nodes)}")
        print(f"  - Frame range: {session_context.frame_range}")
        print(f"  - Format: {session_context.format_info.get('name', 'Unknown')}")
        
        if session_context.error_nodes:
            print(f"  - Error nodes: {session_context.error_nodes}")
    else:
        print("⚠ No Nuke session available (running outside Nuke)")
        # Create mock context for demonstration
        session_context = create_mock_session_context()
        print("✓ Using mock session context for demonstration")
    
    print()
    
    # Example 2: Node Analysis
    print("3. Node Analysis Example...")
    if session_context.selected_nodes:
        selected_analysis = node_inspector.analyze_selected_nodes()
        print(f"✓ Analyzed {len(selected_analysis)} selected nodes")
        
        for analysis in selected_analysis[:2]:  # Show first 2
            print(f"  - {analysis.name} ({analysis.class_name})")
            print(f"    Category: {analysis.category}")
            print(f"    Performance: {analysis.performance_impact}")
            if analysis.optimization_suggestions:
                print(f"    Suggestions: {analysis.optimization_suggestions[0]}")
    else:
        print("⚠ No nodes selected")
    
    print()
    
    # Example 3: Script Generation
    print("4. Script Generation Example...")
    
    # Generate a basic compositing workflow
    basic_comp_script = script_generator.generate_workflow_script(
        'basic_comp', 
        {'background_file': 'bg_plate.exr', 'foreground_file': 'fg_element.exr'}
    )
    
    print(f"✓ Generated script: {basic_comp_script.description}")
    print(f"  - Type: {basic_comp_script.script_type.value}")
    print(f"  - Valid: {basic_comp_script.validation_result.is_valid}")
    print(f"  - Estimated time: {basic_comp_script.estimated_execution_time}s")
    
    if basic_comp_script.validation_result.warnings:
        print(f"  - Warnings: {len(basic_comp_script.validation_result.warnings)}")
    
    print()
    
    # Example 4: VFX Prompt Generation
    print("5. VFX Prompt Generation Example...")
    
    # Create prompt context
    prompt_context = PromptContext(
        session_info={
            'project_name': session_context.project_name,
            'total_nodes': session_context.total_nodes,
            'frame_range': session_context.frame_range
        },
        selected_nodes=session_context.selected_nodes,
        node_analysis={},
        user_intent="Help me create a professional keying workflow for green screen footage",
        workflow_stage="keying",
        complexity_level="intermediate"
    )
    
    # Generate keying prompt for different AI providers
    for provider in [AIProvider.OPENAI, AIProvider.ANTHROPIC]:
        prompt = prompt_engine.generate_prompt(
            PromptType.KEYING, 
            provider, 
            prompt_context
        )
        
        print(f"✓ Generated {provider.value} keying prompt")
        print(f"  - System prompt length: {len(prompt.system_prompt)} chars")
        print(f"  - Examples: {len(prompt.examples)}")
        print(f"  - Constraints: {len(prompt.constraints)}")
    
    print()
    
    # Example 5: Workflow Database
    print("6. Workflow Database Example...")
    
    # Search for keying workflows
    keying_workflows = workflow_db.search_workflows("keying", category=None)
    print(f"✓ Found {len(keying_workflows)} keying workflows")
    
    for workflow in keying_workflows[:2]:  # Show first 2
        print(f"  - {workflow.name} ({workflow.complexity.value})")
        print(f"    Steps: {len(workflow.steps)}")
        print(f"    Estimated time: {workflow.estimated_time}")
    
    # Get workflow recommendations
    recommendations = workflow_db.recommend_workflows({
        'selected_nodes': session_context.selected_nodes,
        'node_types': ['Read', 'Keyer'],
        'user_level': 'intermediate'
    })
    
    print(f"✓ Generated {len(recommendations)} workflow recommendations")
    
    print()
    
    # Example 6: Best Practices Analysis
    print("7. Best Practices Analysis Example...")
    
    # Create context for best practices evaluation
    bp_context = {
        'nodes': [
            {'name': 'Read1', 'class_name': 'Read', 'parameters': {}},
            {'name': 'Merge2_1', 'class_name': 'Merge2', 'parameters': {'bbox': 'union'}},
            {'name': 'ColorCorrect1', 'class_name': 'ColorCorrect', 'parameters': {}}
        ],
        'connections': [],
        'session_info': {
            'frame_range': session_context.frame_range,
            'total_nodes': session_context.total_nodes
        }
    }
    
    assessment = best_practices.evaluate_workflow(bp_context)
    
    print(f"✓ Quality assessment completed")
    print(f"  - Overall score: {assessment.overall_score:.1f}/100")
    print(f"  - Violations: {len(assessment.violations)}")
    print(f"  - Recommendations: {len(assessment.recommendations)}")
    print(f"  - Strengths: {len(assessment.strengths)}")
    
    if assessment.violations:
        print(f"  - Top violation: {assessment.violations[0].description}")
    
    print()
    
    # Example 7: Node Templates
    print("8. Node Template Example...")
    
    # Search for templates
    keying_templates = template_manager.search_templates("keying")
    print(f"✓ Found {len(keying_templates)} keying templates")
    
    for template in keying_templates[:2]:  # Show first 2
        print(f"  - {template.name} ({template.complexity.value})")
        print(f"    Nodes: {len(template.nodes)}")
        print(f"    Connections: {len(template.connections)}")
    
    # Get template statistics
    stats = template_manager.get_statistics()
    print(f"✓ Template statistics:")
    print(f"  - Total templates: {stats['total_templates']}")
    print(f"  - Categories: {list(stats['categories'].keys())}")
    
    print()
    
    # Example 8: Action Application (simulation)
    print("9. Action Application Example...")
    
    # Simulate applying a workflow (would work in actual Nuke)
    if session_context.total_nodes > 0:
        print("✓ Would apply workflow in actual Nuke session")
        print("  - Validation checks would run")
        print("  - User confirmation would be requested")
        print("  - Undo information would be stored")
    else:
        print("⚠ No active Nuke session - simulation mode")
        print("  - Script generation: ✓")
        print("  - Validation: ✓")
        print("  - Execution: (would run in Nuke)")
    
    print()
    
    print("=== Example Complete ===")
    print("\nThis example demonstrates:")
    print("• Session context analysis")
    print("• Node inspection and optimization")
    print("• Safe script generation with validation")
    print("• VFX-specific prompt engineering")
    print("• Workflow database and recommendations")
    print("• Best practices evaluation")
    print("• Node template management")
    print("• Action application with undo support")


def create_mock_session_context():
    """Create a mock session context for demonstration when Nuke is not available"""
    from nuke_integration.context_analyzer import SessionContext, ViewerState, NodeInfo
    
    # Create some mock nodes
    mock_nodes = [
        NodeInfo(
            name="BG_Plate",
            class_name="Read",
            position=(0, 0),
            selected=False,
            disabled=False,
            inputs=[],
            outputs=["ColorCorrect1"],
            knob_values={"file": "bg_plate.exr"}
        ),
        NodeInfo(
            name="FG_Element", 
            class_name="Read",
            position=(200, 0),
            selected=True,
            disabled=False,
            inputs=[],
            outputs=["Merge1"],
            knob_values={"file": "fg_element.exr"}
        ),
        NodeInfo(
            name="Primary_Grade",
            class_name="ColorCorrect",
            position=(0, 100),
            selected=False,
            disabled=False,
            inputs=["BG_Plate"],
            outputs=["Merge1"],
            knob_values={"saturation": 1.1}
        ),
        NodeInfo(
            name="Final_Comp",
            class_name="Merge2",
            position=(100, 200),
            selected=False,
            disabled=False,
            inputs=["Primary_Grade", "FG_Element"],
            outputs=["Viewer1"],
            knob_values={"operation": "over"}
        )
    ]
    
    return SessionContext(
        project_name="Demo_Project",
        script_path="/path/to/demo_project.nk",
        frame_range=(1001, 1100),
        current_frame=1050,
        fps=24.0,
        format_info={"name": "HD_1080", "width": 1920, "height": 1080},
        selected_nodes=["FG_Element"],
        viewer_node="Viewer1",
        viewer_state=ViewerState.RGBA,
        nodes=mock_nodes,
        node_graph_bounds=(0, 0, 200, 200),
        total_nodes=4,
        error_nodes=[],
        performance_stats={"memory_usage": "2.1GB", "cache_usage": "45%"}
    )


if __name__ == "__main__":
    main()