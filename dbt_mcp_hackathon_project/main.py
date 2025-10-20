"""
Main FastAPI application entry point for dbt MCP Hackathon Project
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer

# Create MCP server instance
mcp_server = MCPServer()

# Get the FastAPI app
app = mcp_server.get_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)