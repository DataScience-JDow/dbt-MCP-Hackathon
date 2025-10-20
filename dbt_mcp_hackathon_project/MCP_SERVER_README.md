# dbt MCP Hackathon Project - MCP Server

This project now includes a **real MCP (Model Context Protocol) server** that can be used by AI agents like Claude, ChatGPT, and other MCP-compatible clients.

## What Changed

### ✅ Phase 1 Complete: Real MCP Server Implementation

We've successfully migrated from a custom FastAPI server to a proper MCP server implementation:

- **Real MCP Protocol**: Uses the official `mcp` library (v1.18.0)
- **ChatGPT Integration**: Enhanced AI model generation with proper dbt context
- **Tool-based Interface**: All functionality exposed as MCP tools instead of REST endpoints
- **Resource Access**: dbt manifest available as MCP resource

## Available MCP Tools

### 1. `list_models`
List all dbt models with optional filtering
```json
{
  "search": "customer",
  "materialization": "table",
  "limit": 10
}
```

### 2. `get_model_details`
Get detailed information about a specific model
```json
{
  "model_name": "dim_customers"
}
```

### 3. `generate_model`
Generate new dbt models using ChatGPT
```json
{
  "prompt": "Create a customer lifetime value model",
  "materialization": "table",
  "business_context": "E-commerce analytics",
  "save_model": true
}
```

### 4. `compile_model`
Compile a dbt model to check for syntax errors
```json
{
  "model_name": "dim_customers"
}
```

### 5. `run_model`
Execute a dbt model
```json
{
  "model_name": "dim_customers",
  "with_dependencies": true
}
```

### 6. `get_model_lineage`
Get dependency information for a model
```json
{
  "model_name": "dim_customers"
}
```

## Available MCP Resources

### `dbt://manifest`
Access to the complete dbt project manifest with all models and metadata.

## Usage

### 1. Direct Execution
```bash
cd dbt_mcp_hackathon_project
python mcp_main.py
```

### 2. With Kiro IDE
The MCP server is already configured in `.kiro/settings/mcp.json`. Just ensure your `OPENAI_API_KEY` environment variable is set.

### 3. With Other MCP Clients
Configure your MCP client with:
```json
{
  "command": "python",
  "args": ["path/to/dbt_mcp_hackathon_project/mcp_main.py"],
  "env": {
    "OPENAI_API_KEY": "your-api-key-here"
  }
}
```

## Key Advantages Over Custom API

1. **Standard Protocol**: Works with any MCP-compatible AI client
2. **Better AI Integration**: Structured tool calling instead of REST endpoints
3. **Resource Access**: AI can access dbt manifest and other resources directly
4. **Streaming Support**: Real-time responses for model generation
5. **Type Safety**: Proper JSON schema validation for all inputs

## Testing

Run the test client to verify everything works:
```bash
cd dbt_mcp_hackathon_project
python test_mcp_client.py
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Client     │◄──►│   MCP Server     │◄──►│  dbt Project    │
│  (Claude/GPT)   │    │  (real_mcp_      │    │   (models/      │
│                 │    │   server.py)     │    │    manifest)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   ChatGPT API    │
                       │  (model gen)     │
                       └──────────────────┘
```

## Next Steps

- **Phase 2**: Add more advanced tools (model optimization, testing)
- **Phase 3**: Streaming responses for long-running operations
- **Phase 4**: Integration with dbt Cloud API

## Migration Notes

The original FastAPI server (`mcp_server.py`) is still available for backward compatibility, but the MCP server (`real_mcp_server.py`) is now the recommended approach for AI integration.