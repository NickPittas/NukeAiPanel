# Mistral Authentication Guide

This guide helps you troubleshoot and resolve authentication issues with the Mistral AI provider in the Nuke AI Panel.

## Common Issues

1. **Missing API Key**: The Mistral provider requires a valid API key to authenticate.
2. **Invalid API Key Format**: The API key must be in the correct format.
3. **Missing or Incorrectly Installed Mistral Library**: The `mistralai` Python package must be properly installed.
4. **Network Issues**: Your system must be able to connect to the Mistral API servers.

## Quick Fix

**The most common issue is the Mistral library not being properly installed.** To fix this:

1. Run the provided installation script:
   ```bash
   python install_mistral_library.py
   ```

2. Restart your application after installing the library

3. Try using the Mistral provider again

## Getting a Mistral API Key

1. Create an account at [Mistral AI](https://console.mistral.ai/)
2. Navigate to the API Keys section: https://console.mistral.ai/api-keys/
3. Create a new API key
4. Copy the API key (you won't be able to see it again)

## Fixing Authentication Issues

### Automatic Fix

Run the provided utility script to automatically diagnose and fix Mistral authentication issues:

```bash
python fix_mistral_authentication.py
```

This script will:
- Check if the Mistral library is installed
- Verify your API key configuration
- Test authentication with the Mistral API
- Provide detailed diagnostics if issues persist

### Manual Fix

If the automatic fix doesn't work, follow these steps:

1. **Install the Mistral library**:
   ```bash
   pip install mistralai
   ```

2. **Set your API key**:
   - Open the Nuke AI Panel settings
   - Navigate to the Providers section
   - Select Mistral
   - Enter your API key in the API Key field
   - Save the settings

3. **Verify the configuration**:
   - Check that the Mistral provider is enabled in the settings
   - Ensure the API key is correctly entered without extra spaces
   - Verify the endpoint is set to `https://api.mistral.ai` (default)

4. **Test authentication**:
   ```bash
   python test_mistral_authentication.py
   ```

## Troubleshooting

If you're still experiencing issues, check the following:

### 1. API Key Format

Mistral API keys are typically long strings (30+ characters). Make sure you've copied the entire key without any extra spaces or line breaks.

### 2. Library Installation

Verify the Mistral library is correctly installed:

```bash
pip show mistralai
```

If it's not installed or you see an error, install it:

```bash
pip install mistralai
```

### 3. Network Connectivity

Ensure your system can connect to the Mistral API:

```bash
curl -I https://api.mistral.ai
```

If you're behind a corporate firewall or proxy, you may need to configure your network settings.

### 4. Debug Logs

Enable debug logging to get more information:

1. Set the logging level to DEBUG in the configuration
2. Check the log files for detailed error messages
3. Look for specific authentication errors

## Advanced Diagnostics

For advanced troubleshooting, run the diagnostic function:

```python
from nuke_ai_panel.providers.mistral_provider import MistralProvider
import asyncio

async def run_diagnostics():
    provider = MistralProvider("mistral", {"api_key": "your-api-key"})
    diagnostics = await provider.diagnose_authentication()
    print(diagnostics)

asyncio.run(run_diagnostics())
```

## Support

If you continue to experience issues after following this guide, please:

1. Gather the diagnostic information from the scripts
2. Check the application logs for error messages
3. Contact support with these details for further assistance

## Compatibility

The Mistral provider has been tested with:
- mistralai library versions 0.0.1 and above
- Python 3.8 and above
- Windows, macOS, and Linux operating systems