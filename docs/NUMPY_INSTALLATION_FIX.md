# Numpy Installation Fix for Python 3.13+

This document explains how to fix the "Cannot import 'setuptools.build_meta'" error when installing numpy on Python 3.13 or newer versions.

## The Issue

When trying to install numpy on Python 3.13+, you might encounter an error like this:

```
ERROR: Could not build wheels for numpy, which is required to install pyproject.toml-based projects
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
ERROR: Cannot install numpy==1.24.4 because these package versions have conflicting dependencies.
```

This happens because Python 3.13 introduced changes to the build system that affect how packages with C extensions (like numpy) are built and installed.

## Automatic Fix

We've implemented several solutions to automatically handle this issue:

1. The `fix_numpy_installation.py` script in the project root directory
2. Updated installation scripts that detect Python 3.13+ and use special handling for numpy

### Using the Fix Script

You can run the fix script directly:

```bash
python fix_numpy_installation.py [--version VERSION]
```

Where `VERSION` is the specific numpy version you want to install (e.g., 1.24.4).

The script will:
1. Update setuptools and wheel
2. Try to install numpy using pre-compiled binaries
3. Try different numpy versions if needed
4. Verify the installation

## Manual Fix Options

If the automatic fix doesn't work, you can try these manual solutions:

### Option 1: Update setuptools and use binary wheels

```bash
# Update setuptools and wheel
pip install --upgrade setuptools wheel

# Install numpy using binary wheels only
pip install --only-binary=:all: numpy==1.24.4
```

### Option 2: Try a different numpy version

```bash
# Try newer or older versions
pip install --only-binary=:all: numpy==1.26.4
# or
pip install --only-binary=:all: numpy==1.25.2
# or
pip install --only-binary=:all: numpy==1.23.5
```

### Option 3: Install a C compiler

If you need to build from source:

- **Windows**: Install Visual C++ Build Tools
- **macOS**: Install Xcode Command Line Tools (`xcode-select --install`)
- **Linux**: Install gcc and python development packages (`sudo apt-get install gcc python3-dev`)

Then try installing numpy normally:

```bash
pip install numpy==1.24.4
```

## Compatibility Notes

- The Nuke AI Panel will work without numpy, but some advanced features may be limited
- If you're using Nuke's built-in Python, you won't encounter this issue as Nuke ships with compatible numpy versions
- Consider using Python 3.8-3.12 for the most stable experience with numpy and other scientific packages

## Troubleshooting

If you continue to have issues:

1. Check if numpy is available in your Python environment:
   ```python
   import numpy
   print(numpy.__version__)
   ```

2. Try installing from a specific wheel file:
   - Visit https://pypi.org/project/numpy/#files
   - Download a compatible wheel for your system
   - Install with: `pip install path/to/wheel.whl`

3. Consider using a Python distribution like Anaconda that includes pre-built scientific packages

## Further Assistance

If you continue to experience issues, please:

1. Check our GitHub issues to see if others have encountered the same problem
2. Open a new issue with details about your environment and the exact error messages
3. Contact our support team for direct assistance