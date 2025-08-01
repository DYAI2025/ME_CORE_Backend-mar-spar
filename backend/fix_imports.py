#!/usr/bin/env python3
"""
Script to fix all 'from app.' imports to relative imports in the backend.
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace 'from app.' with 'from ..' (relative import)
    # This assumes files are in subdirectories of backend
    original = content
    content = re.sub(r'from app\.', 'from ..', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed imports in {filepath}")
        return True
    return False

def main():
    backend_dir = Path(__file__).parent
    
    # Find all Python files and fix imports
    for py_file in backend_dir.rglob("*.py"):
        if py_file.name == __file__.split('/')[-1]:  # Skip this script
            continue
        try:
            fix_imports_in_file(py_file)
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

if __name__ == "__main__":
    main()