"""
Complete Nuke AI Panel Example

This example demonstrates how to use the complete AI Panel system,
including UI components, core managers, and integration features.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
except ImportError:
    # Create minimal fallback for testing without Qt
    class QApplication:
        def __init__(self, args): pass
        def exec_(self): return 0
        @staticmethod
        def instance(): return None
    
    class QTimer:
        @staticmethod
        def singleShot(interval, callback): callback()

# Import the AI Panel components
from src.ui.main_panel import NukeAIPanel
from src.core.panel_manager import PanelManager
from src.ui.settings_dialog import SettingsDialog
from src.ui.action_preview import ActionPreviewDialog


def create_standalone_demo():
    """Create a standalone demo of the AI Panel (without Nuke)."""
    
    print("Creating Nuke AI Panel Demo...")
    
    # Create Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create the main panel
    panel = NukeAIPanel()
    panel.show()
    
    # Demo some features
    def demo_features():
        """Demonstrate various panel features."""
        try:
            # Simulate adding a message
            if panel.chat_interface:
                panel.chat_interface.add_user_message("Hello, AI Assistant!")
                panel.chat_interface.add_ai_message(
                    "Hello! I'm your AI assistant for VFX and compositing in Nuke. "
                    "I can help you with:\n\n"
                    "• Creating and connecting nodes\n"
                    "• VFX techniques and workflows\n"
                    "• Script optimization\n"
                    "• Best practices\n\n"
                    "Here's an example script to create a basic comp setup:\n\n"
                    "```python\n"
                    "# Create a basic comp setup\n"
                    "read = nuke.createNode('Read')\n"
                    "read['file'].setValue('/path/to/your/image.exr')\n"
                    "\n"
                    "grade = nuke.createNode('Grade')\n"
                    "grade.setInput(0, read)\n"
                    "\n"
                    "write = nuke.createNode('Write')\n"
                    "write.setInput(0, grade)\n"
                    "write['file'].setValue('/path/to/output.exr')\n"
                    "```\n\n"
                    "Would you like me to explain any part of this setup?"
                )
                
            print("Demo messages added to chat interface")
            
        except Exception as e:
            print(f"Demo feature error: {e}")
    
    # Schedule demo features after a short delay
    QTimer.singleShot(1000, demo_features)
    
    return app, panel


def demo_settings_dialog():
    """Demonstrate the settings dialog."""
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create settings dialog
    settings = SettingsDialog()
    settings.show()
    
    print("Settings dialog created")
    return app, settings


def demo_action_preview():
    """Demonstrate the action preview dialog."""
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Sample code for preview
    sample_code = """
# Create a basic keying setup
bg = nuke.createNode('Read')
bg['file'].setValue('/path/to/background.exr')

fg = nuke.createNode('Read') 
fg['file'].setValue('/path/to/foreground.exr')

# Create keyer
keyer = nuke.createNode('Primatte')
keyer.setInput(0, fg)

# Merge with background
merge = nuke.createNode('Merge')
merge.setInput(0, bg)  # Background (A input)
merge.setInput(1, keyer)  # Foreground (B input)

# Final grade
grade = nuke.createNode('Grade')
grade.setInput(0, merge)

print("Keying setup created successfully!")
"""
    
    # Create action preview dialog
    preview = ActionPreviewDialog(sample_code)
    preview.show()
    
    print("Action preview dialog created")
    return app, preview


def run_complete_demo():
    """Run a complete demonstration of all components."""
    
    print("=" * 60)
    print("Nuke AI Panel - Complete Demo")
    print("=" * 60)
    
    try:
        # Create the main demo
        app, panel = create_standalone_demo()
        
        print(f"Main panel created: {panel}")
        print(f"Panel manager: {panel.get_panel_manager()}")
        
        # Add some demo interactions
        def show_additional_demos():
            """Show additional demo dialogs."""
            try:
                # Show settings after 3 seconds
                QTimer.singleShot(3000, lambda: demo_settings_dialog())
                
                # Show action preview after 5 seconds
                QTimer.singleShot(5000, lambda: demo_action_preview())
                
            except Exception as e:
                print(f"Additional demo error: {e}")
        
        # Schedule additional demos
        QTimer.singleShot(2000, show_additional_demos)
        
        print("\nDemo Features:")
        print("- Main AI Panel with chat interface")
        print("- Settings dialog (opens after 3 seconds)")
        print("- Action preview dialog (opens after 5 seconds)")
        print("- Sample chat messages")
        print("\nClose any window to exit the demo.")
        
        # Run the application
        return app.exec_()
        
    except Exception as e:
        print(f"Demo failed: {e}")
        return 1


def test_components():
    """Test individual components without GUI."""
    
    print("Testing AI Panel Components...")
    
    try:
        # Test imports
        print("✓ UI components imported successfully")
        
        # Test panel manager creation
        panel_manager = PanelManager()
        print("✓ Panel manager created")
        
        # Test available providers
        providers = panel_manager.get_available_providers()
        print(f"✓ Available providers: {providers}")
        
        # Test configuration
        config = panel_manager.get_config()
        print(f"✓ Configuration loaded: {len(config)} settings")
        
        print("\nAll component tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Component test failed: {e}")
        return False


if __name__ == '__main__':
    print("Nuke AI Panel - Complete Example")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'demo':
            # Run GUI demo
            exit_code = run_complete_demo()
            sys.exit(exit_code)
            
        elif command == 'test':
            # Run component tests
            success = test_components()
            sys.exit(0 if success else 1)
            
        elif command == 'settings':
            # Show only settings dialog
            app, settings = demo_settings_dialog()
            sys.exit(app.exec_())
            
        elif command == 'preview':
            # Show only action preview
            app, preview = demo_action_preview()
            sys.exit(app.exec_())
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  demo     - Run complete GUI demo")
            print("  test     - Run component tests")
            print("  settings - Show settings dialog only")
            print("  preview  - Show action preview only")
            
    else:
        print("\nUsage:")
        print("  python complete_panel_example.py demo     # GUI demo")
        print("  python complete_panel_example.py test     # Component tests")
        print("  python complete_panel_example.py settings # Settings dialog")
        print("  python complete_panel_example.py preview  # Action preview")
        
        # Default to component test
        test_components()