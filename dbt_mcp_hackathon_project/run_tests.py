#!/usr/bin/env python3
"""
Comprehensive test suite for dbt MCP Hackathon Project
"""
import asyncio
import subprocess
import sys
import time
import requests
from pathlib import Path

def test_imports():
    """Test that critical imports work correctly"""
    print("🔍 Testing critical imports...")
    try:
        # Test MCP library - this is the most important
        import mcp
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, Resource, TextContent
        print("✅ MCP library and core components imported successfully")
        
        # Test OpenAI import (needed for ChatGPT integration)
        from openai import AsyncOpenAI
        print("✅ OpenAI library imported successfully")
        
        # Test that key files exist
        key_files = [
            "backend/real_mcp_server.py",
            "mcp_main.py",
            "config.py"
        ]
        
        for file_path in key_files:
            if Path(file_path).exists():
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        print(f"   Error details: {type(e).__name__}: {str(e)}")
        return False

def test_mcp_server_startup():
    """Test MCP server can start and stop"""
    print("\n🚀 Testing MCP server startup...")
    try:
        process = subprocess.Popen(
            [sys.executable, "mcp_main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ MCP server started successfully")
            process.terminate()
            process.wait(timeout=5)
            print("✅ MCP server stopped cleanly")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ MCP server failed to start")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def test_legacy_server():
    """Test legacy FastAPI server"""
    print("\n🔧 Testing legacy FastAPI server...")
    try:
        # Start server
        process = subprocess.Popen(
            [sys.executable, "-c", "from main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8001)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it time to start
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ Legacy server health check passed")
                result = True
            else:
                print(f"❌ Legacy server health check failed: {response.status_code}")
                result = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Legacy server connection failed: {e}")
            result = False
        
        # Stop server
        process.terminate()
        process.wait(timeout=5)
        
        return result
        
    except Exception as e:
        print(f"❌ Legacy server test failed: {e}")
        return False

def test_configuration():
    """Test configuration files"""
    print("\n⚙️  Testing configuration...")
    
    # Check MCP config
    mcp_config = Path("../.kiro/settings/mcp.json")
    if mcp_config.exists():
        print("✅ Kiro MCP configuration found")
    else:
        print("⚠️  Kiro MCP configuration not found (this is OK if not using Kiro)")
    
    # Check requirements
    requirements = Path("requirements.txt")
    if requirements.exists():
        with open(requirements) as f:
            content = f.read()
            if "mcp>=" in content:
                print("✅ MCP dependency found in requirements.txt")
            else:
                print("❌ MCP dependency missing from requirements.txt")
                return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Running dbt MCP Hackathon Project Tests")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("MCP Server Tests", test_mcp_server_startup),
        ("Configuration Tests", test_configuration),
        # ("Legacy Server Tests", test_legacy_server),  # Skip for now as it might conflict
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Ready to push to main.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before pushing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())