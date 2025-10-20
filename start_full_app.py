#!/usr/bin/env python3
"""
Start the full dbt MCP Hackathon Project application with AI generation capabilities
"""
import subprocess
import sys
import time
import os
import signal
from pathlib import Path
from threading import Thread

class FullAppLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            'streamlit', 'fastapi', 'uvicorn', 'dbt', 'pandas', 'plotly'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"  ❌ {package}")
        
        if missing:
            print(f"\n⚠️  Missing packages: {', '.join(missing)}")
            print("Install with: pip install -r dbt_mcp_hackathon_project/requirements.txt")
            return False
        
        print("✅ All dependencies found!")
        return True
    
    def setup_environment(self):
        """Setup environment variables and configuration"""
        print("⚙️  Setting up environment...")
        
        # Set Python path
        project_root = Path.cwd()
        if str(project_root) not in sys.path:
            os.environ['PYTHONPATH'] = str(project_root)
        
        # Check for .env file
        env_file = project_root / '.env'
        if not env_file.exists():
            print("📝 Creating .env file...")
            env_content = """# dbt MCP Hackathon Project Configuration
DBT_PROJECT_PATH=.
DUCKDB_PATH=data/dbt_mcp_hackathon_project.duckdb
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
STREAMLIT_PORT=8501

# AI Configuration (optional - will use mock if not provided)
# OPENAI_API_KEY=your_key_here
# KIRO_AI_ENDPOINT=your_endpoint_here
"""
            env_file.write_text(env_content)
            print("✅ Created .env file")
        
        # Ensure data directory exists
        data_dir = project_root / 'data'
        data_dir.mkdir(exist_ok=True)
        
        print("✅ Environment setup complete")
    
    def compile_dbt_project(self):
        """Compile the dbt project"""
        print("📋 Compiling dbt project...")
        
        manifest_path = Path("target/manifest.json")
        if manifest_path.exists():
            print("✅ dbt manifest already exists")
            return True
        
        try:
            result = subprocess.run(["dbt", "compile"], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ dbt project compiled successfully")
                return True
            else:
                print(f"❌ dbt compile failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ dbt compile timed out")
            return False
        except FileNotFoundError:
            print("❌ dbt command not found. Please install dbt-core and dbt-duckdb")
            return False
    
    def start_backend(self):
        """Start the MCP backend server"""
        print("🚀 Starting MCP backend server...")
        
        try:
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "dbt_mcp_hackathon_project.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give server time to start
            time.sleep(5)
            
            # Check if server is running
            if self.backend_process.poll() is None:
                print("✅ MCP server started on http://localhost:8000")
                return True
            else:
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ MCP server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False
    
    def start_frontend(self):
        """Start the Streamlit frontend"""
        print("🎨 Starting Streamlit frontend...")
        
        try:
            # Start Streamlit in a way that doesn't block
            self.frontend_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run",
                "dbt_mcp_hackathon_project/frontend/app.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0",
                "--server.headless", "true"
            ])
            
            time.sleep(3)
            
            if self.frontend_process.poll() is None:
                print("✅ Streamlit frontend started on http://localhost:8501")
                return True
            else:
                print("❌ Streamlit frontend failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
    
    def wait_for_shutdown(self):
        """Wait for user to stop the application"""
        print("\n" + "="*60)
        print("🎉 dbt MCP Hackathon Project is running!")
        print("📍 Frontend: http://localhost:8501")
        print("📍 Backend API: http://localhost:8000")
        print("📍 API Docs: http://localhost:8000/docs")
        print("\n💡 Features available:")
        print("   - Model exploration with real dbt data")
        print("   - AI-powered model generation")
        print("   - Compile and run models")
        print("   - Interactive chat interface")
        print("\nPress Ctrl+C to stop...")
        print("="*60)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
    
    def cleanup(self):
        """Clean up processes"""
        if self.backend_process:
            print("🧹 Stopping backend server...")
            self.backend_process.terminate()
            self.backend_process.wait()
        
        if self.frontend_process:
            print("🧹 Stopping frontend...")
            self.frontend_process.terminate()
            self.frontend_process.wait()
        
        print("✅ Cleanup complete")
    
    def run(self):
        """Run the full application"""
        try:
            print("🤖 dbt MCP Hackathon Project Full Application Launcher")
            print("="*50)
            
            # Check dependencies
            if not self.check_dependencies():
                return False
            
            # Setup environment
            self.setup_environment()
            
            # Compile dbt project
            if not self.compile_dbt_project():
                print("⚠️  Continuing without dbt compilation...")
            
            # Start backend
            if not self.start_backend():
                print("❌ Cannot continue without backend server")
                return False
            
            # Start frontend
            if not self.start_frontend():
                print("❌ Cannot continue without frontend")
                self.cleanup()
                return False
            
            # Wait for shutdown
            self.wait_for_shutdown()
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            self.cleanup()
        
        return True

def main():
    launcher = FullAppLauncher()
    success = launcher.run()
    
    if success:
        print("👋 Thanks for using dbt MCP Hackathon Project!")
    else:
        print("❌ Failed to start dbt MCP Hackathon Project")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you're in the project root directory")
        print("2. Install dependencies: pip install -r dbt_mcp_hackathon_project/requirements.txt")
        print("3. Check that ports 8000 and 8501 are available")
        print("4. Try manual startup (see README_DEMO.md)")

if __name__ == "__main__":
    main()