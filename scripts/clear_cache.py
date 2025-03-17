#!/usr/bin/env python
import os
import shutil
import sys

def clear_python_cache(root_dir='.'):
    """
    Clears all Python cache files and directories from the specified root directory.
    This includes:
    - __pycache__ directories
    - .pyc files
    - .pyo files
    - .pyd files
    """
    total_removed = 0
    
    print(f"Scanning for Python cache files in: {os.path.abspath(root_dir)}")
    
    # Walk through all directories from the root
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip the venv directory if it exists
        if 'venv' in dirpath.split(os.sep):
            continue
            
        # Remove __pycache__ directories
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            print(f"Removing: {pycache_path}")
            try:
                shutil.rmtree(pycache_path)
                total_removed += 1
            except Exception as e:
                print(f"Error removing {pycache_path}: {e}")
        
        # Remove .pyc, .pyo, and .pyd files
        for filename in filenames:
            if filename.endswith(('.pyc', '.pyo', '.pyd')):
                file_path = os.path.join(dirpath, filename)
                print(f"Removing: {file_path}")
                try:
                    os.remove(file_path)
                    total_removed += 1
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
    
    print(f"\nCompleted! Removed {total_removed} cache files/directories.")

if __name__ == "__main__":
    # Use command line argument for the root directory if provided, otherwise use current directory
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    clear_python_cache(root_dir) 