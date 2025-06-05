#!/usr/bin/env python3
"""
Clear Python cache files that might be causing import issues
"""

import os
import shutil
import sys

def clear_python_cache(directory="."):
    """Clear Python cache files recursively"""
    cache_dirs = []
    pyc_files = []
    
    for root, dirs, files in os.walk(directory):
        # Find __pycache__ directories
        if "__pycache__" in dirs:
            cache_dirs.append(os.path.join(root, "__pycache__"))
        
        # Find .pyc files
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                pyc_files.append(os.path.join(root, file))
    
    # Remove cache directories
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"Removed cache directory: {cache_dir}")
        except Exception as e:
            print(f"Failed to remove {cache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"Removed cache file: {pyc_file}")
        except Exception as e:
            print(f"Failed to remove {pyc_file}: {e}")
    
    print(f"\nCleared {len(cache_dirs)} cache directories and {len(pyc_files)} cache files")

if __name__ == "__main__":
    print("Clearing Python cache files...")
    clear_python_cache()
    print("Cache clearing complete!")