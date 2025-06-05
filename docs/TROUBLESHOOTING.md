# Troubleshooting Guide

Common issues and solutions for the Nuke AI Panel system.

## Table of Contents

- [Installation Issues](#installation-issues)
  - [Python Import Errors](#python-import-errors)
  - [Numpy Installation Issues on Python 3.13+](#numpy-installation-issues-on-python-313)
  - [Dependency Conflicts](#dependency-conflicts)
  - [Permission Errors](#permission-errors)
- [Authentication Problems](#authentication-problems)
- [Provider Connection Issues](#provider-connection-issues)
- [Nuke Integration Problems](#nuke-integration-problems)
- [Performance Issues](#performance-issues)
- [UI Problems](#ui-problems)
- [Configuration Issues](#configuration-issues)
- [Error Messages](#error-messages)
- [Debugging Tools](#debugging-tools)
- [Getting Help](#getting-help)

## Installation Issues

### Python Import Errors

**Problem:** `ModuleNotFoundError: No module named 'nuke_ai_panel'`

**Solutions:**
```bash
# Check if package is installed
pip list | grep nuke-ai-panel

# Reinstall package
pip uninstall nuke-ai-panel
pip install -e .

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Add to Python path if needed
export PYTHONPATH="${PYTHONPATH}:/path/to/nuke-ai-panel"
```

### Numpy Installation Issues on Python 3.13+

**Problem:** Error "Cannot import 'setuptools.build_meta'" when installing numpy on Python 3.13+

**Symptoms:**
```
ERROR: Could not build wheels for numpy, which is required to install pyproject.toml-based projects
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solutions:**
```bash
# Use the dedicated fix script
python fix_numpy_installation.py

# Or update setuptools and use binary wheels
pip install --upgrade setuptools wheel
pip install --only-binary=:all: numpy==1.24.4

# Try alternative numpy versions if needed
pip install --only-binary=:all: numpy==1.26.4
pip install --only-binary=:all: numpy==1.25.2
```

**Additional Information:**
See [NUMPY_INSTALLATION_FIX.md](NUMPY_INSTALLATION_FIX.md) for detailed instructions and more solutions.

### Dependency Conflicts

**Problem:** Package version conflicts during installation

**Solutions:**
```bash
# Create clean virtual environment
python -m venv fresh_env
source fresh_env/bin/activate  # Linux/macOS
# or
fresh_env\Scripts\activate  # Windows

# Install with specific versions
pip install -r requirements.txt --force-reinstall

# Check for conflicts
pip check
```

### Permission Errors

**Problem:** Permission denied during installation

**Solutions:**
```bash
# Install for current user only
pip install --user -e .

# Fix file permissions (Linux/macOS)
sudo chown -R $USER:$USER ~/.nuke_ai_panel/
chmod -R 755 ~/.nuke_ai_panel/

# Windows: Run as administrator or check folder permissions
```

## Authentication Problems

### API Key Not Working

**Problem:** Authentication fails with valid API key

**Diagnosis:**
```python
# Test API key directly
import os
from nuke_ai_panel.providers.openai_provider import OpenAIProvider

api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:10]}..." if api_key else "No API key found")

# Test authentication
provider = OpenAIProvider(api_key=api_key)
result = await provider.authenticate()
print(f"Auth result: {result}")
```

**Solutions:**
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Verify API key format
# OpenAI: sk-...
# Anthropic: sk-ant-...
# Google: starts with letters/numbers

# Test with curl
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### Encrypted Storage Issues

**Problem:** Cannot decrypt stored API keys

**Solutions:**
```python
# Reset encryption
from nuke_ai_panel.core.auth import AuthManager

auth_manager = AuthManager()
auth_manager.reset_encryption()

# Re-add API keys
auth_manager.set_api_key('openai', 'your-key')
```

### Multiple API Key Sources

**Problem:** Conflicting API keys from different sources

**Priority Order:**
1. Explicitly passed to provider
2. Environment variables
3. Configuration file
4. Encrypted storage

**Solution:**
```bash
# Clear all sources and use one method
unset OPENAI_API_KEY  # Clear env var
# Edit config file to remove api_key entries
# Use AuthManager for encrypted storage
```

## Provider Connection Issues

### Network Connectivity

**Problem:** Cannot connect to AI provider APIs

**Diagnosis:**
```bash
# Test basic connectivity
ping api.openai.com
ping api.anthropic.com

# Test HTTPS connectivity
curl -I https://api.openai.com/v1/models
curl -I https://api.anthropic.com/v1/messages

# Check for proxy/firewall issues
curl -v https://api.openai.com/v1/models
```

**Solutions:**
```bash
# Configure proxy if needed
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"

# Add to configuration
# config.yaml:
# advanced:
#   proxy:
#     http: "http://proxy.company.com:8080"
#     https: "http://proxy.company.com:8080"
```

### Rate Limiting

**Problem:** Rate limit exceeded errors

**Solutions:**
```python
# Check current rate limits
from nuke_ai_panel.core.config import Config

config = Config()
openai_limit = config.get('providers.openai.rate_limit', 60)
print(f"OpenAI rate limit: {openai_limit} requests/minute")

# Adjust rate limits
config.set('providers.openai.rate_limit', 30)  # Reduce limit
config.save()
```

### Timeout Issues

**Problem:** Requests timing out

**Solutions:**
```yaml
# Increase timeouts in config.yaml
providers:
  openai:
    timeout: 60  # Increase from 30
  ollama:
    timeout: 300  # Local models need more time
```

### Ollama Connection Issues

**Problem:** Cannot connect to local Ollama instance

**Diagnosis:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Check available models
curl http://localhost:11434/api/tags

# Test generation
curl http://localhost:11434/api/generate \
  -d '{"model":"llama2","prompt":"Hello","stream":false}'
```

**Solutions:**
```bash
# Start Ollama service
ollama serve

# Pull required model
ollama pull llama2

# Check custom endpoint in config
# config.yaml:
# providers:
#   ollama:
#     custom_endpoint: "http://localhost:11434"
```

## Nuke Integration Problems

### Panel Not Appearing

**Problem:** AI Panel doesn't appear in Nuke's Windows menu

**Solutions:**
```python
# Check if files are in correct location
import os
nuke_dir = os.path.expanduser("~/.nuke")
panel_dir = os.path.join(nuke_dir, "nuke_ai_panel")
print(f"Panel directory exists: {os.path.exists(panel_dir)}")

# Check menu.py integration
menu_file = os.path.join(nuke_dir, "menu.py")
if os.path.exists(menu_file):
    with open(menu_file, 'r') as f:
        content = f.read()
        if "nuke_ai_panel" in content:
            print("Menu integration found")
        else:
            print("Menu integration missing")
```

### Python Path Issues in Nuke

**Problem:** Nuke can't find the AI Panel modules

**Solutions:**
```python
# Add to Nuke's init.py or menu.py
import sys
import os

# Add AI Panel to Python path
ai_panel_path = os.path.expanduser("~/.nuke/nuke_ai_panel")
if ai_panel_path not in sys.path:
    sys.path.insert(0, ai_panel_path)

# Verify import works
try:
    from src.ui.main_panel import NukeAIPanel
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
```

### Nuke Version Compatibility

**Problem:** Features not working with specific Nuke versions

**Solutions:**
```python
# Check Nuke version
import nuke
version = nuke.NUKE_VERSION_STRING
major_version = int(version.split('.')[0])

print(f"Nuke version: {version}")
print(f"Major version: {major_version}")

# Enable compatibility mode for older versions
if major_version < 14:
    print("Using legacy compatibility mode")
    # Disable newer features
```

### UI Layout Issues

**Problem:** Panel layout broken or not displaying correctly

**Solutions:**
```python
# Reset panel layout
import nuke
nuke.resetPanelLayout()

# Clear Nuke preferences (backup first!)
# Delete ~/.nuke/preferences13.2.nk (or appropriate version)

# Force panel refresh
panel = NukeAIPanel()
panel.refresh_layout()
```

## Performance Issues

### Slow Response Times

**Problem:** AI responses taking too long

**Diagnosis:**
```python
import time
from nuke_ai_panel.core.base_provider import Message, MessageRole

# Time a request
start_time = time.time()
messages = [Message(role=MessageRole.USER, content="Hello")]
response = await provider_manager.generate_text(messages=messages)
end_time = time.time()

print(f"Response time: {end_time - start_time:.2f} seconds")
```

**Solutions:**
```yaml
# Optimize configuration
providers:
  openai:
    timeout: 15  # Reduce timeout
    rate_limit: 100  # Increase if allowed

cache:
  enabled: true
  max_size: 2000  # Increase cache size
  ttl_seconds: 7200  # Longer cache TTL

advanced:
  max_concurrent_requests: 10  # Increase concurrency
```

### Memory Usage

**Problem:** High memory consumption

**Solutions:**
```python
# Monitor memory usage
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_mb:.1f} MB")

# Reduce cache size
from nuke_ai_panel.core.config import Config
config = Config()
config.set('cache.max_size', 500)  # Reduce from 1000
config.save()

# Clear cache periodically
from nuke_ai_panel.utils.cache import CacheManager
cache = CacheManager()
cache.clear()
```

### Cache Issues

**Problem:** Cache not working or causing issues

**Solutions:**
```python
# Clear cache
from nuke_ai_panel.utils.cache import CacheManager
cache = CacheManager()
cache.clear()

# Disable cache temporarily
from nuke_ai_panel.core.config import Config
config = Config()
config.set('cache.enabled', False)

# Check cache statistics
stats = cache.get_stats()
print(f"Cache hits: {stats['hits']}")
print(f"Cache misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## UI Problems

### Panel Not Responding

**Problem:** UI becomes unresponsive

**Solutions:**
```python
# Force refresh
panel = NukeAIPanel()
panel.refresh()

# Reset UI state
panel.reset_state()

# Check for blocking operations
# Ensure all AI calls are async and don't block UI thread
```

### Font/Display Issues

**Problem:** Text not displaying correctly

**Solutions:**
```yaml
# Adjust UI settings in config.yaml
ui:
  font_size: 14  # Increase font size
  theme: "light"  # Try different theme
  
# Force font refresh in Nuke
import nuke
nuke.refreshFonts()
```

### Chat History Issues

**Problem:** Chat history not saving or loading

**Solutions:**
```python
# Check session manager
from src.core.session_manager import SessionManager

session_manager = SessionManager()
sessions = session_manager.list_sessions()
print(f"Available sessions: {sessions}")

# Clear corrupted history
session_manager.clear_history()

# Check file permissions
import os
history_dir = os.path.expanduser("~/.nuke_ai_panel/sessions")
print(f"History directory writable: {os.access(history_dir, os.W_OK)}")
```

## Configuration Issues

### Config File Not Loading

**Problem:** Configuration changes not taking effect

**Solutions:**
```python
# Check config file location
from nuke_ai_panel.core.config import Config

config = Config()
print(f"Config file path: {config.config_path}")
print(f"Config file exists: {os.path.exists(config.config_path)}")

# Force reload
config.load()

# Validate config format
import yaml
try:
    with open(config.config_path, 'r') as f:
        yaml.safe_load(f)
    print("Config file is valid YAML")
except yaml.YAMLError as e:
    print(f"Config file YAML error: {e}")
```

### Environment Variables Not Working

**Problem:** Environment variables not being read

**Solutions:**
```python
# Check environment variables
import os

env_vars = [
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'GOOGLE_API_KEY',
    'NUKE_AI_PANEL_CONFIG'
]

for var in env_vars:
    value = os.getenv(var)
    print(f"{var}: {'Set' if value else 'Not set'}")

# Set in current session
os.environ['OPENAI_API_KEY'] = 'your-key'
```

## Error Messages

### Common Error Patterns

#### "Authentication failed"
```python
# Check API key format and validity
# Verify network connectivity
# Check rate limits
```

#### "Model not found"
```python
# List available models
models = await provider.get_models()
for model in models:
    print(f"Available: {model.id}")
```

#### "Rate limit exceeded"
```python
# Reduce request frequency
# Check rate limit configuration
# Wait before retrying
```

#### "Connection timeout"
```python
# Increase timeout values
# Check network connectivity
# Verify proxy settings
```

## Debugging Tools

### Enable Debug Logging

```python
# Set debug level
from nuke_ai_panel.core.config import Config

config = Config()
config.set('logging.level', 'DEBUG')
config.save()

# Or via environment variable
import os
os.environ['NUKE_AI_PANEL_LOG_LEVEL'] = 'DEBUG'
```

### Health Check Tool

```python
# Run comprehensive health check
from nuke_ai_panel.core.provider_manager import ProviderManager

async def health_check():
    provider_manager = ProviderManager()
    health = await provider_manager.health_check()
    
    for provider, status in health.items():
        print(f"{provider}: {status}")
        if not status.healthy:
            print(f"  Error: {status.error}")
            print(f"  Details: {status.details}")

import asyncio
asyncio.run(health_check())
```

### Configuration Validator

```python
# Validate configuration
from nuke_ai_panel.core.config import Config

def validate_config():
    config = Config()
    
    # Check required settings
    required_settings = [
        'providers.openai.enabled',
        'cache.enabled',
        'logging.level'
    ]
    
    for setting in required_settings:
        value = config.get(setting)
        print(f"{setting}: {value}")
        
    # Check API keys
    from nuke_ai_panel.core.auth import AuthManager
    auth = AuthManager()
    providers = auth.list_providers()
    print(f"Providers with API keys: {providers}")

validate_config()
```

### Network Diagnostics

```python
# Test network connectivity
import aiohttp
import asyncio

async def test_connectivity():
    endpoints = [
        'https://api.openai.com/v1/models',
        'https://api.anthropic.com/v1/messages',
        'https://generativelanguage.googleapis.com/v1/models',
        'http://localhost:11434/api/version'  # Ollama
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                async with session.get(endpoint, timeout=10) as response:
                    print(f"{endpoint}: {response.status}")
            except Exception as e:
                print(f"{endpoint}: Error - {e}")

asyncio.run(test_connectivity())
```

## Getting Help

### Before Reporting Issues

1. **Check this troubleshooting guide**
2. **Search existing issues** on GitHub
3. **Run diagnostic tools** provided above
4. **Collect relevant information**:
   - Operating system and version
   - Python version
   - Nuke version
   - Complete error messages
   - Steps to reproduce

### Information to Include

```python
# System information script
import sys
import platform
import nuke_ai_panel

print("=== System Information ===")
print(f"OS: {platform.system()} {platform.release()}")
print(f"Python: {sys.version}")
print(f"Nuke AI Panel: {nuke_ai_panel.__version__}")

try:
    import nuke
    print(f"Nuke: {nuke.NUKE_VERSION_STRING}")
except ImportError:
    print("Nuke: Not available")

print("\n=== Configuration ===")
from nuke_ai_panel.core.config import Config
config = Config()
print(f"Config file: {config.config_path}")

print("\n=== Providers ===")
from nuke_ai_panel.core.auth import AuthManager
auth = AuthManager()
providers = auth.list_providers()
print(f"Configured providers: {providers}")
```

### Support Channels

1. **GitHub Issues**: For bugs and feature requests
2. **GitHub Discussions**: For questions and community help
3. **Documentation**: Check API reference and guides
4. **Email Support**: For enterprise/commercial support

### Creating Good Bug Reports

```markdown
## Bug Report Template

**Environment:**
- OS: [Windows 11 / macOS 13 / Ubuntu 22.04]
- Python: [3.9.7]
- Nuke: [14.0v5]
- Nuke AI Panel: [1.0.0]

**Description:**
Clear description of the issue

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
```
Complete error traceback here
```

**Additional Context:**
Any other relevant information
```

---

If your issue isn't covered here, please check the [GitHub Issues](https://github.com/your-repo/nuke-ai-panel/issues) or create a new issue with detailed information.