#!/usr/bin/env python3
"""
Script to fix relative imports to absolute imports in rez-proxy.
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix relative imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match relative imports
        patterns = [
            # from ..module import something
            (r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', r'from rez_proxy.\1'),
            # from .module import something  
            (r'from \.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)', r'from rez_proxy.\1'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix all imports."""
    src_dir = Path("src/rez_proxy")
    
    if not src_dir.exists():
        print(f"Source directory {src_dir} not found!")
        return
    
    # Find all Python files
    python_files = list(src_dir.rglob("*.py"))
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files out of {len(python_files)} Python files.")


if __name__ == "__main__":
    main()
