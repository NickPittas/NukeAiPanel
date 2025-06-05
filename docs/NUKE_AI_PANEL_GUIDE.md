# Nuke AI Panel - Complete Installation and Usage Guide

## Overview

The Nuke AI Panel is a comprehensive AI-powered assistant for Nuke that provides intelligent help for VFX and compositing tasks. It features a chat interface, multiple AI provider support, VFX knowledge integration, and safe execution of AI-generated scripts.

## Features

### Core Features
- **AI Chat Interface**: Real-time chat with AI about VFX techniques and workflows
- **Multiple AI Providers**: Support for OpenAI, Anthropic, Google, Mistral, Ollama, and OpenRouter
- **Context-Aware Assistance**: AI understands your current Nuke script and provides relevant suggestions
- **Safe Code Execution**: Preview and validate AI-generated scripts before applying them
- **VFX Knowledge Base**: Access to best practices, workflows, and node templates
- **Session Management**: Persistent chat history and context

### UI Components
- **Main Panel**: Primary interface with chat, provider selection, and settings
- **Chat Interface**: Message history, input field, and action buttons
- **Settings Dialog**: Configuration for API keys, providers, and preferences
- **Action Preview**: Safe preview and execution of AI-generated code

### Safety Features
- **Code Analysis**: Automatic safety analysis of AI-generated scripts
- **Dry Run Mode**: Test scripts without making changes
- **Undo Support**: Safe execution with rollback capabilities
- **Confirmation Dialogs**: User confirmation for potentially dangerous operations

## Installation

### Prerequisites
- Nuke 11.0 or later
- Python 3.6 or later
- Internet connection for AI provider APIs

### Step 1: Download and Extract
1. Download the Nuke AI Panel package
2. Extract to your Nuke plugins directory:
   - **Windows**: `C:\Users\[username]\.nuke\`
   - **macOS**: `/Users/[username]/.nuke/`
   - **Linux**: `/home/[username]/.nuke/`

### Step 2: Install Dependencies
```bash
# Navigate to the package directory
cd /path/to/NukeAiPanel

# Install required Python packages
pip install -r requirements.txt
```

### Step 3: Nuke Integration
Add the following to your `menu.py` file in the `.nuke` directory:

```python
# Add Nuke AI Panel
import sys
import os

# Add the AI Panel path
ai_panel_path = os.path.join(os.path.expanduser("~/.nuke"), "NukeAiPanel")
if ai_panel_path not in sys.path:
    sys.path.append(ai_panel_path)

# Initialize the AI Panel
try:
    import src
    src.initialize()
    print("Nuke AI Panel loaded successfully")
except Exception as e:
    print(f"Failed to load Nuke AI Panel: {e}")
```

### Step 4: Restart Nuke
Restart Nuke to load the AI Panel. You should see "AI Assistant" in the main menu.

## Configuration

### First-Time Setup
1. Open Nuke
2. Go to **AI Assistant > Show Panel**
3. Click the settings button (gear icon) in the panel
4. Configure your AI provider:

#### OpenAI Configuration
- **API Key**: Your OpenAI API key
- **Model**: `gpt-4-turbo-preview` (recommended)
- **Temperature**: 0.7 (default)
- **Max Tokens**: 2000 (default)

#### Anthropic Configuration
- **API Key**: Your Anthropic API key
- **Model**: `claude-3-sonnet-20240229` (recommended)
- **Temperature**: 0.7 (default)
- **Max Tokens**: 2000 (default)

#### Other Providers
Similar configuration for Google, Mistral, Ollama, and OpenRouter.

### API Key Setup
1. **OpenAI**: Get your API key from https://platform.openai.com/api-keys
2. **Anthropic**: Get your API key from https://console.anthropic.com/
3. **Google**: Get your API key from Google AI Studio
4. **Others**: Follow respective provider documentation

## Usage

### Basic Chat
1. Open the AI Assistant panel
2. Select your preferred AI provider and model
3. Type your question in the input field
4. Press **Ctrl+Enter** to send (or click Send)

### Example Conversations

#### Getting Help with Compositing
```
User: How do I create a realistic fire effect in Nuke?

AI: I'll help you create a realistic fire effect in Nuke. Here's a comprehensive approach:

1. **Base Fire Element**:
   - Use a Noise node with Turbulence for the base fire shape
   - Animate the noise over time for movement
   - Use ColorCorrect to create orange/red/yellow gradients

2. **Fire Core Script**:
```python
# Create fire effect nodes
noise = nuke.createNode('Noise')
noise['size'].setValue(50)
noise['zoffset'].setValue('frame*0.1')

# Add turbulence
turbulence = nuke.createNode('Turbulence')
turbulence.setInput(0, noise)
turbulence['size'].setValue(20)
turbulence['offset'].setValue('frame*0.05')
```

[Preview Action] [Copy Code]
```

#### Script Analysis
```
User: Can you analyze my current Nuke script and suggest optimizations?

AI: I'll analyze your current script. Let me examine the node structure...

**Current Script Analysis**:
- 23 nodes total
- 3 Read nodes detected
- Multiple ColorCorrect nodes that could be consolidated
- Potential optimization opportunities found

**Suggestions**:
1. Merge similar ColorCorrect operations
2. Use expression linking for repeated values
3. Consider using a single Grade node instead of multiple ColorCorrects

Would you like me to generate an optimized version?
```

### Context-Aware Features

#### Adding Current Context
1. Click **Add Context** button
2. AI will analyze your current Nuke script
3. Provides context-aware suggestions

#### Using Workflows
1. Click **Workflows** button
2. Browse available VFX workflows
3. Select a workflow to get specific guidance

### Action Preview and Execution

When the AI suggests code:
1. Click **Preview Action** to see what the code will do
2. Review the safety analysis
3. Use **Dry Run** to test without changes
4. Click **Apply Action** to execute

### Safety Features

#### Code Analysis
- **Green indicator**: Safe to execute
- **Yellow indicator**: Requires caution
- **Red indicator**: Potentially dangerous

#### Safety Checks
- Syntax validation
- Dangerous operation detection
- Scene impact analysis
- Runtime estimation

## Advanced Features

### Session Management
- **Auto-save**: Chat history is automatically saved
- **Session switching**: Load previous conversations
- **Export**: Save chat history to files

### Custom Workflows
Add your own workflows to the VFX knowledge base:

```python
# Example custom workflow
workflow = {
    "name": "Custom Keying Workflow",
    "description": "Advanced keying technique",
    "steps": [
        "Create Primatte node",
        "Adjust spill suppression",
        "Add edge refinement"
    ]
}
```

### Keyboard Shortcuts
- **Ctrl+Shift+A**: Open AI Assistant panel
- **Ctrl+Enter**: Send message in chat
- **Enter**: New line in message input

## Troubleshooting

### Common Issues

#### Panel Not Loading
1. Check Python path configuration
2. Verify all dependencies are installed
3. Check Nuke console for error messages

#### API Connection Issues
1. Verify API key is correct
2. Check internet connection
3. Confirm API provider service status

#### Code Execution Failures
1. Review safety analysis warnings
2. Check Nuke script compatibility
3. Use dry run mode for testing

### Debug Mode
Enable debug logging in settings:
1. Go to Settings > Advanced
2. Set Log Level to "DEBUG"
3. Check console output for detailed information

### Log Files
Logs are stored in:
- **Windows**: `%USERPROFILE%\.nuke\ai_panel_logs\`
- **macOS/Linux**: `~/.nuke/ai_panel_logs/`

## Best Practices

### Effective AI Interaction
1. **Be Specific**: Provide clear, detailed questions
2. **Add Context**: Use the context button for script-specific help
3. **Iterate**: Build on previous responses for complex tasks
4. **Verify**: Always review AI-generated code before applying

### Safety Guidelines
1. **Preview First**: Always preview actions before applying
2. **Backup Scripts**: Save your work before major changes
3. **Test Incrementally**: Apply changes step by step
4. **Use Dry Run**: Test complex operations safely

### Performance Tips
1. **Manage Sessions**: Clear old chat history periodically
2. **Optimize Queries**: Be concise but specific
3. **Use Appropriate Models**: Choose models based on task complexity

## API Usage and Costs

### Token Management
- Monitor token usage in provider dashboards
- Use shorter conversations for simple queries
- Clear context when switching topics

### Cost Optimization
- Use smaller models for simple questions
- Implement rate limiting in settings
- Monitor monthly usage limits

## Support and Community

### Getting Help
1. Check this guide first
2. Review error messages and logs
3. Test with different AI providers
4. Check provider API status

### Contributing
The Nuke AI Panel is designed to be extensible:
- Add custom VFX workflows
- Extend the knowledge base
- Create custom node templates
- Contribute safety patterns

## Updates and Maintenance

### Updating the Panel
1. Download the latest version
2. Replace existing files
3. Restart Nuke
4. Check for new features in settings

### Maintenance Tasks
- Clear old session files periodically
- Update API keys as needed
- Review and update safety patterns
- Backup custom configurations

## Conclusion

The Nuke AI Panel transforms your VFX workflow by providing intelligent, context-aware assistance directly within Nuke. With proper setup and usage, it becomes an invaluable tool for both beginners learning VFX techniques and experts looking to optimize their workflows.

For the best experience:
- Keep your API keys secure and up to date
- Regularly update the panel for new features
- Engage with the AI conversationally for better results
- Always prioritize safety when executing generated code

Happy compositing with AI assistance!