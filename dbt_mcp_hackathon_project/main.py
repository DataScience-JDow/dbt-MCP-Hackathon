"""
Main FastAPI application entry point for dbt MCP Hackathon Project
"""
from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer

# Create MCP server instance
mcp_server = MCPServer()

# Get the FastAPI app
app = mcp_server.get_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)