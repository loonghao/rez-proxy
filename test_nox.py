#!/usr/bin/env python3
"""
Test script to verify nox configuration works correctly.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🧪 Testing: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print("Output:", result.stdout[:500])
            return True
        else:
            print(f"❌ {description} - FAILED")
            print("STDOUT:", result.stdout[:500])
            print("STDERR:", result.stderr[:500])
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def main():
    """Test nox configuration."""
    print("🚀 Testing nox configuration for rez-proxy")
    print("=" * 50)
    
    # Find nox executable
    nox_cmd = None
    possible_paths = [
        "C:\\Users\\hallo\\.local\\bin\\nox.exe",
        "nox",
        "uvx nox"
    ]
    
    for path in possible_paths:
        try:
            if path == "uvx nox":
                cmd = ["uvx", "nox", "--version"]
            else:
                cmd = [path, "--version"]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                nox_cmd = path
                print(f"✅ Found nox: {path}")
                break
        except:
            continue
    
    if not nox_cmd:
        print("❌ Could not find nox executable")
        return False
    
    # Test commands
    tests = [
        (["list sessions"], f"{nox_cmd} -l"),
        (["lint check"], f"{nox_cmd} -s lint"),
        (["format check"], f"{nox_cmd} -s format"),
        (["unit tests"], f"{nox_cmd} -s test_unit"),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for description, cmd_str in tests:
        if nox_cmd == "uvx nox":
            cmd = ["uvx", "nox"] + cmd_str.split()[2:]
        else:
            cmd = cmd_str.split()
        
        if run_command(cmd, description[0]):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All nox tests passed!")
        return True
    else:
        print("⚠️ Some nox tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
