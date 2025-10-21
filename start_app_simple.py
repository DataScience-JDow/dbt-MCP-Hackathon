#!/usr/bin/env python3
"""
Simple startup script for dbt MCP Hackathon Project
Uses the tested and working components
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    """Start the application with working components"""
    print("🚀 Starting dbt MCP Hackathon Project")
    print("=" * 50)
    
    print("📋 Instructions:")
    print("1. First, start the backend in one terminal:")
    print("   cd dbt_mcp_hackathon_project")
    print('   python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd().parent)); from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer; import uvicorn; mcp_server = MCPServer(); app = mcp_server.get_app(); uvicorn.run(app, host=\'0.0.0.0\', port=8000)"')
    print()
    print("2. Then, start the frontend in another terminal:")
    print("   cd dbt_mcp_hackathon_project")
    print("   streamlit run full_app.py --server.port 8502")
    print()
    print("3. Or test the MCP server:")
    print("   cd dbt_mcp_hackathon_project")
    print("   python mcp_main.py")
    print()
    print("=" * 50)
    
    # Ask user which option they want
    print("Choose an option:")
    print("1. Start backend only")
    print("2. Start frontend only (requires backend running)")
    print("3. Test MCP server")
    print("4. Run tests")
    print("5. Show manual instructions")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        print("🚀 Starting backend...")
        os.chdir("dbt_mcp_hackathon_project")
        cmd = [
            sys.executable, "-c",
            "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd().parent)); from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer; import uvicorn; mcp_server = MCPServer(); app = mcp_server.get_app(); uvicorn.run(app, host='0.0.0.0', port=8000)"
        ]
        subprocess.run(cmd)
        
    elif choice == "2":
        print("🎨 Starting frontend...")
        os.chdir("dbt_mcp_hackathon_project")
        cmd = [sys.executable, "-m", "streamlit", "run", "full_app.py", "--server.port", "8502"]
        subprocess.run(cmd)
        
    elif choice == "3":
        print("🔧 Testing MCP server...")
        os.chdir("dbt_mcp_hackathon_project")
        cmd = [sys.executable, "mcp_main.py"]
        subprocess.run(cmd)
        
    elif choice == "4":
        print("🧪 Running tests...")
        os.chdir("dbt_mcp_hackathon_project")
        cmd = [sys.executable, "run_tests.py"]
        subprocess.run(cmd)
        
    elif choice == "5":
        print("\n📋 Manual Instructions:")
        print("Backend: http://localhost:8000")
        print("Frontend: http://localhost:8502")
        print("API Docs: http://localhost:8000/docs")
        
    else:
        print("❌ Invalid choice")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())