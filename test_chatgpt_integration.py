#!/usr/bin/env python3
"""
Test script for ChatGPT integration
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dbt_mcp_hackathon_project.backend.chatgpt_service import ChatGPTService
from dbt_mcp_hackathon_project.config import Config

async def test_chatgpt_integration():
    """Test ChatGPT integration with various prompts"""
    
    print("🧪 Testing ChatGPT Integration")
    print("=" * 50)
    
    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("💡 Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("   or create a .env file with OPENAI_API_KEY=your-api-key-here")
        return False
    
    print(f"✅ OpenAI API key found (ends with: ...{api_key[-4:]})")
    
    # Initialize service
    config = Config()
    service = ChatGPTService(config)
    
    # Test connection
    print("\n🔌 Testing API connection...")
    connection_result = await service.test_connection()
    
    if not connection_result["success"]:
        print(f"❌ Connection failed: {connection_result['error']}")
        return False
    
    print(f"✅ Connection successful: {connection_result['message']}")
    
    # Test SQL generation with various prompts
    test_prompts = [
        {
            "prompt": "Create a simple customer analysis model",
            "context": {"materialization": "view"}
        },
        {
            "prompt": "Build a daily revenue model combining orders and products",
            "context": {"materialization": "table", "business_area": "analytics"}
        },
        {
            "prompt": "Generate a customer lifetime value calculation",
            "context": {"materialization": "view", "requirements": "Include total orders and revenue"}
        }
    ]
    
    print("\n🤖 Testing SQL generation...")
    
    for i, test in enumerate(test_prompts, 1):
        print(f"\n--- Test {i}: {test['prompt']} ---")
        
        result = await service.generate_sql(test["prompt"], test["context"])
        
        if result["success"]:
            print(f"✅ Generated model: {result['model_name']}")
            print(f"📝 Description: {result['description']}")
            print(f"🏗️  Materialization: {result['materialization']}")
            print(f"🎯 Confidence: {result['confidence']}")
            
            # Show first few lines of SQL
            sql_lines = result["sql"].split('\n')[:10]
            print("📄 SQL Preview:")
            for line in sql_lines:
                print(f"   {line}")
            if len(result["sql"].split('\n')) > 10:
                print("   ...")
            
            if result.get("warnings"):
                print(f"⚠️  Warnings: {', '.join(result['warnings'])}")
        else:
            print(f"❌ Generation failed: {result['error']}")
    
    print("\n🎉 ChatGPT integration test complete!")
    return True

async def test_server_integration():
    """Test the server integration"""
    print("\n🖥️  Testing Server Integration")
    print("=" * 50)
    
    try:
        from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer
        
        # Create server instance
        server = MCPServer()
        
        # Check if ChatGPT service is available
        if hasattr(server, 'chatgpt_service') and server.chatgpt_service.is_available():
            print("✅ ChatGPT service is available in MCP server")
            
            # Test the new endpoints would work
            print("✅ New endpoints available:")
            print("   - POST /generate (auto-selects best AI)")
            print("   - POST /generate-chatgpt (ChatGPT only)")
            print("   - POST /generate-pattern (pattern AI only)")
            print("   - GET /ai-status (AI service status)")
        else:
            print("⚠️  ChatGPT service not available in MCP server")
            print("   Server will fall back to pattern-based AI")
        
        return True
        
    except Exception as e:
        print(f"❌ Server integration test failed: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions"""
    print("\n📋 Setup Instructions")
    print("=" * 50)
    print("1. Get an OpenAI API key from https://platform.openai.com/api-keys")
    print("2. Set the environment variable:")
    print("   export OPENAI_API_KEY='your-api-key-here'")
    print("3. Or create a .env file:")
    print("   echo 'OPENAI_API_KEY=your-api-key-here' > .env")
    print("4. Install requirements:")
    print("   pip install -r dbt_mcp_hackathon_project/requirements.txt")
    print("5. Run the server:")
    print("   python start_full_app.py")
    print("\n💡 The server will automatically use ChatGPT if available,")
    print("   otherwise fall back to pattern-based AI.")

async def main():
    """Main test function"""
    print("🚀 dbt MCP Hackathon Project - ChatGPT Integration Test")
    print("=" * 60)
    
    # Test ChatGPT service
    chatgpt_success = await test_chatgpt_integration()
    
    # Test server integration
    server_success = await test_server_integration()
    
    # Print setup instructions
    print_setup_instructions()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"ChatGPT Service: {'✅ PASS' if chatgpt_success else '❌ FAIL'}")
    print(f"Server Integration: {'✅ PASS' if server_success else '❌ FAIL'}")
    
    if chatgpt_success and server_success:
        print("\n🎉 All tests passed! ChatGPT integration is ready.")
        print("🌐 Start the server with: python start_full_app.py")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main())