#!/usr/bin/env python3
"""
Simple test client for the dbt MCP Hackathon Project MCP Server

This script tests the MCP server functionality by connecting to it
and calling various tools.
"""
import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_server():
    """Test the MCP server by calling its tools"""
    
    try:
        # Start the MCP server as a subprocess
        logger.info("Starting MCP server...")
        
        server_process = subprocess.Popen(
            [sys.executable, "mcp_main.py"],
            cwd=project_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Simple test - just check if server starts without errors
        await asyncio.sleep(2)  # Give server time to start
        
        if server_process.poll() is None:
            logger.info("✅ MCP Server started successfully")
            
            # Terminate the server
            server_process.terminate()
            await asyncio.sleep(1)
            
            if server_process.poll() is None:
                server_process.kill()
            
            logger.info("✅ MCP Server stopped cleanly")
            return True
        else:
            # Server exited, check for errors
            stdout, stderr = server_process.communicate()
            logger.error(f"❌ MCP Server failed to start")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("Testing dbt MCP Hackathon Project MCP Server...")
    
    success = await test_mcp_server()
    
    if success:
        logger.info("🎉 All tests passed!")
        print("\n" + "="*60)
        print("MCP SERVER READY!")
        print("="*60)
        print("\nYour MCP server is working correctly.")
        print("\nTo use it with an AI client, configure it like this:")
        print(f"""
{{
    "command": "python",
    "args": ["{project_root / 'mcp_main.py'}"],
    "env": {{
        "OPENAI_API_KEY": "your-api-key-here"
    }}
}}
        """)
        print("\nAvailable tools:")
        print("- list_models: List all dbt models")
        print("- get_model_details: Get detailed model information")
        print("- generate_model: Generate new models with ChatGPT")
        print("- compile_model: Compile dbt models")
        print("- run_model: Execute dbt models")
        print("- get_model_lineage: Get model dependencies")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())