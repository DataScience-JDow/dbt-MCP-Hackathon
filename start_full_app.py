#!/usr/bin/env python3
"""
Start the full dbt MCP Hackathon Project application
Fixed version that uses working components
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    
    # Change to the correct directory
    backend_dir = Path("dbt_mcp_hackathon_project")
    
    backend_cmd = [
        sys.executable, "-c", 
        """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer
import uvicorn

mcp_server = MCPServer()
app = mcp_server.get_app()
uvicorn.run(app, host="127.0.0.1", port=8001)
        """
    ]
    
    backend_process = subprocess.Popen(backend_cmd, cwd=str(backend_dir))
    return backend_process

def start_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    
    # Use the working single-file frontend
    frontend_dir = Path("dbt_mcp_hackathon_project")
    
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "full_app.py",
        "--server.port", "8502",
        "--server.headless", "true"
    ]
    
    frontend_process = subprocess.Popen(frontend_cmd, cwd=str(frontend_dir))
    return frontend_process

def main():
    """Main function"""
    print("🚀 Starting dbt MCP Hackathon Project Full Application")
    print("=" * 60)
    
    try:
        # Start backend
        backend_process = start_backend()
        print("⏳ Waiting for backend to initialize...")
        time.sleep(8)  # Give backend more time to start
        
        # Start frontend
        frontend_process = start_frontend()
        print("⏳ Waiting for frontend to initialize...")
        time.sleep(5)
        
        print("\n" + "=" * 60)
        print("🎉 Full Application Ready!")
        print("📊 Backend API: http://localhost:8001")
        print("🎨 Frontend UI: http://localhost:8502")
        print("📚 API Docs: http://localhost:8001/docs")
        print("=" * 60)
        print("\nPress Ctrl+C to stop both services")
        
        # Wait for processes
        try:
            while True:
                if backend_process.poll() is not None:
                    print("❌ Backend process stopped unexpectedly")
                    break
                if frontend_process.poll() is not None:
                    print("❌ Frontend process stopped unexpectedly")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            backend_process.terminate()
            frontend_process.terminate()
            
            # Wait for graceful shutdown
            time.sleep(2)
            
            # Force kill if needed
            if backend_process.poll() is None:
                backend_process.kill()
            if frontend_process.poll() is None:
                frontend_process.kill()
                
            print("✅ Services stopped")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())