#!/usr/bin/env python3
"""
MCP Server entry point for dbt MCP Hackathon Project

This script starts the real MCP server that can be used by AI agents
like Claude, ChatGPT, etc. through the Model Context Protocol.

Usage:
    python mcp_main.py

Or as an MCP server in your AI client configuration:
    {
        "command": "python",
        "args": ["path/to/dbt_mcp_hackathon_project/mcp_main.py"],
        "env": {
            "OPENAI_API_KEY": "your-api-key-here"
        }
    }
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
parent_root = project_root.parent
sys.path.insert(0, str(parent_root))

from dbt_mcp_hackathon_project.backend.real_mcp_server import RealMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)  # MCP uses stderr for logging
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting dbt MCP Hackathon Project MCP Server...")
        
        # Create and run the MCP server
        server = RealMCPServer()
        await server.run_server()
        
    except KeyboardInterrupt:
        logger.info("MCP Server stopped by user")
    except Exception as e:
        logger.error(f"MCP Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())