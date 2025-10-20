#!/usr/bin/env python3
"""
Health check for dbt MCP Hackathon Project services
"""
import requests
import time
import sys

def check_backend():
    """Check if MCP backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend server is healthy")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Models: {data.get('models_count')}")
            print(f"   - Database: {'Connected' if data.get('database_connected') else 'Disconnected'}")
            return True
        else:
            print(f"❌ Backend server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not reachable (not running?)")
        return False
    except Exception as e:
        print(f"❌ Backend check failed: {e}")
        return False

def check_frontend():
    """Check if Streamlit frontend is running"""
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not reachable (not running?)")
        return False
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def test_model_generation():
    """Test model generation API"""
    try:
        test_request = {
            "prompt": "Create a simple test model",
            "output_name": "test_model",
            "materialization": "view"
        }
        
        response = requests.post(
            "http://localhost:8000/generate",
            json=test_request,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Model generation API working")
            print(f"   - Generated SQL: {len(data.get('sql', ''))} characters")
            print(f"   - Model name: {data.get('model_name')}")
            return True
        else:
            print(f"❌ Model generation failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Model generation test failed: {e}")
        return False

def main():
    print("🔍 dbt MCP Hackathon Project Health Check")
    print("="*40)
    
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    if backend_ok:
        generation_ok = test_model_generation()
    else:
        generation_ok = False
    
    print("\n" + "="*40)
    print("📊 Summary:")
    print(f"Backend Server: {'✅' if backend_ok else '❌'}")
    print(f"Frontend App: {'✅' if frontend_ok else '❌'}")
    print(f"AI Generation: {'✅' if generation_ok else '❌'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 All systems operational!")
        print("🌐 Open http://localhost:8501 to use dbt MCP Hackathon Project")
        
        if generation_ok:
            print("🤖 AI model generation is working!")
        else:
            print("⚠️  AI generation may have issues (check logs)")
            
    else:
        print("\n❌ Some services are not running")
        print("💡 Try running: python start_full_app.py")
    
    return backend_ok and frontend_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)