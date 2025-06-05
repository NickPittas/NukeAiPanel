"""
VFX Prompt Engine

Creates VFX compositor-specific prompts that give AI deep understanding
of Nuke workflows, terminology, and best practices.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of VFX prompts"""
    GENERAL_COMPOSITING = "general_compositing"
    KEYING = "keying"
    COLOR_CORRECTION = "color_correction"
    TRACKING = "tracking"
    ROTOSCOPING = "rotoscoping"
    CG_INTEGRATION = "cg_integration"
    CLEANUP = "cleanup"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"
    WORKFLOW_DESIGN = "workflow_design"


class AIProvider(Enum):
    """Supported AI providers with different prompt styles"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


@dataclass
class PromptContext:
    """Context information for prompt generation"""
    session_info: Dict[str, Any]
    selected_nodes: List[str]
    node_analysis: Dict[str, Any]
    user_intent: str
    workflow_stage: str
    complexity_level: str


@dataclass
class GeneratedPrompt:
    """A generated prompt with metadata"""
    prompt_type: PromptType
    ai_provider: AIProvider
    system_prompt: str
    user_prompt: str
    context_prompt: str
    examples: List[str]
    constraints: List[str]
    expected_output_format: str


class VFXPromptEngine:
    """
    Generates VFX-specific prompts for different AI providers,
    incorporating deep knowledge of Nuke workflows and terminology.
    """
    
    def __init__(self):
        """Initialize the VFX prompt engine"""
        
        # Core VFX terminology and concepts
        self.vfx_terminology = {
            'compositing': [
                'alpha channel', 'premultiplication', 'over operation', 'screen operation',
                'multiply blend', 'additive compositing', 'subtractive compositing',
                'holdout matte', 'garbage matte', 'edge treatment', 'spill suppression'
            ],
            'keying': [
                'chroma key', 'luminance key', 'difference key', 'despill',
                'edge erosion', 'edge dilation', 'core matte', 'edge matte',
                'clean plate', 'backing color', 'spill suppression', 'edge detail'
            ],
            'color': [
                'lift gamma gain', 'primary correction', 'secondary correction',
                'color temperature', 'white balance', 'exposure compensation',
                'contrast enhancement', 'saturation adjustment', 'hue shift',
                'color matching', 'LUT application', 'gamma correction'
            ],
            'tracking': [
                'feature tracking', 'planar tracking', 'camera tracking',
                'stabilization', 'match moving', 'corner pinning',
                'transform data', 'tracking markers', 'solve quality'
            ],
            'cg_integration': [
                'render passes', 'beauty pass', 'diffuse pass', 'specular pass',
                'reflection pass', 'shadow pass', 'ambient occlusion',
                'depth pass', 'motion vectors', 'cryptomatte', 'AOV channels'
            ]
        }
        
        # Common Nuke node workflows
        self.node_workflows = {
            'basic_comp': ['Read', 'ColorCorrect', 'Merge2', 'Write'],
            'keying': ['Read', 'Keyer', 'FilterErode', 'Blur', 'Premult'],
            'cg_integration': ['Read', 'Shuffle', 'Merge2', 'Grade', 'Write'],
            'cleanup': ['Read', 'RotoPaint', 'Merge2', 'Write'],
            'tracking': ['Read', 'Tracker', 'CornerPin', 'Merge2', 'Write']
        }
        
        # Provider-specific prompt styles
        self.provider_styles = {
            AIProvider.OPENAI: {
                'system_style': 'professional_assistant',
                'instruction_format': 'step_by_step',
                'code_format': 'python_blocks',
                'explanation_level': 'detailed'
            },
            AIProvider.ANTHROPIC: {
                'system_style': 'expert_consultant',
                'instruction_format': 'structured_thinking',
                'code_format': 'annotated_scripts',
                'explanation_level': 'comprehensive'
            },
            AIProvider.GOOGLE: {
                'system_style': 'technical_advisor',
                'instruction_format': 'logical_sequence',
                'code_format': 'documented_code',
                'explanation_level': 'moderate'
            },
            AIProvider.MISTRAL: {
                'system_style': 'practical_expert',
                'instruction_format': 'direct_approach',
                'code_format': 'clean_scripts',
                'explanation_level': 'concise'
            }
        }
    
    def generate_prompt(self, prompt_type: PromptType, ai_provider: AIProvider,
                       context: PromptContext) -> GeneratedPrompt:
        """
        Generate a VFX-specific prompt for the given context
        
        Args:
            prompt_type: Type of VFX prompt to generate
            ai_provider: Target AI provider
            context: Context information for the prompt
            
        Returns:
            GeneratedPrompt object
        """
        try:
            # Generate system prompt
            system_prompt = self._generate_system_prompt(prompt_type, ai_provider)
            
            # Generate context prompt
            context_prompt = self._generate_context_prompt(context)
            
            # Generate user prompt
            user_prompt = self._generate_user_prompt(prompt_type, context)
            
            # Get examples
            examples = self._get_examples(prompt_type)
            
            # Get constraints
            constraints = self._get_constraints(prompt_type, ai_provider)
            
            # Get expected output format
            output_format = self._get_output_format(prompt_type, ai_provider)
            
            return GeneratedPrompt(
                prompt_type=prompt_type,
                ai_provider=ai_provider,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context_prompt=context_prompt,
                examples=examples,
                constraints=constraints,
                expected_output_format=output_format
            )
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return self._create_fallback_prompt(prompt_type, ai_provider, context)
    
    def _generate_system_prompt(self, prompt_type: PromptType, ai_provider: AIProvider) -> str:
        """Generate the system prompt based on type and provider"""
        
        base_identity = """You are an expert VFX compositor with deep knowledge of Nuke, industry workflows, and visual effects production. You understand:

- Advanced compositing techniques and node-based workflows
- Color science, keying, tracking, and CG integration
- Industry-standard practices and optimization strategies
- Nuke's Python API and scripting capabilities
- Production pipelines and quality standards"""
        
        # Add prompt-type specific expertise
        if prompt_type == PromptType.KEYING:
            expertise = """
You specialize in keying and matte extraction:
- Chroma and luminance keying techniques
- Edge treatment and spill suppression
- Multi-pass keying workflows
- Clean plate integration and garbage matting
- Advanced keying tools like Primatte and IBK"""
            
        elif prompt_type == PromptType.COLOR_CORRECTION:
            expertise = """
You specialize in color correction and grading:
- Primary and secondary color correction
- Color matching and continuity
- LUT workflows and color space management
- Exposure and contrast optimization
- Creative color grading techniques"""
            
        elif prompt_type == PromptType.CG_INTEGRATION:
            expertise = """
You specialize in CG integration and render pass compositing:
- Multi-pass rendering workflows
- AOV channel management and reconstruction
- Lighting and shadow integration
- Depth compositing and atmospheric effects
- Cryptomatte and ID matte workflows"""
            
        elif prompt_type == PromptType.TRACKING:
            expertise = """
You specialize in tracking and match moving:
- Feature and planar tracking techniques
- Camera tracking and 3D integration
- Stabilization and transform workflows
- Corner pinning and perspective correction
- Tracking data analysis and refinement"""
            
        else:
            expertise = """
You have comprehensive knowledge across all compositing disciplines:
- Node graph optimization and organization
- Workflow design and automation
- Problem-solving and troubleshooting
- Performance optimization techniques"""
        
        # Add provider-specific style
        style = self.provider_styles.get(ai_provider, self.provider_styles[AIProvider.OPENAI])
        
        if style['system_style'] == 'expert_consultant':
            tone = "\nYou approach problems methodically, considering multiple solutions and explaining trade-offs."
        elif style['system_style'] == 'practical_expert':
            tone = "\nYou focus on practical, efficient solutions that work in production environments."
        else:
            tone = "\nYou provide clear, actionable guidance with detailed explanations."
        
        return base_identity + expertise + tone
    
    def _generate_context_prompt(self, context: PromptContext) -> str:
        """Generate context-specific information for the prompt"""
        
        context_parts = []
        
        # Session information
        if context.session_info:
            context_parts.append("CURRENT SESSION:")
            if 'project_name' in context.session_info:
                context_parts.append(f"- Project: {context.session_info['project_name']}")
            if 'frame_range' in context.session_info:
                fr = context.session_info['frame_range']
                context_parts.append(f"- Frame range: {fr[0]}-{fr[1]}")
            if 'format_info' in context.session_info:
                fmt = context.session_info['format_info']
                context_parts.append(f"- Format: {fmt.get('width', 'unknown')}x{fmt.get('height', 'unknown')}")
            if 'total_nodes' in context.session_info:
                context_parts.append(f"- Total nodes: {context.session_info['total_nodes']}")
        
        # Selected nodes
        if context.selected_nodes:
            context_parts.append(f"\nSELECTED NODES: {', '.join(context.selected_nodes)}")
        
        # Node analysis
        if context.node_analysis:
            context_parts.append("\nNODE ANALYSIS:")
            for node_name, analysis in context.node_analysis.items():
                if isinstance(analysis, dict):
                    node_type = analysis.get('class_name', 'Unknown')
                    context_parts.append(f"- {node_name} ({node_type})")
                    if 'potential_issues' in analysis and analysis['potential_issues']:
                        context_parts.append(f"  Issues: {', '.join(analysis['potential_issues'])}")
        
        # Workflow stage
        if context.workflow_stage:
            context_parts.append(f"\nWORKFLOW STAGE: {context.workflow_stage}")
        
        # Complexity level
        if context.complexity_level:
            context_parts.append(f"COMPLEXITY LEVEL: {context.complexity_level}")
        
        return '\n'.join(context_parts)
    
    def _generate_user_prompt(self, prompt_type: PromptType, context: PromptContext) -> str:
        """Generate the user-facing prompt"""
        
        base_prompt = f"USER REQUEST: {context.user_intent}\n\n"
        
        # Add type-specific guidance
        if prompt_type == PromptType.KEYING:
            guidance = """Please provide a keying solution that includes:
1. Analysis of the source material and keying challenges
2. Recommended keying approach and node setup
3. Edge treatment and cleanup strategies
4. Quality assessment and refinement steps
5. Nuke script code for implementation"""
            
        elif prompt_type == PromptType.COLOR_CORRECTION:
            guidance = """Please provide a color correction solution that includes:
1. Analysis of the current color and exposure issues
2. Primary correction strategy (exposure, contrast, color balance)
3. Secondary correction recommendations (selective adjustments)
4. Color matching approach if multiple sources
5. Nuke script code for implementation"""
            
        elif prompt_type == PromptType.CG_INTEGRATION:
            guidance = """Please provide a CG integration solution that includes:
1. Analysis of available render passes and channels
2. Recommended compositing approach and pass reconstruction
3. Lighting and shadow integration strategy
4. Quality enhancement and final polish steps
5. Nuke script code for implementation"""
            
        elif prompt_type == PromptType.OPTIMIZATION:
            guidance = """Please provide an optimization solution that includes:
1. Analysis of current performance bottlenecks
2. Node graph optimization recommendations
3. Workflow efficiency improvements
4. Memory and processing optimizations
5. Nuke script code for implementation"""
            
        else:
            guidance = """Please provide a comprehensive solution that includes:
1. Analysis of the current situation and requirements
2. Recommended approach and workflow
3. Step-by-step implementation strategy
4. Quality considerations and best practices
5. Nuke script code for implementation"""
        
        return base_prompt + guidance
    
    def _get_examples(self, prompt_type: PromptType) -> List[str]:
        """Get relevant examples for the prompt type"""
        
        examples = {
            PromptType.KEYING: [
                "# Basic chroma key setup\nkeyer = nuke.createNode('Keyer')\nkeyer['operation'].setValue('luminance key')",
                "# Edge cleanup workflow\nerode = nuke.createNode('FilterErode')\nblur = nuke.createNode('Blur')\nblur['size'].setValue(0.5)"
            ],
            PromptType.COLOR_CORRECTION: [
                "# Primary color correction\ngrade = nuke.createNode('Grade')\ngrade['white'].setValue([1.2, 1.0, 0.9, 1.0])",
                "# Secondary correction with mask\ncc = nuke.createNode('ColorCorrect')\ncc['saturation'].setValue(1.3)"
            ],
            PromptType.CG_INTEGRATION: [
                "# Multi-pass compositing\nbeauty = nuke.createNode('Read')\nreflection = nuke.createNode('Read')\nmerge = nuke.createNode('Merge2')",
                "# Cryptomatte workflow\ncrypto = nuke.createNode('Cryptomatte')\ncrypto['matteList'].setValue('car')"
            ]
        }
        
        return examples.get(prompt_type, [])
    
    def _get_constraints(self, prompt_type: PromptType, ai_provider: AIProvider) -> List[str]:
        """Get constraints for the prompt"""
        
        base_constraints = [
            "Only suggest safe, production-tested techniques",
            "Provide working Nuke Python code",
            "Consider performance implications",
            "Follow industry best practices",
            "Ensure compatibility with standard Nuke installations"
        ]
        
        type_constraints = {
            PromptType.KEYING: [
                "Prioritize edge quality over speed",
                "Consider spill suppression requirements",
                "Account for motion blur in source material"
            ],
            PromptType.COLOR_CORRECTION: [
                "Preserve image data integrity",
                "Consider color space implications",
                "Maintain natural color relationships"
            ],
            PromptType.OPTIMIZATION: [
                "Do not compromise visual quality",
                "Ensure changes are reversible",
                "Test performance improvements"
            ]
        }
        
        constraints = base_constraints + type_constraints.get(prompt_type, [])
        
        # Add provider-specific constraints
        if ai_provider == AIProvider.ANTHROPIC:
            constraints.append("Provide detailed reasoning for recommendations")
        elif ai_provider == AIProvider.MISTRAL:
            constraints.append("Focus on practical, immediate solutions")
        
        return constraints
    
    def _get_output_format(self, prompt_type: PromptType, ai_provider: AIProvider) -> str:
        """Get expected output format"""
        
        base_format = """Please structure your response as:

1. **Analysis**: Brief analysis of the situation
2. **Approach**: Recommended strategy and workflow
3. **Implementation**: Step-by-step instructions
4. **Code**: Working Nuke Python script
5. **Notes**: Additional considerations and tips"""
        
        if prompt_type == PromptType.TROUBLESHOOTING:
            return """Please structure your response as:

1. **Problem Diagnosis**: Identify the root cause
2. **Solution**: Recommended fix or workaround
3. **Prevention**: How to avoid this issue in future
4. **Code**: Any necessary script fixes
5. **Testing**: How to verify the solution works"""
        
        return base_format
    
    def _create_fallback_prompt(self, prompt_type: PromptType, ai_provider: AIProvider,
                               context: PromptContext) -> GeneratedPrompt:
        """Create a basic fallback prompt when generation fails"""
        
        return GeneratedPrompt(
            prompt_type=prompt_type,
            ai_provider=ai_provider,
            system_prompt="You are a VFX compositor expert helping with Nuke workflows.",
            user_prompt=f"Help with: {context.user_intent}",
            context_prompt="No additional context available.",
            examples=[],
            constraints=["Provide safe, working solutions"],
            expected_output_format="Provide analysis, approach, and implementation steps."
        )
    
    def get_terminology_for_context(self, context_type: str) -> List[str]:
        """Get relevant VFX terminology for a context"""
        return self.vfx_terminology.get(context_type, [])
    
    def get_workflow_nodes(self, workflow_type: str) -> List[str]:
        """Get typical node sequence for a workflow"""
        return self.node_workflows.get(workflow_type, [])
    
    def enhance_prompt_with_terminology(self, prompt: str, context_type: str) -> str:
        """Enhance a prompt with relevant VFX terminology"""
        terminology = self.get_terminology_for_context(context_type)
        if terminology:
            term_section = f"\n\nRelevant VFX terminology: {', '.join(terminology[:10])}"
            return prompt + term_section
        return prompt