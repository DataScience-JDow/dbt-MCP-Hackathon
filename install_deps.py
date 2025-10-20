#!/usr/bin/env python3
"""
Install dependencies for dbt MCP Hackathon Project
"""
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python dependencies...")
    
    requirements_file = Path("dbt_mcp_hackathon_project/requirements.txt")
    
    if not requirements_file.exists():
        print("❌ Requirements file not found")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        
        print("✅ Python dependencies installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_dbt_installation():
    """Check if dbt is properly installed"""
    print("🔍 Checking dbt installation...")
    
    try:
        result = subprocess.run(["dbt", "--version"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ dbt is installed")
            print(f"   Version info: {result.stdout.strip()}")
            return True
        else:
            print("❌ dbt not working properly")
            return False
            
    except FileNotFoundError:
        print("❌ dbt command not found")
        print("💡 Install with: pip install dbt-core dbt-duckdb")
        return False

def setup_dbt_profiles():
    """Setup dbt profiles if needed"""
    print("⚙️  Checking dbt profiles...")
    
    profiles_dir = Path.home() / ".dbt"
    profiles_file = profiles_dir / "profiles.yml"
    
    if profiles_file.exists():
        print("✅ dbt profiles.yml exists")
        return True
    
    print("📝 Creating dbt profiles.yml...")
    
    profiles_dir.mkdir(exist_ok=True)
    
    profiles_content = """default:
  outputs:
    dev:
      type: duckdb
      path: 'data/dbt_mcp_hackathon_project.duckdb'
      threads: 4
  target: dev
"""
    
    profiles_file.write_text(profiles_content)
    print("✅ Created dbt profiles.yml")
    return True

def main():
    print("🚀 dbt MCP Hackathon Project Installation Setup")
    print("="*40)
    
    # Install Python requirements
    if not install_requirements():
        print("❌ Failed to install Python dependencies")
        return False
    
    # Check dbt
    if not check_dbt_installation():
        print("❌ dbt installation issues")
        return False
    
    # Setup dbt profiles
    if not setup_dbt_profiles():
        print("❌ Failed to setup dbt profiles")
        return False
    
    print("\n✅ Installation complete!")
    print("\n🎯 Next steps:")
    print("1. Run: python start_full_app.py")
    print("2. Open: http://localhost:8501")
    print("3. Try the AI model generation!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Installation failed")
        print("💡 Try manual installation:")
        print("   pip install -r dbt_mcp_hackathon_project/requirements.txt")
        print("   pip install dbt-core dbt-duckdb")
        sys.exit(1)