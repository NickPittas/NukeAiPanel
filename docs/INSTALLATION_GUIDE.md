# Nuke AI Panel - Installation Guide

This guide provides detailed instructions for installing and configuring the Nuke AI Panel with all its dependencies.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
   - [Automatic Installation](#automatic-installation)
   - [Manual Installation](#manual-installation)
3. [Provider Setup](#provider-setup)
   - [OpenAI](#openai)
   - [Anthropic](#anthropic)
   - [Google](#google)
   - [Mistral](#mistral)
   - [Ollama](#ollama)
   - [OpenRouter](#openrouter)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Uninstallation](#uninstallation)

## Prerequisites

Before installing the Nuke AI Panel, ensure you have the following:

- **Nuke**: The panel is designed to work with Nuke 13.0 or later.
- **Python**: Python 3.8 or later (included with Nuke).
- **Internet Connection**: Required for downloading packages and accessing AI services.
- **API Keys**: You'll need API keys for the AI providers you plan to use.

## Installation

### Automatic Installation

The easiest way to install all dependencies is using the provided installation script:

1. Open a terminal or command prompt
2. Navigate to the Nuke AI Panel directory
3. Run the installation script:

```bash
python install_all_dependencies.py
```

This script will:
- Install all required dependencies for all providers
- Provide setup instructions for each provider
- Verify the installation was successful

#### Installation Options

The installation script supports several options:

- `--check-only`: Only check if dependencies are installed, don't install anything
- `--skip-optional`: Skip installation of optional dependencies
- `--upgrade`: Upgrade packages to the latest version

Example:
```bash
python install_all_dependencies.py --skip-optional
```

### Manual Installation

If you prefer to install dependencies manually, you can use pip to install the required packages:

#### Core Dependencies

```bash
pip install aiohttp==3.9.1 asyncio-throttle==1.0.2 cryptography==41.0.7 pydantic==2.5.2 pyyaml==6.0.1 python-dotenv==1.0.0
pip install tenacity==8.2.3 cachetools==5.3.2 colorlog==6.8.0 aiofiles==23.2.1 httpx==0.25.2
```

#### Provider-Specific Dependencies

```bash
# OpenAI
pip install openai==1.6.1

# Anthropic
pip install anthropic==0.8.1

# Google
pip install google-generativeai==0.3.2

# Mistral
pip install mistralai==0.1.2

# Ollama
pip install ollama==0.1.7
```

#### Optional Dependencies

```bash
# UI dependencies (for standalone mode)
pip install PySide6==6.6.1

# Data processing (requires C compiler)
pip install numpy==1.24.4 pandas==2.1.4

# Enhanced logging
pip install structlog==23.2.0 rich==13.7.0
```

> **Note:** Some packages like numpy and pandas require a C compiler for installation from source. If you encounter compilation errors, you can:
> 1. Install a C compiler (Visual C++ Build Tools on Windows, gcc on Linux, Xcode Command Line Tools on macOS)
> 2. Use pre-built wheels with `pip install --only-binary=:all: numpy pandas`
> 3. Use a distribution like Anaconda that includes pre-compiled versions of these packages

## Provider Setup

Each AI provider requires specific setup steps, typically involving API keys.

### OpenAI

1. Create an account at [OpenAI](https://platform.openai.com/)
2. Navigate to [API Keys](https://platform.openai.com/api-keys)
3. Create a new API key
4. Set the environment variable:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   Or add it to your `.env` file in the project directory

### Anthropic

1. Create an account at [Anthropic](https://console.anthropic.com/)
2. Navigate to [API Keys](https://console.anthropic.com/settings/keys)
3. Create a new API key
4. Set the environment variable:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```
   Or add it to your `.env` file in the project directory

### Google

1. Create an account at [Google AI Studio](https://makersuite.google.com/)
2. Navigate to [API Keys](https://makersuite.google.com/app/apikey)
3. Create a new API key
4. Set the environment variable:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
   Or add it to your `.env` file in the project directory

### Mistral

1. Create an account at [Mistral AI](https://console.mistral.ai/)
2. Navigate to [API Keys](https://console.mistral.ai/api-keys/)
3. Create a new API key
4. Set the environment variable:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```
   Or add it to your `.env` file in the project directory

### Ollama

Ollama runs locally on your machine and doesn't require an API key.

1. Download and install Ollama from [ollama.ai/download](https://ollama.ai/download)
2. Start the Ollama service
3. Pull models you want to use:
   ```bash
   ollama pull llama2
   ollama pull mistral
   ollama pull codellama
   ```

### OpenRouter

1. Create an account at [OpenRouter](https://openrouter.ai/)
2. Navigate to [API Keys](https://openrouter.ai/keys)
3. Create a new API key
4. Set the environment variable:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```
   Or add it to your `.env` file in the project directory

## Verification

To verify that all dependencies are installed correctly:

```bash
python install_all_dependencies.py --check-only
```

This will check all required and optional dependencies and report their status.

## Troubleshooting

### Common Issues

#### Installation Failures

If package installation fails:

1. Check your internet connection
2. Ensure you have the necessary permissions to install packages
3. Try installing the package manually:
   ```bash
   pip install package_name
   ```
4. Check for version conflicts with existing packages

##### Compilation Errors

For packages that require compilation (like numpy and pandas):

1. **Windows:**
   - Install Visual C++ Build Tools from the [Microsoft website](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Select "C++ build tools" during installation

2. **Linux:**
   - Install the required development packages:
     ```bash
     # Ubuntu/Debian
     sudo apt-get install build-essential python3-dev
     
     # Fedora/RHEL/CentOS
     sudo dnf install gcc gcc-c++ python3-devel
     ```

3. **macOS:**
   - Install Xcode Command Line Tools:
     ```bash
     xcode-select --install
     ```

4. **Alternative Solution:**
   - Use pre-built wheels:
     ```bash
     pip install --only-binary=:all: numpy pandas
     ```
   - Or use Anaconda/Miniconda which includes pre-compiled packages

#### API Connection Issues

If you can't connect to an AI provider:

1. Verify your API key is correct
2. Check if the service is experiencing downtime
3. Ensure your network allows connections to the API endpoints
4. Check if your API key has sufficient credits/quota

#### Nuke Integration Issues

If the panel doesn't appear in Nuke:

1. Ensure the panel is installed in the correct Nuke plugins directory
2. Check Nuke's script editor for Python errors
3. Verify that all dependencies are installed in Nuke's Python environment
4. Restart Nuke after installation

### Getting Help

If you encounter issues not covered in this guide:

1. Check the project's GitHub issues
2. Consult the documentation
3. Reach out to the community for support

## Uninstallation

To uninstall the Nuke AI Panel and its dependencies:

1. Remove the panel files from your Nuke plugins directory
2. Uninstall dependencies if no longer needed:
   ```bash
   pip uninstall -y openai anthropic google-generativeai mistralai ollama
   pip uninstall -y aiohttp asyncio-throttle cryptography pydantic pyyaml python-dotenv
   ```

Note that this will only remove the packages if they're not used by other applications.