#!/usr/bin/env python3
"""
Quick development environment setup script.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a command with error handling."""
    print(f"🔧 {description}...")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:200]}")
        else:
            print(f"   ❌ Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[:200]}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        return False
    except FileNotFoundError:
        print(f"   ❌ Command not found: {cmd[0]}")
        return False

def check_tool(tool_name, cmd):
    """Check if a tool is available."""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0
    except:
        return False

def main():
    """Set up development environment."""
    print("🚀 Rez-Proxy Development Environment Setup")
    print("=" * 50)
    
    # Check system
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print()
    
    # Check prerequisites
    print("📋 Checking prerequisites...")
    
    tools_status = {}
    
    # Check uv
    tools_status['uv'] = check_tool('uv', ['uv', '--version'])
    if tools_status['uv']:
        print("   ✅ uv is available")
    else:
        print("   ❌ uv is not available")
        print("   📖 Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    
    # Check git
    tools_status['git'] = check_tool('git', ['git', '--version'])
    if tools_status['git']:
        print("   ✅ git is available")
    else:
        print("   ❌ git is not available")
    
    print()
    
    if not tools_status['uv']:
        print("❌ uv is required. Please install it first.")
        return False
    
    # Install nox
    print("🔧 Setting up tools...")
    success = True
    
    if not check_tool('nox', ['uvx', 'nox', '--version']):
        success &= run_command(['uv', 'tool', 'install', 'nox'], 
                              "Installing nox", check=False)
    else:
        print("   ✅ nox is already available")
    
    # Set up development environment
    if success:
        print("\n🏗️  Setting up development environment...")
        success &= run_command(['uvx', 'nox', '-s', 'dev'], 
                              "Setting up development environment", check=False)
    
    # Run a quick test
    if success:
        print("\n🧪 Running quick validation...")
        success &= run_command(['uvx', 'nox', '-s', 'lint'], 
                              "Running code linting", check=False)
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 Development environment setup completed successfully!")
        print("\n📖 Next steps:")
        print("   1. Run tests:        make test")
        print("   2. Start server:     make serve")
        print("   3. Check quality:    make quality")
        print("   4. See all commands: make help")
        print("\n💡 Quick commands:")
        print("   uvx nox -s test      # Run all tests")
        print("   uvx nox -s serve     # Start dev server")
        print("   uvx nox -l           # List all commands")
        
        # Install pre-commit hooks if git is available
        if tools_status['git']:
            print("\n🪝 Installing pre-commit hooks...")
            if run_command(['pip', 'install', 'pre-commit'], 
                          "Installing pre-commit", check=False):
                run_command(['pre-commit', 'install'], 
                           "Installing git hooks", check=False)
                run_command(['pre-commit', 'install', '--hook-type', 'commit-msg'], 
                           "Installing commit-msg hooks", check=False)
    else:
        print("❌ Setup failed. Please check the errors above.")
        print("\n🔍 Troubleshooting:")
        print("   1. Make sure uv is installed and in PATH")
        print("   2. Check internet connection")
        print("   3. Try running commands manually")
        print("   4. See DEVELOPMENT_EN.md for detailed instructions")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
