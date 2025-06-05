#!/usr/bin/env python3
"""
Test script to debug and fix final connectivity issues with AI providers.

This script will:
1. Debug API key loading from configuration
2. Check for missing Python libraries
3. Test provider connectivity
4. Create dependency installation guide
"""

import sys
import os
import json
import importlib
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

def test_library_imports():
    """Test if required libraries are available for each provider."""
    print("🔍 Testing library imports for each provider...")
    
    library_requirements = {
        'mistral': ['mistralai'],
        'openrouter': ['openai', 'aiohttp'],  # OpenRouter uses OpenAI-compatible API
        'ollama': ['aiohttp'],
        'openai': ['openai'],
        'anthropic': ['anthropic'],
        'google': ['google-generativeai']
    }
    
    missing_libraries = {}
    
    for provider, libraries in library_requirements.items():
        print(f"\n📦 Testing {provider} provider libraries:")
        provider_missing = []
        
        for lib in libraries:
            try:
                importlib.import_module(lib)
                print(f"  ✅ {lib} - Available")
            except ImportError:
                print(f"  ❌ {lib} - Missing")
                provider_missing.append(lib)
        
        if provider_missing:
            missing_libraries[provider] = provider_missing
    
    return missing_libraries

def test_config_loading():
    """Test configuration loading and API key access."""
    print("\n🔧 Testing configuration loading...")
    
    try:
        from nuke_ai_panel.core.config import Config
        
        # Initialize config
        config = Config()
        print("✅ Config manager initialized")
        
        # Test provider configurations
        providers = ['openai', 'anthropic', 'google', 'mistral', 'ollama', 'openrouter']
        
        for provider in providers:
            print(f"\n🔍 Testing {provider} configuration:")
            
            # Get provider config
            provider_config = config.get_provider_config(provider)
            print(f"  📋 Config object: {type(provider_config)}")
            print(f"  🔑 API key present: {'Yes' if provider_config.api_key else 'No'}")
            print(f"  ⚙️  Enabled: {provider_config.enabled}")
            print(f"  🎯 Default model: {provider_config.default_model}")
            
            # Check raw config data
            raw_config = config.get(f"providers.{provider}", {})
            print(f"  📊 Raw config keys: {list(raw_config.keys())}")
            
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_provider_initialization():
    """Test provider initialization with current configuration."""
    print("\n🚀 Testing provider initialization...")
    
    try:
        from nuke_ai_panel.core.config import Config
        from nuke_ai_panel.core.provider_manager import ProviderManager
        
        # Initialize components
        config = Config()
        provider_manager = ProviderManager(config)
        
        print("✅ Provider manager initialized")
        
        # Test each provider
        available_providers = provider_manager.get_available_providers()
        print(f"📋 Available providers: {available_providers}")
        
        for provider_name in available_providers:
            print(f"\n🔍 Testing {provider_name} provider:")
            
            # Get provider instance
            provider = provider_manager.get_provider(provider_name)
            if provider:
                print(f"  ✅ Provider instance created")
                print(f"  🔐 Authenticated: {provider.is_authenticated}")
                
                # Check if API key is loaded
                api_key = getattr(provider, 'api_key', None)
                print(f"  🔑 API key loaded: {'Yes' if api_key else 'No'}")
                if api_key:
                    print(f"  🔑 API key preview: {api_key[:8]}..." if len(api_key) > 8 else "  🔑 API key too short")
            else:
                print(f"  ❌ Provider instance not created")
                
        return True
        
    except Exception as e:
        print(f"❌ Provider initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_dependency_installer():
    """Create a script to install missing dependencies."""
    print("\n📦 Creating dependency installer...")
    
    installer_script = '''#!/usr/bin/env python3
"""
Dependency installer for Nuke AI Panel providers.

This script installs the required Python libraries for each AI provider.
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install dependencies for all providers."""
    print("🚀 Installing Nuke AI Panel dependencies...")
    
    # Core dependencies (always needed)
    core_deps = [
        "aiohttp",  # For HTTP requests
        "pyyaml",   # For configuration files
    ]
    
    # Provider-specific dependencies
    provider_deps = {
        "OpenAI": ["openai"],
        "Anthropic": ["anthropic"],
        "Google": ["google-generativeai"],
        "Mistral": ["mistralai"],
        "OpenRouter": ["openai"],  # Uses OpenAI-compatible API
        "Ollama": [],  # No additional deps needed (uses aiohttp)
    }
    
    print("\\n📦 Installing core dependencies...")
    for dep in core_deps:
        print(f"Installing {dep}...")
        if install_package(dep):
            print(f"✅ {dep} installed successfully")
        else:
            print(f"❌ Failed to install {dep}")
    
    print("\\n🤖 Installing provider dependencies...")
    for provider, deps in provider_deps.items():
        if deps:
            print(f"\\n{provider} provider:")
            for dep in deps:
                print(f"  Installing {dep}...")
                if install_package(dep):
                    print(f"  ✅ {dep} installed successfully")
                else:
                    print(f"  ❌ Failed to install {dep}")
        else:
            print(f"\\n{provider} provider: No additional dependencies needed")
    
    print("\\n🎉 Dependency installation complete!")
    print("\\nYou can now configure your API keys in the settings dialog.")

if __name__ == "__main__":
    main()
'''
    
    with open('install_dependencies.py', 'w') as f:
        f.write(installer_script)
    
    print("✅ Created install_dependencies.py")
    return True

def create_api_key_config_fix():
    """Create a fix for API key configuration loading."""
    print("\n🔧 Creating API key configuration fix...")
    
    # First, let's check if there's a configuration file and what it contains
    try:
        from nuke_ai_panel.core.config import Config
        config = Config()
        
        # Check if config file exists
        if config.config_file.exists():
            print(f"📁 Config file found: {config.config_file}")
            
            # Load and display current config
            with open(config.config_file, 'r') as f:
                if config.config_file.suffix == '.json':
                    current_config = json.load(f)
                else:
                    # Try to load as YAML or JSON
                    content = f.read()
                    try:
                        import yaml
                        current_config = yaml.safe_load(content)
                    except:
                        current_config = json.loads(content)
            
            print("📋 Current configuration structure:")
            for provider in ['openai', 'anthropic', 'google', 'mistral', 'ollama', 'openrouter']:
                if provider in current_config.get('providers', {}):
                    provider_config = current_config['providers'][provider]
                    has_api_key = 'api_key' in provider_config and provider_config['api_key']
                    print(f"  {provider}: API key {'✅ present' if has_api_key else '❌ missing'}")
                else:
                    print(f"  {provider}: ❌ not configured")
        else:
            print("📁 No config file found - will be created on first run")
            
    except Exception as e:
        print(f"❌ Error checking config: {e}")
    
    return True

def test_provider_connection_status():
    """Test the connection status logic for providers."""
    print("\n🔗 Testing provider connection status...")
    
    try:
        from nuke_ai_panel.core.config import Config
        from nuke_ai_panel.core.provider_manager import ProviderManager
        
        config = Config()
        provider_manager = ProviderManager(config)
        
        # Test connection status
        is_connected = provider_manager.is_connected()
        print(f"📡 Overall connection status: {'✅ Connected' if is_connected else '❌ Not connected'}")
        
        # Test individual provider status
        provider_status = provider_manager.get_provider_status()
        
        for provider_name, status in provider_status.items():
            print(f"\n🔍 {provider_name} status:")
            print(f"  📡 Available: {status.available}")
            print(f"  🔐 Authenticated: {status.authenticated}")
            print(f"  ⚡ Enabled: {status.enabled}")
            if status.error_message:
                print(f"  ❌ Error: {status.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection status test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_provider_config_template():
    """Create a template configuration with placeholder API keys."""
    print("\n📝 Creating provider configuration template...")
    
    template_config = {
        "version": "1.0",
        "default_provider": "openai",
        "providers": {
            "openai": {
                "name": "openai",
                "enabled": True,
                "api_key": "",  # User needs to fill this
                "default_model": "gpt-4",
                "base_url": "https://api.openai.com/v1",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "anthropic": {
                "name": "anthropic",
                "enabled": True,
                "api_key": "",  # User needs to fill this
                "default_model": "claude-3-sonnet-20240229",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "google": {
                "name": "google",
                "enabled": True,
                "api_key": "",  # User needs to fill this
                "default_model": "gemini-pro",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "mistral": {
                "name": "mistral",
                "enabled": True,
                "api_key": "",  # User needs to fill this
                "default_model": "mistral-medium",
                "base_url": "https://api.mistral.ai",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            },
            "ollama": {
                "name": "ollama",
                "enabled": True,
                "api_key": "",  # Optional for local Ollama
                "default_model": "llama2",
                "base_url": "http://localhost:11434",
                "max_retries": 3,
                "timeout": 60
            },
            "openrouter": {
                "name": "openrouter",
                "enabled": True,
                "api_key": "",  # User needs to fill this
                "default_model": "openai/gpt-4",
                "base_url": "https://openrouter.ai/api/v1",
                "max_retries": 3,
                "timeout": 30,
                "rate_limit": 60
            }
        },
        "cache": {
            "enabled": True,
            "max_size": 1000,
            "ttl_seconds": 3600
        },
        "logging": {
            "level": "INFO",
            "file_logging": True,
            "console_logging": True
        }
    }
    
    # Save template
    with open('config_template.json', 'w') as f:
        json.dump(template_config, f, indent=2)
    
    print("✅ Created config_template.json")
    print("📋 Users can copy this template and fill in their API keys")
    
    return True

def main():
    """Run all connectivity tests and create fixes."""
    print("🔍 NUKE AI PANEL - CONNECTIVITY DEBUG & FIX")
    print("=" * 50)
    
    # Test 1: Library imports
    missing_libs = test_library_imports()
    
    # Test 2: Configuration loading
    config_ok = test_config_loading()
    
    # Test 3: Provider initialization
    providers_ok = test_provider_initialization()
    
    # Test 4: Connection status
    connection_ok = test_provider_connection_status()
    
    # Create fixes
    print("\n🛠️  CREATING FIXES...")
    print("=" * 30)
    
    create_dependency_installer()
    create_api_key_config_fix()
    create_provider_config_template()
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 20)
    
    if missing_libs:
        print("❌ Missing libraries detected:")
        for provider, libs in missing_libs.items():
            print(f"  {provider}: {', '.join(libs)}")
        print("💡 Run: python install_dependencies.py")
    else:
        print("✅ All required libraries are available")
    
    print(f"📋 Configuration loading: {'✅ OK' if config_ok else '❌ Failed'}")
    print(f"🚀 Provider initialization: {'✅ OK' if providers_ok else '❌ Failed'}")
    print(f"🔗 Connection status: {'✅ OK' if connection_ok else '❌ Failed'}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Install missing dependencies: python install_dependencies.py")
    print("2. Configure API keys in the settings dialog")
    print("3. Test provider connections")
    
    return True

if __name__ == "__main__":
    main()