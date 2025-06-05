"""
Nuke AI Panel - Main Package

Complete AI-powered assistant for Nuke with chat interface, provider management,
VFX knowledge integration, and safe action execution capabilities.
"""

import logging
import sys
import os

# Add the package root to Python path for imports
package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_root not in sys.path:
    sys.path.insert(0, package_root)

# Version information
__version__ = "1.0.0"
__author__ = "Nuke AI Panel Team"
__description__ = "AI-powered assistant for Nuke with comprehensive VFX knowledge"

# Import main components
from .ui.main_panel import NukeAIPanel, create_ai_panel, register_panel
from .core.panel_manager import PanelManager
from .core.session_manager import SessionManager
from .core.action_engine import ActionEngine
from .menu import initialize_nuke_integration, get_menu_integration

# Import UI components
from .ui.chat_interface import ChatInterface
from .ui.settings_dialog import SettingsDialog
from .ui.action_preview import ActionPreviewDialog

# Import integration components
from .nuke_integration.context_analyzer import NukeContextAnalyzer
from .nuke_integration.script_generator import ScriptGenerator
from .nuke_integration.action_applier import ActionApplier
from .nuke_integration.node_inspector import NodeInspector

# Import VFX knowledge components
from .vfx_knowledge.prompt_engine import PromptEngine
from .vfx_knowledge.workflow_database import WorkflowDatabase
from .vfx_knowledge.best_practices import BestPracticesEngine
from .vfx_knowledge.node_templates import NodeTemplateManager

# Setup logging
def setup_logging(level=logging.INFO):
    """Set up logging for the AI Panel."""
    logger = logging.getLogger('nuke_ai_panel')
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger

# Initialize logging
logger = setup_logging()

# Check Nuke availability
try:
    import nuke
    import nukescripts
    NUKE_AVAILABLE = True
    logger.info("Nuke environment detected")
except ImportError:
    NUKE_AVAILABLE = False
    logger.warning("Nuke not available - some features will be disabled")

# Main initialization function
def initialize():
    """Initialize the Nuke AI Panel system."""
    try:
        logger.info(f"Initializing Nuke AI Panel v{__version__}")
        
        # Initialize Nuke integration if available
        if NUKE_AVAILABLE:
            success = initialize_nuke_integration()
            if success:
                logger.info("Nuke integration initialized successfully")
            else:
                logger.warning("Nuke integration initialization failed")
        
        # Initialize core components
        logger.info("Core components initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Nuke AI Panel: {e}")
        return False

# Convenience functions for external use
def show_panel():
    """Show the AI Assistant panel."""
    if NUKE_AVAILABLE:
        try:
            nukescripts.showPanel("com.nukeaipanel.AIAssistant")
        except Exception as e:
            logger.error(f"Failed to show panel: {e}")
    else:
        logger.warning("Cannot show panel - Nuke not available")

def create_panel():
    """Create a new AI Panel instance."""
    try:
        return create_ai_panel()
    except Exception as e:
        logger.error(f"Failed to create panel: {e}")
        return None

def get_version():
    """Get the current version."""
    return __version__

def get_info():
    """Get package information."""
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'nuke_available': NUKE_AVAILABLE,
        'components': {
            'ui': ['main_panel', 'chat_interface', 'settings_dialog', 'action_preview'],
            'core': ['panel_manager', 'session_manager', 'action_engine'],
            'nuke_integration': ['context_analyzer', 'script_generator', 'action_applier', 'node_inspector'],
            'vfx_knowledge': ['prompt_engine', 'workflow_database', 'best_practices', 'node_templates']
        }
    }

# Export main components
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',
    
    # Main functions
    'initialize',
    'show_panel',
    'create_panel',
    'get_version',
    'get_info',
    
    # UI Components
    'NukeAIPanel',
    'ChatInterface',
    'SettingsDialog',
    'ActionPreviewDialog',
    
    # Core Components
    'PanelManager',
    'SessionManager',
    'ActionEngine',
    
    # Integration Components
    'ContextAnalyzer',
    'ScriptGenerator',
    'ActionApplier',
    'NodeInspector',
    
    # VFX Knowledge Components
    'PromptEngine',
    'WorkflowDatabase',
    'BestPracticesEngine',
    'NodeTemplateManager',
    
    # Utilities
    'setup_logging',
    'NUKE_AVAILABLE'
]

# Auto-initialize if imported in Nuke
if NUKE_AVAILABLE and __name__ != '__main__':
    try:
        # Check if we're in Nuke's GUI environment
        if hasattr(nuke, 'env') and nuke.env.get('gui'):
            initialize()
    except Exception as e:
        logger.error(f"Auto-initialization failed: {e}")

# Command-line interface for testing
if __name__ == '__main__':
    print(f"Nuke AI Panel v{__version__}")
    print(f"Nuke Available: {NUKE_AVAILABLE}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'info':
            import json
            print(json.dumps(get_info(), indent=2))
        elif command == 'test':
            print("Running basic tests...")
            success = initialize()
            print(f"Initialization: {'SUCCESS' if success else 'FAILED'}")
        elif command == 'version':
            print(__version__)
        else:
            print(f"Unknown command: {command}")
            print("Available commands: info, test, version")
    else:
        print("Use 'python -m src info' for package information")