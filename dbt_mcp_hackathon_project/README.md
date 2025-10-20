# dbt MCP Hackathon Project

A conversational interface for dbt projects that enables natural language exploration and model generation through the **Model Context Protocol (MCP)**.

## 🚀 What's New: Real MCP Server

This project now includes a **real MCP server** that can be used by AI agents like Claude, ChatGPT, and other MCP-compatible clients for seamless dbt integration.

## Quick Start

### Option 1: MCP Server (Recommended)
```bash
cd dbt_mcp_hackathon_project
pip install -r requirements.txt

# Test the MCP server
python test_mcp_client.py

# Run the MCP server
python mcp_main.py
```

### Option 2: Legacy FastAPI Server
```bash
cd dbt_mcp_hackathon_project
pip install -r requirements.txt
python main.py setup
python main.py server start
```

## MCP Integration

### With Kiro IDE
The MCP server is pre-configured in `.kiro/settings/mcp.json`. Just set your `OPENAI_API_KEY` environment variable.

### With Other MCP Clients
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

## Available MCP Tools

- **`list_models`** - List all dbt models with filtering
- **`get_model_details`** - Get detailed model information  
- **`generate_model`** - Generate new models with ChatGPT
- **`compile_model`** - Compile dbt models
- **`run_model`** - Execute dbt models
- **`get_model_lineage`** - Get model dependencies

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Client     │◄──►│   MCP Server     │◄──►│  dbt Project    │
│  (Claude/GPT)   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   ChatGPT API    │
                       │  (model gen)     │
                       └──────────────────┘
```

- **MCP Server**: Real MCP protocol implementation (`backend/real_mcp_server.py`)
- **Legacy API**: FastAPI server for backward compatibility (`backend/mcp_server.py`)
- **Frontend**: Streamlit-based chat interface (`frontend/`)
- **Shared**: Common data models and utilities (`shared/`)

## Configuration

Configuration is handled in `config.py`. Key settings:

- `DBT_PROJECT_PATH` - Path to dbt project
- `DUCKDB_PATH` - Path to DuckDB database
- `OPENAI_API_KEY` - Required for ChatGPT model generation

## Documentation

- [MCP Server Details](MCP_SERVER_README.md) - Complete MCP implementation guide
- [API Reference](backend/) - Legacy FastAPI endpoints