# Installation Guide

This guide provides step-by-step instructions for installing the Nuke AI Panel in various environments and Nuke versions.

## Table of Contents

- [System Requirements](#system-requirements)
- [Pre-Installation Checklist](#pre-installation-checklist)
- [Installation Methods](#installation-methods)
- [Nuke Version Compatibility](#nuke-version-compatibility)
- [Configuration Setup](#configuration-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Nuke**: 13.0 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 1GB free space
- **Network**: Internet connection for AI providers

### Recommended Requirements
- **Python**: 3.9 or higher
- **Nuke**: 14.0 or higher
- **RAM**: 16GB or more
- **Storage**: 5GB free space (for cache and logs)
- **GPU**: CUDA-compatible GPU (for local AI models)

### Operating System Support
- **Windows**: 10/11 (64-bit)
- **macOS**: 10.15 (Catalina) or higher
- **Linux**: Ubuntu 18.04+, CentOS 7+, RHEL 7+

## Pre-Installation Checklist

### 1. Verify Python Installation

```bash
# Check Python version
python --version
# or
python3 --version

# Should output Python 3.8.x or higher
```

### 2. Verify Nuke Installation

```bash
# Check Nuke installation path
# Windows
echo %NUKE_PATH%

# macOS/Linux
echo $NUKE_PATH
```

### 3. Check Network Connectivity

```bash
# Test internet connection
ping google.com

# Test AI provider endpoints
curl -I https://api.openai.com/v1/models
curl -I https://api.anthropic.com/v1/messages
```

## Installation Methods

### Method 1: Automated Installation (Recommended)

The automated installer handles all setup steps including Nuke integration.

```bash
# Clone the repository
git clone https://github.com/your-repo/nuke-ai-panel.git
cd nuke-ai-panel

# Run the automated installer
python deploy/install_script.py

# Follow the interactive prompts
```

#### Automated Installation Options

```bash
# Development installation
python deploy/install_script.py --environment development

# Production installation
python deploy/install_script.py --environment production

# Studio installation (multi-user)
python deploy/install_script.py --environment studio

# Custom Nuke path
python deploy/install_script.py --nuke-path "/path/to/nuke"

# Skip Nuke integration (Python package only)
python deploy/install_script.py --no-nuke-integration
```

### Method 2: Manual Installation

For advanced users who prefer manual control over the installation process.

#### Step 1: Install Python Package

```bash
# Clone repository
git clone https://github.com/your-repo/nuke-ai-panel.git
cd nuke-ai-panel

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install package
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Nuke Integration

```bash
# Find Nuke plugins directory
# Windows: %USERPROFILE%\.nuke\
# macOS: ~/.nuke/
# Linux: ~/.nuke/

# Copy source files
cp -r src/ ~/.nuke/nuke_ai_panel/

# Copy menu integration
cp src/menu.py ~/.nuke/menu.py
```

#### Step 3: Configuration

```bash
# Create configuration directory
mkdir -p ~/.nuke_ai_panel

# Copy default configuration
cp config/default_config.yaml ~/.nuke_ai_panel/config.yaml

# Edit configuration as needed
nano ~/.nuke_ai_panel/config.yaml
```

### Method 3: Docker Installation

For containerized environments or testing.

```bash
# Build Docker image
docker build -t nuke-ai-panel .

# Run container
docker run -it --name nuke-ai-panel \
  -v ~/.nuke_ai_panel:/root/.nuke_ai_panel \
  -p 8080:8080 \
  nuke-ai-panel
```

## Nuke Version Compatibility

### Supported Versions

| Nuke Version | Support Level | Notes |
|--------------|---------------|-------|
| 15.0+ | Full Support | All features available |
| 14.0-14.1 | Full Support | Recommended version |
| 13.2-13.2v9 | Full Support | Stable support |
| 13.0-13.1 | Limited Support | Some UI limitations |
| 12.x | Not Supported | Use legacy version |

### Version-Specific Installation

#### Nuke 15.0+

```bash
# Standard installation
python deploy/install_script.py --nuke-version 15.0

# Enable new features
python deploy/install_script.py --nuke-version 15.0 --enable-experimental
```

#### Nuke 14.x

```bash
# Standard installation
python deploy/install_script.py --nuke-version 14.0

# Compatibility mode for older 14.x versions
python deploy/install_script.py --nuke-version 14.0 --compatibility-mode
```

#### Nuke 13.x

```bash
# Legacy support installation
python deploy/install_script.py --nuke-version 13.2 --legacy-mode

# Manual Python path configuration may be required
export NUKE_PYTHON_PATH="/path/to/python3.8"
```

## Configuration Setup

### 1. API Keys Configuration

#### Method A: Environment Variables (Recommended)

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export OPENAI_API_KEY="sk-your-openai-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"
export GOOGLE_API_KEY="your-google-api-key-here"
export OPENROUTER_API_KEY="sk-or-your-openrouter-key-here"
export MISTRAL_API_KEY="your-mistral-api-key-here"

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc
```

#### Method B: Configuration File

```yaml
# Edit ~/.nuke_ai_panel/config.yaml
providers:
  openai:
    enabled: true
    api_key: "sk-your-openai-key-here"
  anthropic:
    enabled: true
    api_key: "sk-ant-your-anthropic-key-here"
```

#### Method C: Interactive Setup

```bash
# Run configuration wizard
python -c "from nuke_ai_panel.core.auth import AuthManager; AuthManager().setup_wizard()"
```

### 2. Provider-Specific Setup

#### OpenAI Setup

```bash
# Verify API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Test connection
python -c "
from nuke_ai_panel.providers.openai_provider import OpenAIProvider
import asyncio
async def test():
    provider = OpenAIProvider()
    result = await provider.authenticate()
    print(f'OpenAI connection: {result}')
asyncio.run(test())
"
```

#### Anthropic Setup

```bash
# Verify API key
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/messages \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

#### Ollama Setup (Local AI)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model
ollama pull llama2

# Test connection
curl http://localhost:11434/api/generate \
  -d '{"model":"llama2","prompt":"Hello","stream":false}'
```

### 3. Studio Configuration

For multi-user studio environments:

```bash
# Install for all users
sudo python deploy/install_script.py --environment studio --global

# Create shared configuration
sudo mkdir -p /etc/nuke_ai_panel
sudo cp config/studio_config.yaml /etc/nuke_ai_panel/config.yaml

# Set permissions
sudo chown -R nuke:nuke /etc/nuke_ai_panel
sudo chmod 755 /etc/nuke_ai_panel
sudo chmod 644 /etc/nuke_ai_panel/config.yaml
```

## Verification

### 1. Python Package Verification

```bash
# Test import
python -c "import nuke_ai_panel; print('Package imported successfully')"

# Check version
python -c "from nuke_ai_panel import __version__; print(f'Version: {__version__}')"

# Run basic tests
python -m pytest tests/test_basic.py -v
```

### 2. Nuke Integration Verification

```python
# In Nuke's Script Editor
import sys
sys.path.append('/path/to/nuke_ai_panel')

try:
    from src.ui.main_panel import NukeAIPanel
    print("Nuke AI Panel imported successfully")
    
    # Test panel creation (don't show yet)
    panel = NukeAIPanel()
    print("Panel created successfully")
    
except Exception as e:
    print(f"Error: {e}")
```

### 3. AI Provider Verification

```bash
# Run provider tests
python -c "
import asyncio
from nuke_ai_panel.core.provider_manager import ProviderManager
from nuke_ai_panel.core.config import Config
from nuke_ai_panel.core.auth import AuthManager

async def test_providers():
    config = Config()
    auth = AuthManager()
    manager = ProviderManager(config=config, auth_manager=auth)
    
    health = await manager.health_check()
    for provider, status in health.items():
        print(f'{provider}: {status}')

asyncio.run(test_providers())
"
```

## Post-Installation Steps

### 1. First Launch

```python
# In Nuke, go to Windows menu -> Custom -> AI Panel
# Or run in Script Editor:
from src.ui.main_panel import NukeAIPanel
panel = NukeAIPanel()
panel.show()
```

### 2. Initial Configuration

1. Open the AI Panel in Nuke
2. Go to Settings tab
3. Configure your preferred AI providers
4. Test connection to each provider
5. Set default models and parameters

### 3. Performance Optimization

```bash
# Enable caching for better performance
python -c "
from nuke_ai_panel.core.config import Config
config = Config()
config.set('cache.enabled', True)
config.set('cache.max_size', 2000)
config.save()
"

# Optimize for your hardware
python deploy/optimize_config.py --auto-detect
```

## Troubleshooting

### Common Issues

#### 1. Python Import Errors

```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Add to Nuke's Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/nuke_ai_panel"
```

#### 2. Nuke Integration Issues

```python
# Check Nuke Python version
import sys
print(f"Nuke Python version: {sys.version}")

# Verify Nuke paths
import nuke
print(f"Nuke version: {nuke.NUKE_VERSION_STRING}")
print(f"Plugin path: {nuke.pluginPath()}")
```

#### 3. API Connection Issues

```bash
# Test network connectivity
curl -v https://api.openai.com/v1/models

# Check firewall/proxy settings
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
```

#### 4. Permission Issues

```bash
# Fix file permissions
chmod -R 755 ~/.nuke/nuke_ai_panel/
chmod -R 644 ~/.nuke_ai_panel/

# Fix ownership (Linux/macOS)
chown -R $USER:$USER ~/.nuke_ai_panel/
```

### Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Search [GitHub Issues](https://github.com/your-repo/nuke-ai-panel/issues)
3. Create a new issue with:
   - Operating system and version
   - Nuke version
   - Python version
   - Complete error messages
   - Steps to reproduce

### Uninstallation

```bash
# Automated uninstallation
python deploy/uninstall_script.py

# Manual uninstallation
rm -rf ~/.nuke/nuke_ai_panel/
rm -rf ~/.nuke_ai_panel/
pip uninstall nuke-ai-panel
```

---

**Next Steps**: After successful installation, see the [API Reference](API_REFERENCE.md) for detailed usage instructions.