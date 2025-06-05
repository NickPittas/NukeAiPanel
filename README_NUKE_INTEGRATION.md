# Nuke AI Panel - Integration System

This document describes the Nuke integration layer and VFX knowledge system that enables AI-powered assistance for Nuke compositing workflows.

## Overview

The Nuke integration system provides:

- **Session Analysis**: Deep analysis of current Nuke sessions, node graphs, and workflow state
- **VFX Knowledge Base**: Comprehensive database of workflows, best practices, and node templates
- **AI Prompt Engineering**: VFX-specific prompts that give AI deep understanding of compositing
- **Safe Script Generation**: Validated Python scripts with undo/redo support
- **Quality Assessment**: Industry best practices evaluation and optimization suggestions

## Architecture

```
src/
├── nuke_integration/          # Core Nuke integration
│   ├── context_analyzer.py    # Session state analysis
│   ├── node_inspector.py      # Deep node analysis
│   ├── script_generator.py    # Safe script generation
│   └── action_applier.py      # Script execution with undo
│
├── vfx_knowledge/            # VFX knowledge system
│   ├── prompt_engine.py      # AI prompt generation
│   ├── workflow_database.py  # Workflow patterns
│   ├── best_practices.py     # Quality standards
│   └── node_templates.py     # Pre-built setups
│
└── data/                     # Knowledge base data
    ├── workflows/            # Workflow definitions
    ├── prompts/             # AI prompt templates
    ├── templates/           # Node templates
    └── best_practices/      # Quality rules
```

## Core Components

### 1. Context Analyzer (`context_analyzer.py`)

Analyzes the current Nuke session to extract comprehensive context:

```python
from nuke_integration.context_analyzer import NukeContextAnalyzer

analyzer = NukeContextAnalyzer()
context = analyzer.get_session_context()

print(f"Project: {context.project_name}")
print(f"Nodes: {context.total_nodes}")
print(f"Selected: {context.selected_nodes}")
print(f"Errors: {context.error_nodes}")
```

**Features:**
- Session metadata (project, frame range, format)
- Complete node graph analysis
- Connection mapping and data flow
- Performance statistics
- Error detection
- Viewer state tracking

### 2. Node Inspector (`node_inspector.py`)

Provides deep analysis of individual nodes and overall graph structure:

```python
from nuke_integration.node_inspector import NodeInspector

inspector = NodeInspector()

# Analyze specific node
analysis = inspector.analyze_node("ColorCorrect1")
print(f"Performance impact: {analysis.performance_impact}")
print(f"Suggestions: {analysis.optimization_suggestions}")

# Analyze entire graph
graph_analysis = inspector.analyze_graph()
print(f"Complexity score: {graph_analysis.complexity_score}")
print(f"Bottlenecks: {graph_analysis.bottlenecks}")
```

**Features:**
- Node categorization and role analysis
- Performance impact assessment
- Connection analysis with data types
- Optimization suggestions
- Graph complexity scoring
- Bottleneck identification

### 3. Script Generator (`script_generator.py`)

Generates safe, validated Nuke Python scripts:

```python
from nuke_integration.script_generator import NukeScriptGenerator, ValidationLevel

generator = NukeScriptGenerator(ValidationLevel.MODERATE)

# Generate node creation script
script = generator.generate_node_creation_script(
    "ColorCorrect",
    {"saturation": 1.2, "gamma": [1.0, 1.0, 1.0, 1.0]},
    position=(100, 200)
)

print(f"Valid: {script.validation_result.is_valid}")
print(f"Code:\n{script.code}")
```

**Features:**
- Multiple script types (nodes, connections, workflows)
- Comprehensive validation with safety checks
- Automatic undo script generation
- Risk assessment and warnings
- Provider-specific formatting

### 4. Action Applier (`action_applier.py`)

Safely executes AI-generated scripts with full undo support:

```python
from nuke_integration.action_applier import ActionApplier

applier = ActionApplier()

# Apply script with automatic snapshot
action = applier.apply_script(generated_script)

print(f"Status: {action.status}")
print(f"Execution time: {action.execution_time}s")

# Undo if needed
if action.status == ActionStatus.SUCCESS:
    applier.undo_last_action()
```

**Features:**
- Pre-execution validation and confirmation
- Automatic state snapshots
- Comprehensive undo/redo system
- Batch operation support
- Action history tracking
- Error recovery

## VFX Knowledge System

### 1. Prompt Engine (`prompt_engine.py`)

Creates VFX-specific prompts for different AI providers:

```python
from vfx_knowledge.prompt_engine import VFXPromptEngine, PromptType, AIProvider

engine = VFXPromptEngine()

prompt = engine.generate_prompt(
    PromptType.KEYING,
    AIProvider.OPENAI,
    context
)

print(f"System prompt: {prompt.system_prompt}")
print(f"User prompt: {prompt.user_prompt}")
```

**Features:**
- Provider-specific prompt styles
- VFX terminology integration
- Context-aware prompt generation
- Industry workflow knowledge
- Example code snippets

### 2. Workflow Database (`workflow_database.py`)

Manages common VFX workflows and patterns:

```python
from vfx_knowledge.workflow_database import WorkflowDatabase

db = WorkflowDatabase()

# Search workflows
workflows = db.search_workflows("keying", complexity="intermediate")

# Get recommendations
recommendations = db.recommend_workflows({
    'selected_nodes': ['Read1', 'Keyer1'],
    'user_level': 'intermediate'
})
```

**Features:**
- Comprehensive workflow library
- Search and recommendation system
- Step-by-step instructions
- Quality checkpoints
- Workflow templates

### 3. Best Practices Engine (`best_practices.py`)

Evaluates workflows against industry standards:

```python
from vfx_knowledge.best_practices import BestPracticesEngine

engine = BestPracticesEngine()

assessment = engine.evaluate_workflow(context)

print(f"Overall score: {assessment.overall_score}/100")
print(f"Violations: {len(assessment.violations)}")
print(f"Recommendations: {assessment.recommendations}")
```

**Features:**
- Industry best practice rules
- Quality scoring system
- Violation detection and suggestions
- Performance optimization tips
- Collaboration guidelines

### 4. Node Templates (`node_templates.py`)

Pre-built node combinations for common operations:

```python
from vfx_knowledge.node_templates import NodeTemplateManager

manager = NodeTemplateManager()

# Search templates
templates = manager.search_templates("keying")

# Instantiate template
instance = manager.instantiate_template("basic_keying", {
    'key_tolerance': 0.1,
    'edge_size': -0.5
})
```

**Features:**
- Ready-to-use node setups
- Customizable parameters
- Template instantiation in Nuke
- Category-based organization
- Template sharing and export

## Usage Examples

### Basic Session Analysis

```python
from nuke_integration.context_analyzer import NukeContextAnalyzer

# Analyze current session
analyzer = NukeContextAnalyzer()
context = analyzer.get_session_context()

if context:
    print(f"Analyzing {context.project_name}")
    print(f"Total nodes: {context.total_nodes}")
    
    if context.error_nodes:
        print(f"Errors found in: {context.error_nodes}")
    
    # Get selected node details
    selected_analysis = analyzer.get_selected_nodes_context()
    for node in selected_analysis:
        print(f"Selected: {node.name} ({node.class_name})")
```

### Generate AI-Optimized Workflow

```python
from vfx_knowledge.prompt_engine import VFXPromptEngine, PromptType, AIProvider, PromptContext

# Create context for AI
prompt_context = PromptContext(
    session_info={'project_name': 'Hero_Shot_v01'},
    selected_nodes=['Read1', 'Keyer1'],
    node_analysis={},
    user_intent="Improve this keying setup for better edge quality",
    workflow_stage="keying",
    complexity_level="advanced"
)

# Generate AI prompt
engine = VFXPromptEngine()
prompt = engine.generate_prompt(PromptType.KEYING, AIProvider.OPENAI, prompt_context)

# Send to AI provider (using existing provider system)
# ai_response = provider.generate_response(prompt.system_prompt, prompt.user_prompt)
```

### Apply AI Suggestions Safely

```python
from nuke_integration.script_generator import NukeScriptGenerator
from nuke_integration.action_applier import ActionApplier

# Generate script from AI suggestion
generator = NukeScriptGenerator()
script = generator.generate_parameter_adjustment_script(
    "Keyer1",
    {"tolerance": 0.05, "edge_size": -1.0}
)

# Apply with safety checks
applier = ActionApplier()
action = applier.apply_script(script, require_confirmation=True)

if action.status == ActionStatus.SUCCESS:
    print("Changes applied successfully")
    print(f"Execution time: {action.execution_time}s")
else:
    print(f"Failed: {action.error_message}")
```

### Quality Assessment

```python
from vfx_knowledge.best_practices import BestPracticesEngine

engine = BestPracticesEngine()

# Evaluate current workflow
assessment = engine.evaluate_workflow({
    'nodes': context.nodes,
    'connections': context.connections,
    'session_info': context.session_info
})

print(f"Quality Score: {assessment.overall_score:.1f}/100")

# Show violations
for violation in assessment.violations:
    print(f"⚠ {violation.description}")
    print(f"  Suggestion: {violation.suggestion}")

# Show recommendations
for rec in assessment.recommendations:
    print(f"💡 {rec}")
```

## Safety Features

### Script Validation

All generated scripts undergo comprehensive validation:

- **Syntax checking**: AST parsing for Python syntax errors
- **Security scanning**: Detection of dangerous functions
- **Nuke API validation**: Verification of node types and parameters
- **Risk assessment**: Classification of potential issues

### Undo System

Complete undo/redo support with:

- **State snapshots**: Full session state before changes
- **Action history**: Detailed log of all operations
- **Selective undo**: Undo specific actions by ID
- **Batch operations**: Group related changes

### Error Handling

Robust error handling throughout:

- **Graceful degradation**: Works outside Nuke environment
- **Detailed logging**: Comprehensive error reporting
- **Recovery mechanisms**: Automatic rollback on failures
- **User feedback**: Clear error messages and suggestions

## Configuration

### Validation Levels

```python
from nuke_integration.script_generator import ValidationLevel

# Strict: Only safe, well-known operations
generator = NukeScriptGenerator(ValidationLevel.STRICT)

# Moderate: Most operations with validation (default)
generator = NukeScriptGenerator(ValidationLevel.MODERATE)

# Permissive: Minimal validation for advanced users
generator = NukeScriptGenerator(ValidationLevel.PERMISSIVE)
```

### Data Directories

```python
from vfx_knowledge.workflow_database import WorkflowDatabase

# Use custom data directory
db = WorkflowDatabase(data_directory="custom/workflows")

# Load additional workflows
db._load_workflows_from_files()
```

## Integration with AI Providers

The system integrates seamlessly with the existing AI provider framework:

```python
from nuke_ai_panel.core.provider_manager import ProviderManager
from vfx_knowledge.prompt_engine import VFXPromptEngine

# Get AI response using VFX-optimized prompts
provider_manager = ProviderManager()
prompt_engine = VFXPromptEngine()

# Generate VFX-specific prompt
prompt = prompt_engine.generate_prompt(PromptType.KEYING, AIProvider.OPENAI, context)

# Send to AI provider
response = provider_manager.generate_response(
    provider_name="openai",
    messages=[
        {"role": "system", "content": prompt.system_prompt},
        {"role": "user", "content": prompt.user_prompt}
    ]
)

# Process AI response and generate scripts
# ... (script generation and application)
```

## Performance Considerations

### Caching

- Session context cached for 5 seconds
- Node analysis results cached per session
- Template instantiation optimized for reuse

### Memory Management

- Lazy loading of workflow database
- Efficient node graph traversal
- Automatic cleanup of temporary data

### Scalability

- Handles large node graphs (1000+ nodes)
- Efficient search algorithms
- Minimal impact on Nuke performance

## Future Enhancements

### Planned Features

- **Machine Learning Integration**: Learn from user preferences
- **Advanced Templates**: Procedural template generation
- **Collaboration Tools**: Team workflow sharing
- **Performance Profiling**: Detailed performance analysis
- **Custom Rules**: User-defined best practices

### API Extensions

- **Plugin Architecture**: Third-party extensions
- **Custom Workflows**: User workflow creation
- **External Integrations**: Pipeline tool connections
- **Cloud Sync**: Workflow synchronization

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Nuke Python API is available
2. **Permission Errors**: Check file system permissions for data directories
3. **Memory Issues**: Reduce cache sizes for large projects
4. **Performance**: Use proxy modes for complex workflows

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for all components
```

### Support

For issues and questions:
- Check the example scripts in `examples/`
- Review the test cases for usage patterns
- Enable debug logging for detailed information

## License

This integration system is part of the Nuke AI Panel project and follows the same licensing terms.