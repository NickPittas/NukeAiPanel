"""
VFX Knowledge System

This module provides VFX-specific knowledge, workflows, and best practices
for AI-powered assistance in Nuke compositing.
"""

from .prompt_engine import VFXPromptEngine
from .workflow_database import WorkflowDatabase
from .best_practices import BestPracticesEngine
from .node_templates import NodeTemplateManager

__all__ = [
    'VFXPromptEngine',
    'WorkflowDatabase',
    'BestPracticesEngine',
    'NodeTemplateManager'
]