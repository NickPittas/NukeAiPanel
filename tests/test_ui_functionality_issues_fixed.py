#!/usr/bin/env python
"""
Test script to verify that the UI button functionality issues have been fixed.

This script tests:
1. Preview Action Button - Verifies that QRegularExpression is properly implemented
2. Copy Code Button - Verifies that the copy feedback mechanism works
"""

import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, 'src')

# Check if we can run the GUI test
has_pyside6 = False
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
    from PySide6.QtCore import Qt
    has_pyside6 = True
except ImportError:
    logger.warning("PySide6 not available - will run non-GUI tests only")

# Import our modules
from ui.action_preview import ActionPreviewDialog, QRegularExpression
from ui.chat_interface import MessageWidget

# Test QRegularExpression implementation
def test_qregularexpression():
    """Test QRegularExpression implementation"""
    try:
        # Create a QRegularExpression instance
        regex = QRegularExpression("test")
        
        # Test match method
        match = regex.match("test string")
        
        # Test globalMatch method
        match_iterator = regex.globalMatch("test string with test pattern")
        
        logger.info("✅ QRegularExpression implementation test passed")
        return True
    except Exception as e:
        logger.error(f"❌ QRegularExpression implementation test failed: {e}")
        return False

# Run non-GUI tests
logger.info("Starting tests...")
test_results = []

# Test QRegularExpression
test_results.append(("QRegularExpression", test_qregularexpression()))

# Print results
for test_name, result in test_results:
    status = "✅ PASSED" if result else "❌ FAILED"
    logger.info(f"{test_name}: {status}")

# Only run GUI tests if PySide6 is available
if has_pyside6:
    # Create application
    app = QApplication(sys.argv)
    
    # Test window
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("UI Functionality Test")
            self.setGeometry(100, 100, 800, 600)
            
            # Central widget
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            # Status label
            self.status = QLabel("Running tests...")
            self.status.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.status)
            
            # Test buttons
            test_preview_btn = QPushButton("Test Preview Action Button")
            test_preview_btn.clicked.connect(self.test_preview_action)
            layout.addWidget(test_preview_btn)
            
            test_copy_btn = QPushButton("Test Copy Code Button")
            test_copy_btn.clicked.connect(self.test_copy_code)
            layout.addWidget(test_copy_btn)
            
            # Results
            self.results = QLabel("")
            self.results.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.results.setWordWrap(True)
            layout.addWidget(self.results)
            
            # Run tests automatically
            self.run_all_tests()
            
        def run_all_tests(self):
            """Run all tests automatically"""
            self.results.setText("")
            self.add_result("Starting automated tests...")
            
            # Test QRegularExpression implementation
            self.test_qregularexpression()
            
            # Test preview action
            self.test_preview_action()
            
            # Test copy code
            self.test_copy_code()
            
            self.status.setText("Tests completed")
            
        def add_result(self, message):
            """Add a message to the results"""
            current = self.results.text()
            self.results.setText(f"{current}\n{message}")
            logger.info(message)
            
        def test_qregularexpression(self):
            """Test QRegularExpression implementation"""
            try:
                # Create a QRegularExpression instance
                regex = QRegularExpression("test")
                
                # Test match method
                match = regex.match("test string")
                
                # Test globalMatch method
                match_iterator = regex.globalMatch("test string with test pattern")
                
                self.add_result("✅ QRegularExpression implementation test passed")
                return True
            except Exception as e:
                self.add_result(f"❌ QRegularExpression implementation test failed: {e}")
                return False
                
        def test_preview_action(self):
            """Test preview action button functionality"""
            try:
                # Create a simple Python code for testing
                test_code = """import nuke\n\n# Create a Blur node\nblur = nuke.createNode('Blur')\nblur['size'].setValue(10)"""
                
                # Create dialog
                dialog = ActionPreviewDialog(test_code)
                
                # Test syntax highlighting (this uses QRegularExpression)
                highlighter = dialog.highlighter
                
                # If we got here without errors, the test passed
                self.add_result("✅ Preview Action Button test passed")
                return True
            except Exception as e:
                self.add_result(f"❌ Preview Action Button test failed: {e}")
                return False
                
        def test_copy_code(self):
            """Test copy code button functionality"""
            try:
                # Create a message with code
                message = "Here's a simple Nuke script:\n```python\nimport nuke\nblur = nuke.createNode('Blur')\n```"
                timestamp = datetime.now()
                
                # Create message widget
                msg_widget = MessageWidget(message, False, timestamp)
                
                # Test extract_code method
                code = msg_widget.extract_code()
                if not code:
                    raise ValueError("Failed to extract code from message")
                
                # Test copy_code method (this should use the clipboard)
                msg_widget.copy_code()
                
                # Test show_copy_feedback method
                msg_widget.show_copy_feedback()
                
                # If we got here without errors, the test passed
                self.add_result("✅ Copy Code Button test passed")
                return True
            except Exception as e:
                self.add_result(f"❌ Copy Code Button test failed: {e}")
                return False
    
    # Create and show the test window
    window = TestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())
else:
    logger.info("GUI tests skipped - PySide6 not available")
    logger.info("All available tests completed")