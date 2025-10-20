#!/usr/bin/env python3
"""
Simple script to start both FastAPI backend and Streamlit frontend for testing
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    
    # Change to the project directory
    os.chdir("dbt_mcp_hackathon_project")
    
    # Start the backend server
    backend_process = subprocess.Popen([
        sys.executable, "-c", 
        """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer
import uvicorn

mcp_server = MCPServer()
app = mcp_server.get_app()
uvicorn.run(app, host="0.0.0.0", port=8000)
        """
    ])
    
    return backend_process

def start_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    
    # Create a simple streamlit app for testing
    simple_app = """
import streamlit as st
import requests
import json

st.set_page_config(page_title="dbt MCP Test", page_icon="🤖")

st.title("🤖 dbt MCP Hackathon Project - Test Interface")

# Test backend connection
st.header("Backend Connection Test")

try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        st.success("✅ Backend is connected!")
        health_data = response.json()
        st.json(health_data)
    else:
        st.error(f"❌ Backend connection failed: {response.status_code}")
except Exception as e:
    st.error(f"❌ Backend connection error: {e}")

# Test model listing
st.header("Models Test")
if st.button("List Models"):
    try:
        response = requests.get("http://localhost:8000/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            st.success(f"✅ Found {models.get('total_count', 0)} models")
            
            # Show first few models
            if models.get('models'):
                st.subheader("Sample Models:")
                for model in models['models'][:5]:
                    with st.expander(f"📊 {model['name']}"):
                        st.write(f"**Description:** {model.get('description', 'No description')}")
                        st.write(f"**Materialization:** {model.get('materialization', 'Unknown')}")
                        st.write(f"**Columns:** {len(model.get('columns', []))}")
        else:
            st.error(f"❌ Failed to fetch models: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error fetching models: {e}")

# Test AI status
st.header("AI Services Test")
if st.button("Check AI Status"):
    try:
        response = requests.get("http://localhost:8000/ai-status", timeout=5)
        if response.status_code == 200:
            ai_status = response.json()
            st.success("✅ AI services status retrieved")
            st.json(ai_status)
        else:
            st.error(f"❌ Failed to get AI status: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error getting AI status: {e}")

# Simple model generation test
st.header("Model Generation Test")
prompt = st.text_area("Enter a model description:", 
                     value="Create a simple customer summary model")

if st.button("Generate Model (SQL Only)"):
    if prompt:
        try:
            payload = {
                "prompt": prompt,
                "materialization": "view"
            }
            response = requests.post("http://localhost:8000/generate", 
                                   json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Model generated successfully!")
                st.subheader("Generated SQL:")
                st.code(result.get('sql', 'No SQL generated'), language='sql')
                st.subheader("Details:")
                st.json({
                    "model_name": result.get('model_name'),
                    "description": result.get('description'),
                    "confidence": result.get('confidence'),
                    "reasoning": result.get('reasoning')
                })
            else:
                st.error(f"❌ Generation failed: {response.status_code}")
                st.text(response.text)
        except Exception as e:
            st.error(f"❌ Error generating model: {e}")
    else:
        st.warning("Please enter a model description")

st.markdown("---")
st.markdown("**Testing the dbt MCP Hackathon Project integration**")
    """
    
    # Write the simple app to a temporary file
    with open("dbt_mcp_hackathon_project/simple_test_app.py", "w") as f:
        f.write(simple_app)
    
    # Start streamlit with the simple app
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "dbt_mcp_hackathon_project/simple_test_app.py",
        "--server.port", "8501"
    ])
    
    return frontend_process

def main():
    """Main function to start both services"""
    print("🧪 Starting dbt MCP Hackathon Project Test Environment")
    print("=" * 60)
    
    try:
        # Start backend
        backend_process = start_backend()
        print("⏳ Waiting for backend to start...")
        time.sleep(5)
        
        # Start frontend
        frontend_process = start_frontend()
        print("⏳ Waiting for frontend to start...")
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("🎉 Test environment ready!")
        print("📊 Backend API: http://localhost:8000")
        print("🎨 Frontend UI: http://localhost:8501")
        print("=" * 60)
        print("\nPress Ctrl+C to stop both services")
        
        # Wait for user to stop
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            backend_process.terminate()
            frontend_process.terminate()
            print("✅ Services stopped")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())