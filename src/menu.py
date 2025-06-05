"""
Nuke Menu Integration

This module handles the integration of the AI Panel into Nuke's menu system
and provides panel registration and initialization functionality.
"""

import logging
from typing import Optional

try:
    import nuke
    import nukescripts
    NUKE_AVAILABLE = True
except ImportError:
    NUKE_AVAILABLE = False
    print("Warning: Nuke not available - menu integration disabled")

from .ui.main_panel import NukeAIPanel, create_ai_panel


class MenuIntegration:
    """Handles Nuke menu integration for the AI Panel."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.panel_registered = False
        
    def register_panel(self) -> bool:
        """Register the AI panel with Nuke."""
        if not NUKE_AVAILABLE:
            self.logger.warning("Nuke not available - cannot register panel")
            return False
            
        try:
            # Register the panel with Nuke
            nukescripts.registerPanel(
                'com.nukeaipanel.AIAssistant',
                create_ai_panel
            )
            
            self.panel_registered = True
            self.logger.info("AI Panel registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register AI panel: {e}")
            return False
            
    def create_menu_items(self):
        """Create menu items for the AI Panel."""
        if not NUKE_AVAILABLE:
            return
            
        try:
            # Get the main Nuke menu
            nuke_menu = nuke.menu('Nuke')
            
            # Create AI Assistant submenu
            ai_menu = nuke_menu.addMenu('AI Assistant')
            
            # Add panel show command
            ai_menu.addCommand(
                'Show Panel',
                'nukescripts.showPanel("com.nukeaipanel.AIAssistant")',
                tooltip='Show the AI Assistant panel'
            )
            
            # Add separator
            ai_menu.addSeparator()
            
            # Add quick actions
            ai_menu.addCommand(
                'Quick Chat',
                self.quick_chat_action,
                tooltip='Open AI chat in a dialog'
            )
            
            ai_menu.addCommand(
                'Analyze Current Script',
                self.analyze_script_action,
                tooltip='Get AI analysis of the current Nuke script'
            )
            
            ai_menu.addCommand(
                'VFX Best Practices',
                self.best_practices_action,
                tooltip='Get VFX best practices recommendations'
            )
            
            # Add separator
            ai_menu.addSeparator()
            
            # Add settings
            ai_menu.addCommand(
                'Settings...',
                self.show_settings_action,
                tooltip='Configure AI Assistant settings'
            )
            
            # Add help
            ai_menu.addCommand(
                'Help',
                self.show_help_action,
                tooltip='Show AI Assistant help'
            )
            
            self.logger.info("AI Assistant menu created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create menu items: {e}")
            
    def quick_chat_action(self):
        """Handle quick chat action."""
        try:
            from .ui.chat_interface import ChatInterface
            from .core.panel_manager import PanelManager
            
            # Create a dialog with chat interface
            dialog = nuke.Panel('AI Quick Chat')
            dialog.setWidth(500)
            
            # For now, just show a message
            nuke.message("Quick Chat feature - coming soon!\n\nUse the main AI Panel for full functionality.")
            
        except Exception as e:
            self.logger.error(f"Quick chat action failed: {e}")
            nuke.message(f"Quick chat failed: {e}")
            
    def analyze_script_action(self):
        """Handle script analysis action."""
        try:
            from .nuke_integration.context_analyzer import ContextAnalyzer
            
            # Get current script context
            analyzer = ContextAnalyzer()
            context = analyzer.get_full_context()
            
            if not context:
                nuke.message("No script loaded or script is empty.")
                return
                
            # Show analysis in a dialog
            dialog = nuke.Panel('Script Analysis')
            dialog.setWidth(600)
            
            # For now, show basic info
            script_info = f"Current Script Analysis:\n\n{context[:500]}..."
            nuke.message(script_info)
            
        except Exception as e:
            self.logger.error(f"Script analysis action failed: {e}")
            nuke.message(f"Script analysis failed: {e}")
            
    def best_practices_action(self):
        """Handle best practices action."""
        try:
            from .vfx_knowledge.best_practices import BestPracticesEngine
            
            # Get best practices
            bp_engine = BestPracticesEngine()
            practices = bp_engine.get_general_practices()
            
            if practices:
                practices_text = "VFX Best Practices:\n\n"
                for practice in practices[:5]:  # Show first 5
                    practices_text += f"• {practice}\n"
                    
                nuke.message(practices_text)
            else:
                nuke.message("Best practices database not available.")
                
        except Exception as e:
            self.logger.error(f"Best practices action failed: {e}")
            nuke.message(f"Best practices failed: {e}")
            
    def show_settings_action(self):
        """Handle settings action."""
        try:
            # Try to get existing panel and show its settings
            try:
                panel = nukescripts.findPanel('com.nukeaipanel.AIAssistant')
                if panel:
                    panel.show_settings()
                    return
            except:
                pass
                
            # If no panel exists, show message
            nuke.message("Please open the AI Assistant panel first to access settings.")
            
        except Exception as e:
            self.logger.error(f"Settings action failed: {e}")
            nuke.message(f"Settings failed: {e}")
            
    def show_help_action(self):
        """Handle help action."""
        try:
            help_text = """
AI Assistant for Nuke - Help

The AI Assistant provides intelligent help for VFX and compositing tasks in Nuke.

Features:
• Chat with AI about VFX techniques and workflows
• Get context-aware suggestions based on your current Nuke script
• Preview and apply AI-generated scripts safely
• Access VFX best practices and workflows
• Multiple AI provider support (OpenAI, Anthropic, etc.)

Getting Started:
1. Open the AI Assistant panel from the menu
2. Configure your AI provider settings
3. Start chatting about your VFX needs!

Keyboard Shortcuts:
• Ctrl+Enter: Send message
• Enter: New line in message

Safety Features:
• All AI-generated code is analyzed for safety
• Preview actions before applying them
• Undo support for most operations

For more help, visit the documentation or ask the AI directly!
            """
            
            nuke.message(help_text.strip())
            
        except Exception as e:
            self.logger.error(f"Help action failed: {e}")
            nuke.message(f"Help failed: {e}")
            
    def add_toolbar_button(self):
        """Add AI Assistant button to Nuke toolbar."""
        if not NUKE_AVAILABLE:
            return
            
        try:
            # Add to the main toolbar
            toolbar = nuke.toolbar("Nodes")
            
            # Create AI Assistant button
            toolbar.addCommand(
                "AI Assistant",
                'nukescripts.showPanel("com.nukeaipanel.AIAssistant")',
                tooltip="Open AI Assistant Panel",
                icon="AIAssistant.png"  # You would need to provide this icon
            )
            
            self.logger.info("AI Assistant toolbar button added")
            
        except Exception as e:
            self.logger.error(f"Failed to add toolbar button: {e}")
            
    def register_keyboard_shortcuts(self):
        """Register keyboard shortcuts for AI Assistant."""
        if not NUKE_AVAILABLE:
            return
            
        try:
            # Register Ctrl+Shift+A to open AI panel
            nuke.menu('Nuke').addCommand(
                'AI Assistant/Show Panel',
                'nukescripts.showPanel("com.nukeaipanel.AIAssistant")',
                'ctrl+shift+a'
            )
            
            self.logger.info("AI Assistant keyboard shortcuts registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register keyboard shortcuts: {e}")
            
    def setup_startup_callback(self):
        """Set up callback to initialize AI panel on Nuke startup."""
        if not NUKE_AVAILABLE:
            return
            
        try:
            def on_nuke_startup():
                """Callback function for Nuke startup."""
                try:
                    # Initialize AI panel components
                    self.logger.info("Initializing AI Assistant on startup")
                    
                    # You could add any startup initialization here
                    # For example, loading default settings, checking for updates, etc.
                    
                except Exception as e:
                    self.logger.error(f"AI Assistant startup initialization failed: {e}")
                    
            # Add the callback
            nuke.addOnCreate(on_nuke_startup, nodeClass='Root')
            
        except Exception as e:
            self.logger.error(f"Failed to setup startup callback: {e}")
            
    def initialize_full_integration(self):
        """Initialize complete Nuke integration."""
        if not NUKE_AVAILABLE:
            self.logger.warning("Nuke not available - skipping integration")
            return False
            
        try:
            self.logger.info("Initializing AI Assistant Nuke integration...")
            
            # Register the panel
            if not self.register_panel():
                return False
                
            # Create menu items
            self.create_menu_items()
            
            # Add toolbar button (optional)
            # self.add_toolbar_button()
            
            # Register keyboard shortcuts
            self.register_keyboard_shortcuts()
            
            # Setup startup callback
            self.setup_startup_callback()
            
            self.logger.info("AI Assistant Nuke integration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Nuke integration: {e}")
            return False


# Global menu integration instance
_menu_integration = None


def initialize_nuke_integration():
    """Initialize the Nuke integration."""
    global _menu_integration
    
    if _menu_integration is None:
        _menu_integration = MenuIntegration()
        
    return _menu_integration.initialize_full_integration()


def get_menu_integration() -> Optional[MenuIntegration]:
    """Get the menu integration instance."""
    return _menu_integration


# Auto-initialize if this module is imported in Nuke
if NUKE_AVAILABLE:
    try:
        # Check if we're in Nuke's Python environment
        if hasattr(nuke, 'env') and nuke.env.get('gui'):
            # We're in Nuke GUI mode, initialize integration
            initialize_nuke_integration()
    except Exception as e:
        print(f"AI Assistant auto-initialization failed: {e}")