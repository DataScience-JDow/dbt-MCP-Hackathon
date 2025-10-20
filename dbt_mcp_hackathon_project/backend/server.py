"""
Startup script for dbt MCP Hackathon Project MCP Server
"""
import uvicorn
import typer
from pathlib import Path

from .mcp_server import MCPServer
from ..config import Config

app = typer.Typer()

@app.command()
def start(
    host: str = typer.Option(Config.MCP_HOST, help="Host to bind the server to"),
    port: int = typer.Option(Config.MCP_PORT, help="Port to bind the server to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    log_level: str = typer.Option("info", help="Log level")
):
    """Start the dbt MCP Hackathon Project MCP Server"""
    
    try:
        # Initialize the MCP server
        mcp_server = MCPServer()
        
        typer.echo(f"Starting dbt MCP Hackathon Project MCP Server on {host}:{port}")
        typer.echo(f"dbt project path: {Config.DBT_PROJECT_PATH}")
        typer.echo(f"DuckDB database: {Config.DUCKDB_PATH}")
        
        # Start the server
        uvicorn.run(
            mcp_server.get_app(),
            host=host,
            port=port,
            reload=reload,
            log_level=log_level
        )
        
    except Exception as e:
        typer.echo(f"Failed to start MCP Server: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def health():
    """Check server health"""
    import requests
    
    try:
        response = requests.get(f"http://{Config.MCP_HOST}:{Config.MCP_PORT}/health")
        if response.status_code == 200:
            health_data = response.json()
            typer.echo("✅ Server is healthy")
            typer.echo(f"dbt project: {health_data['dbt_project_path']}")
            typer.echo(f"Database connected: {health_data['database_connected']}")
            typer.echo(f"Models count: {health_data['models_count']}")
        else:
            typer.echo(f"❌ Server unhealthy: {response.status_code}")
            raise typer.Exit(1)
    except requests.exceptions.ConnectionError:
        typer.echo("❌ Cannot connect to server")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Health check failed: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()