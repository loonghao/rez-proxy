#!/usr/bin/env python3
"""
Script to add FastAPI versioning decorators to router files.
"""

import os
import re
from pathlib import Path


def add_versioning_to_file(file_path: Path):
    """Add versioning imports and decorators to a router file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has versioning
    if 'fastapi_versioning' in content:
        print(f"Skipping {file_path} - already has versioning")
        return
    
    # Add import
    if 'from fastapi import' in content:
        content = content.replace(
            'from fastapi import',
            'from fastapi import'
        )
        # Add versioning import after fastapi imports
        fastapi_import_pattern = r'(from fastapi import[^\n]+\n)'
        if re.search(fastapi_import_pattern, content):
            content = re.sub(
                fastapi_import_pattern,
                r'\1from fastapi_versioning import version\n',
                content,
                count=1
            )
    
    # Add @version(1) decorator to all router endpoints
    router_pattern = r'(@router\.(get|post|put|delete|patch)\([^)]*\)\n)(async def)'
    content = re.sub(
        router_pattern,
        r'\1@version(1)\n\3',
        content
    )
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {file_path}")


def main():
    """Main function to process all router files."""
    
    routers_dir = Path(__file__).parent.parent / 'src' / 'rez_proxy' / 'routers'
    
    # Files to process (excluding already processed ones)
    files_to_process = [
        'environments.py',
        'package_ops.py', 
        'repositories.py',
        'resolver.py',
        'rez_config.py',
        'versions.py',
    ]
    
    for filename in files_to_process:
        file_path = routers_dir / filename
        if file_path.exists():
            add_versioning_to_file(file_path)
        else:
            print(f"File not found: {file_path}")


if __name__ == '__main__':
    main()
