#!/usr/bin/env python3
"""
Demo script showing the correct way to run tests with nox.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show the result."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def main():
    """Demonstrate correct testing workflow."""
    print("🚀 Rez-Proxy Testing Demo")
    print("This script demonstrates the correct way to run tests using nox.")
    print()
    
    # Check if nox is available
    nox_available = False
    try:
        result = subprocess.run(["uvx", "nox", "--version"], 
                              capture_output=True, timeout=10)
        if result.returncode == 0:
            nox_available = True
            print("✅ Nox is available via uvx")
        else:
            print("❌ Nox not available via uvx")
    except:
        print("❌ Could not check nox availability")
    
    if not nox_available:
        print("\n🔧 To install nox:")
        print("   uv tool install nox")
        print("\n📖 Then run this script again")
        return False
    
    print("\n📋 Available test commands:")
    print("1. uvx nox -s test          # Full tests with coverage")
    print("2. uvx nox -s test_fast     # Fast tests without coverage")
    print("3. uvx nox -s test_unit     # Unit tests only")
    print("4. uvx nox -s lint          # Code linting")
    print("5. uvx nox -s quality       # All quality checks")
    print("6. uvx nox -s ci_fast       # Fast CI checks")
    
    print("\n🎯 Running demonstration...")
    
    # Demo commands
    demos = [
        (["uvx", "nox", "-l"], "List all available nox sessions"),
        (["uvx", "nox", "-s", "lint"], "Run code linting"),
        (["uvx", "nox", "-s", "test_unit"], "Run unit tests"),
    ]
    
    success_count = 0
    for cmd, description in demos:
        if run_command(cmd, description):
            success_count += 1
    
    print(f"\n📊 Demo Results: {success_count}/{len(demos)} commands succeeded")
    
    if success_count == len(demos):
        print("\n🎉 All demo commands completed successfully!")
        print("\n💡 You can now use these commands for development:")
        print("   make test           # Run all tests")
        print("   make test-fast      # Run fast tests")
        print("   make lint           # Check code style")
        print("   make serve          # Start dev server")
    else:
        print("\n⚠️ Some demo commands failed. Check the output above.")
    
    print("\n📖 For more information, see:")
    print("   - DEVELOPMENT_EN.md (English)")
    print("   - DEVELOPMENT.md (中文)")
    print("   - make help")
    print("   - uvx nox -l")
    
    return success_count == len(demos)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
