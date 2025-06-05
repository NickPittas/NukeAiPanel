"""
Best Practices Engine

Industry best practices and optimization rules for VFX compositing,
providing guidance on quality standards and workflow optimization.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PracticeCategory(Enum):
    """Categories of best practices"""
    WORKFLOW = "workflow"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    ORGANIZATION = "organization"
    COLOR_MANAGEMENT = "color_management"
    TECHNICAL = "technical"
    COLLABORATION = "collaboration"


class Severity(Enum):
    """Severity levels for practice violations"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class BestPractice:
    """A single best practice rule"""
    id: str
    category: PracticeCategory
    title: str
    description: str
    rationale: str
    examples: List[str]
    violations: List[str]
    fixes: List[str]
    severity: Severity
    applicable_contexts: List[str]


@dataclass
class PracticeViolation:
    """A detected violation of best practices"""
    practice_id: str
    severity: Severity
    node_name: Optional[str]
    description: str
    suggestion: str
    auto_fixable: bool


@dataclass
class QualityAssessment:
    """Assessment of workflow quality"""
    overall_score: float
    category_scores: Dict[PracticeCategory, float]
    violations: List[PracticeViolation]
    recommendations: List[str]
    strengths: List[str]


class BestPracticesEngine:
    """
    Engine for evaluating VFX workflows against industry best practices
    and providing optimization recommendations.
    """
    
    def __init__(self):
        """Initialize the best practices engine"""
        self.practices: Dict[str, BestPractice] = {}
        self._initialize_practices()
    
    def _initialize_practices(self):
        """Initialize built-in best practices"""
        
        practices = [
            # Workflow Organization
            BestPractice(
                id="node_naming",
                category=PracticeCategory.ORGANIZATION,
                title="Descriptive Node Naming",
                description="Use clear, descriptive names for all nodes",
                rationale="Improves readability and collaboration, makes debugging easier",
                examples=[
                    "BG_Plate_v01 instead of Read1",
                    "Hero_ColorCorrect instead of ColorCorrect3",
                    "Final_Comp instead of Merge2_7"
                ],
                violations=[
                    "Default node names (Read1, Merge2, etc.)",
                    "Cryptic abbreviations",
                    "Numbers without context"
                ],
                fixes=[
                    "Rename nodes immediately after creation",
                    "Use project naming conventions",
                    "Include version numbers when appropriate"
                ],
                severity=Severity.WARNING,
                applicable_contexts=["all"]
            ),
            
            BestPractice(
                id="node_organization",
                category=PracticeCategory.ORGANIZATION,
                title="Logical Node Layout",
                description="Organize nodes in a logical, readable flow",
                rationale="Reduces confusion, improves maintenance, enables collaboration",
                examples=[
                    "Left-to-right flow for main pipeline",
                    "Vertical branches for variations",
                    "Grouped related operations"
                ],
                violations=[
                    "Crossing connections",
                    "Random node placement",
                    "Unclear data flow"
                ],
                fixes=[
                    "Use Dot nodes for organization",
                    "Align nodes in clean rows/columns",
                    "Group related operations together"
                ],
                severity=Severity.INFO,
                applicable_contexts=["all"]
            ),
            
            # Performance Optimization
            BestPractice(
                id="bbox_optimization",
                category=PracticeCategory.PERFORMANCE,
                title="Bounding Box Optimization",
                description="Use appropriate bounding box settings to minimize processing",
                rationale="Reduces memory usage and processing time",
                examples=[
                    "Set bbox to 'B' input for Merge operations",
                    "Use 'intersection' for operations that don't expand",
                    "Crop early in the pipeline"
                ],
                violations=[
                    "Union bbox on all operations",
                    "Processing full format when unnecessary",
                    "Late cropping in pipeline"
                ],
                fixes=[
                    "Add Crop nodes early in pipeline",
                    "Set appropriate bbox modes on Merge nodes",
                    "Use Reformat to reduce resolution for tests"
                ],
                severity=Severity.WARNING,
                applicable_contexts=["performance_critical"]
            ),
            
            BestPractice(
                id="proxy_workflow",
                category=PracticeCategory.PERFORMANCE,
                title="Proxy Workflow Usage",
                description="Use proxy modes for interactive work",
                rationale="Improves interactive performance during creative work",
                examples=[
                    "Set proxy scale to 1/2 or 1/4 for complex comps",
                    "Use proxy files for heavy source material",
                    "Switch to full resolution for final review"
                ],
                violations=[
                    "Working at full resolution unnecessarily",
                    "No proxy setup for heavy comps",
                    "Forgetting to switch back to full res"
                ],
                fixes=[
                    "Set up proxy scale in project settings",
                    "Create proxy versions of heavy source files",
                    "Use proxy indicators in viewer"
                ],
                severity=Severity.INFO,
                applicable_contexts=["interactive_work"]
            ),
            
            # Quality Standards
            BestPractice(
                id="color_space_management",
                category=PracticeCategory.COLOR_MANAGEMENT,
                title="Proper Color Space Management",
                description="Maintain correct color spaces throughout the pipeline",
                rationale="Ensures color accuracy and prevents artifacts",
                examples=[
                    "Set correct color space on Read nodes",
                    "Work in linear for compositing operations",
                    "Convert to display space only for viewing"
                ],
                violations=[
                    "Incorrect color space settings",
                    "Missing color space conversions",
                    "Working in display space for compositing"
                ],
                fixes=[
                    "Verify color space metadata",
                    "Add Colorspace nodes when needed",
                    "Use OCIO configuration"
                ],
                severity=Severity.ERROR,
                applicable_contexts=["color_critical"]
            ),
            
            BestPractice(
                id="alpha_handling",
                category=PracticeCategory.QUALITY,
                title="Proper Alpha Channel Handling",
                description="Handle alpha channels correctly for clean compositing",
                rationale="Prevents edge artifacts and color contamination",
                examples=[
                    "Use Premult for CG elements",
                    "Unpremult before color operations",
                    "Check alpha in viewer regularly"
                ],
                violations=[
                    "Ignoring premultiplication state",
                    "Color correcting premultiplied images",
                    "Black edges from incorrect alpha handling"
                ],
                fixes=[
                    "Add Premult/Unpremult nodes as needed",
                    "Use alpha-aware color correction",
                    "Verify alpha channels in viewer"
                ],
                severity=Severity.ERROR,
                applicable_contexts=["compositing"]
            ),
            
            BestPractice(
                id="edge_quality",
                category=PracticeCategory.QUALITY,
                title="Edge Quality Preservation",
                description="Maintain high-quality edges throughout the pipeline",
                rationale="Ensures professional-looking composites",
                examples=[
                    "Use appropriate filtering on Transform nodes",
                    "Preserve motion blur in keying operations",
                    "Avoid over-processing edges"
                ],
                violations=[
                    "Aliased edges from poor filtering",
                    "Lost detail from over-processing",
                    "Inconsistent edge treatment"
                ],
                fixes=[
                    "Use high-quality filters",
                    "Process edges separately when needed",
                    "Test edge quality at different scales"
                ],
                severity=Severity.WARNING,
                applicable_contexts=["quality_critical"]
            ),
            
            # Technical Standards
            BestPractice(
                id="frame_range_consistency",
                category=PracticeCategory.TECHNICAL,
                title="Frame Range Consistency",
                description="Maintain consistent frame ranges across all elements",
                rationale="Prevents sync issues and missing frames",
                examples=[
                    "Set project frame range first",
                    "Verify all Read nodes have correct ranges",
                    "Handle frame offsets explicitly"
                ],
                violations=[
                    "Mismatched frame ranges",
                    "Missing frames in sequences",
                    "Incorrect frame rate settings"
                ],
                fixes=[
                    "Check frame ranges on all Read nodes",
                    "Use frame expressions for offsets",
                    "Verify frame rate consistency"
                ],
                severity=Severity.ERROR,
                applicable_contexts=["all"]
            ),
            
            BestPractice(
                id="version_control",
                category=PracticeCategory.COLLABORATION,
                title="Version Control and Backup",
                description="Maintain proper version control and backups",
                rationale="Prevents data loss and enables collaboration",
                examples=[
                    "Save incremental versions regularly",
                    "Use descriptive version comments",
                    "Backup to multiple locations"
                ],
                violations=[
                    "Overwriting previous versions",
                    "No backup strategy",
                    "Unclear version naming"
                ],
                fixes=[
                    "Implement version numbering system",
                    "Set up automatic backups",
                    "Document version changes"
                ],
                severity=Severity.WARNING,
                applicable_contexts=["production"]
            ),
            
            # Keying Best Practices
            BestPractice(
                id="keying_workflow",
                category=PracticeCategory.QUALITY,
                title="Professional Keying Workflow",
                description="Follow established keying workflow for best results",
                rationale="Ensures consistent, high-quality keys",
                examples=[
                    "Start with conservative key",
                    "Refine edges separately",
                    "Handle spill suppression properly"
                ],
                violations=[
                    "Aggressive initial keying",
                    "Ignoring edge treatment",
                    "No spill suppression"
                ],
                fixes=[
                    "Use multi-pass keying approach",
                    "Add edge refinement nodes",
                    "Include spill suppression in workflow"
                ],
                severity=Severity.WARNING,
                applicable_contexts=["keying"]
            ),
            
            # Performance Monitoring
            BestPractice(
                id="memory_management",
                category=PracticeCategory.PERFORMANCE,
                title="Memory Usage Optimization",
                description="Monitor and optimize memory usage",
                rationale="Prevents crashes and improves performance",
                examples=[
                    "Use appropriate cache settings",
                    "Limit concurrent processing",
                    "Monitor memory usage during renders"
                ],
                violations=[
                    "Excessive memory usage",
                    "Memory leaks from poor caching",
                    "Running out of memory during renders"
                ],
                fixes=[
                    "Adjust cache limits",
                    "Use disk cache for large operations",
                    "Process in smaller chunks"
                ],
                severity=Severity.WARNING,
                applicable_contexts=["performance_critical"]
            )
        ]
        
        # Add practices to dictionary
        for practice in practices:
            self.practices[practice.id] = practice
    
    def evaluate_workflow(self, context: Dict[str, Any]) -> QualityAssessment:
        """
        Evaluate a workflow against best practices
        
        Args:
            context: Workflow context including nodes, connections, etc.
            
        Returns:
            QualityAssessment with violations and recommendations
        """
        violations = []
        category_scores = {}
        
        try:
            # Extract context information
            nodes = context.get('nodes', [])
            connections = context.get('connections', [])
            session_info = context.get('session_info', {})
            
            # Check each practice
            for practice in self.practices.values():
                practice_violations = self._check_practice(practice, context)
                violations.extend(practice_violations)
            
            # Calculate category scores
            for category in PracticeCategory:
                category_violations = [v for v in violations if self.practices[v.practice_id].category == category]
                category_practices = [p for p in self.practices.values() if p.category == category]
                
                if category_practices:
                    violation_penalty = sum(self._get_severity_weight(v.severity) for v in category_violations)
                    max_penalty = len(category_practices) * self._get_severity_weight(Severity.CRITICAL)
                    score = max(0, 100 - (violation_penalty / max_penalty * 100)) if max_penalty > 0 else 100
                    category_scores[category] = score
                else:
                    category_scores[category] = 100
            
            # Calculate overall score
            overall_score = sum(category_scores.values()) / len(category_scores) if category_scores else 100
            
            # Generate recommendations
            recommendations = self._generate_recommendations(violations, context)
            
            # Identify strengths
            strengths = self._identify_strengths(violations, context)
            
            return QualityAssessment(
                overall_score=overall_score,
                category_scores=category_scores,
                violations=violations,
                recommendations=recommendations,
                strengths=strengths
            )
            
        except Exception as e:
            logger.error(f"Error evaluating workflow: {e}")
            return QualityAssessment(
                overall_score=50.0,
                category_scores={cat: 50.0 for cat in PracticeCategory},
                violations=[],
                recommendations=["Error occurred during evaluation"],
                strengths=[]
            )
    
    def _check_practice(self, practice: BestPractice, context: Dict[str, Any]) -> List[PracticeViolation]:
        """Check a specific practice against the context"""
        violations = []
        
        try:
            nodes = context.get('nodes', [])
            
            # Check node naming practice
            if practice.id == "node_naming":
                for node in nodes:
                    node_name = node.get('name', '')
                    class_name = node.get('class_name', '')
                    
                    # Check for default names
                    if (node_name.startswith(class_name) and 
                        node_name[len(class_name):].isdigit()):
                        violations.append(PracticeViolation(
                            practice_id=practice.id,
                            severity=practice.severity,
                            node_name=node_name,
                            description=f"Node '{node_name}' uses default naming",
                            suggestion=f"Rename to describe its purpose (e.g., 'BG_Plate', 'Hero_Grade')",
                            auto_fixable=False
                        ))
            
            # Check bounding box optimization
            elif practice.id == "bbox_optimization":
                for node in nodes:
                    class_name = node.get('class_name', '')
                    parameters = node.get('parameters', {})
                    
                    if class_name in ['Merge2', 'Merge']:
                        bbox_setting = parameters.get('bbox', 'union')
                        if bbox_setting == 'union':
                            violations.append(PracticeViolation(
                                practice_id=practice.id,
                                severity=practice.severity,
                                node_name=node.get('name', ''),
                                description=f"Merge node using 'union' bbox mode",
                                suggestion="Consider using 'B' or 'intersection' for better performance",
                                auto_fixable=True
                            ))
            
            # Check color space management
            elif practice.id == "color_space_management":
                for node in nodes:
                    class_name = node.get('class_name', '')
                    parameters = node.get('parameters', {})
                    
                    if class_name == 'Read':
                        colorspace = parameters.get('colorspace', '')
                        if not colorspace or colorspace == 'default':
                            violations.append(PracticeViolation(
                                practice_id=practice.id,
                                severity=practice.severity,
                                node_name=node.get('name', ''),
                                description="Read node missing explicit color space setting",
                                suggestion="Set appropriate color space based on source material",
                                auto_fixable=False
                            ))
            
            # Check frame range consistency
            elif practice.id == "frame_range_consistency":
                session_frame_range = context.get('session_info', {}).get('frame_range', (1, 100))
                
                for node in nodes:
                    class_name = node.get('class_name', '')
                    parameters = node.get('parameters', {})
                    
                    if class_name == 'Read':
                        first_frame = parameters.get('first', 1)
                        last_frame = parameters.get('last', 100)
                        
                        if (first_frame != session_frame_range[0] or 
                            last_frame != session_frame_range[1]):
                            violations.append(PracticeViolation(
                                practice_id=practice.id,
                                severity=practice.severity,
                                node_name=node.get('name', ''),
                                description=f"Frame range mismatch: {first_frame}-{last_frame} vs project {session_frame_range[0]}-{session_frame_range[1]}",
                                suggestion="Verify frame range matches project settings",
                                auto_fixable=True
                            ))
            
            # Check for unused nodes
            elif practice.id == "node_organization":
                connections = context.get('connections', [])
                connected_nodes = set()
                
                for conn in connections:
                    connected_nodes.add(conn.get('source_node', ''))
                    connected_nodes.add(conn.get('target_node', ''))
                
                for node in nodes:
                    node_name = node.get('name', '')
                    class_name = node.get('class_name', '')
                    
                    # Skip output nodes
                    if class_name in ['Viewer', 'Write']:
                        continue
                    
                    if node_name not in connected_nodes:
                        violations.append(PracticeViolation(
                            practice_id=practice.id,
                            severity=Severity.INFO,
                            node_name=node_name,
                            description=f"Unused node detected: {node_name}",
                            suggestion="Remove unused nodes or connect to workflow",
                            auto_fixable=True
                        ))
            
        except Exception as e:
            logger.warning(f"Error checking practice {practice.id}: {e}")
        
        return violations
    
    def _get_severity_weight(self, severity: Severity) -> float:
        """Get numeric weight for severity level"""
        weights = {
            Severity.INFO: 1.0,
            Severity.WARNING: 2.0,
            Severity.ERROR: 4.0,
            Severity.CRITICAL: 8.0
        }
        return weights.get(severity, 1.0)
    
    def _generate_recommendations(self, violations: List[PracticeViolation], 
                                context: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on violations"""
        recommendations = []
        
        # Group violations by severity
        critical_violations = [v for v in violations if v.severity == Severity.CRITICAL]
        error_violations = [v for v in violations if v.severity == Severity.ERROR]
        warning_violations = [v for v in violations if v.severity == Severity.WARNING]
        
        # Priority recommendations
        if critical_violations:
            recommendations.append("Address critical issues immediately to prevent workflow failures")
        
        if error_violations:
            recommendations.append("Fix error-level issues to ensure quality standards")
        
        # Specific recommendations based on violation patterns
        naming_violations = [v for v in violations if v.practice_id == "node_naming"]
        if len(naming_violations) > 5:
            recommendations.append("Implement consistent node naming convention across the project")
        
        performance_violations = [v for v in violations if 
                                self.practices[v.practice_id].category == PracticeCategory.PERFORMANCE]
        if len(performance_violations) > 3:
            recommendations.append("Focus on performance optimization to improve interactive experience")
        
        color_violations = [v for v in violations if 
                          self.practices[v.practice_id].category == PracticeCategory.COLOR_MANAGEMENT]
        if color_violations:
            recommendations.append("Review color management workflow to ensure accuracy")
        
        # Auto-fixable recommendations
        auto_fixable = [v for v in violations if v.auto_fixable]
        if len(auto_fixable) > 2:
            recommendations.append(f"{len(auto_fixable)} issues can be automatically fixed")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _identify_strengths(self, violations: List[PracticeViolation], 
                          context: Dict[str, Any]) -> List[str]:
        """Identify workflow strengths"""
        strengths = []
        
        # Check what's working well
        all_practices = set(self.practices.keys())
        violated_practices = set(v.practice_id for v in violations)
        good_practices = all_practices - violated_practices
        
        if "node_naming" in good_practices:
            strengths.append("Consistent node naming convention")
        
        if "color_space_management" in good_practices:
            strengths.append("Proper color space management")
        
        if "frame_range_consistency" in good_practices:
            strengths.append("Consistent frame range handling")
        
        if "bbox_optimization" in good_practices:
            strengths.append("Optimized bounding box usage")
        
        # Check for complex workflows with few violations
        nodes = context.get('nodes', [])
        if len(nodes) > 20 and len(violations) < 5:
            strengths.append("Well-organized complex workflow")
        
        return strengths
    
    def get_practice(self, practice_id: str) -> Optional[BestPractice]:
        """Get a specific best practice by ID"""
        return self.practices.get(practice_id)
    
    def get_practices_by_category(self, category: PracticeCategory) -> List[BestPractice]:
        """Get all practices in a category"""
        return [p for p in self.practices.values() if p.category == category]
    
    def get_applicable_practices(self, context: str) -> List[BestPractice]:
        """Get practices applicable to a specific context"""
        return [p for p in self.practices.values() 
                if "all" in p.applicable_contexts or context in p.applicable_contexts]
    
    def suggest_fixes(self, violation: PracticeViolation) -> List[str]:
        """Get suggested fixes for a violation"""
        practice = self.get_practice(violation.practice_id)
        if practice:
            return practice.fixes
        return []
    
    def get_practice_examples(self, practice_id: str) -> List[str]:
        """Get examples for a specific practice"""
        practice = self.get_practice(practice_id)
        if practice:
            return practice.examples
        return []
    
    def export_assessment(self, assessment: QualityAssessment, file_path: str) -> bool:
        """
        Export quality assessment to a file
        
        Args:
            assessment: The assessment to export
            file_path: Path to save the file
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            import json
            
            # Convert assessment to serializable format
            data = {
                'overall_score': assessment.overall_score,
                'category_scores': {cat.value: score for cat, score in assessment.category_scores.items()},
                'violations': [
                    {
                        'practice_id': v.practice_id,
                        'severity': v.severity.value,
                        'node_name': v.node_name,
                        'description': v.description,
                        'suggestion': v.suggestion,
                        'auto_fixable': v.auto_fixable
                    }
                    for v in assessment.violations
                ],
                'recommendations': assessment.recommendations,
                'strengths': assessment.strengths
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Assessment exported to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting assessment: {e}")
            return False