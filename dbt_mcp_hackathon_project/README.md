# dbt MCP Hackathon Project

A conversational interface for dbt projects that enables natural language exploration and model generation.

## Quick Start

1. **Setup the environment:**
   ```bash
   cd dbt_mcp_hackathon_project
   pip install -r requirements.txt
   python main.py setup
   ```

2. **Start the MCP server:**
   ```bash
   python main.py server start
   ```

3. **Start the frontend (in another terminal):**
   ```bash
   python main.py frontend
   ```

## Architecture

- **Frontend**: Streamlit-based chat interface (`frontend/`)
- **Backend**: MCP server with dbt integration (`backend/`)
- **Shared**: Common data models and utilities (`shared/`)

## API Endpoints

- `GET /health` - Health check
- `GET /models` - List all dbt models
- `GET /models/{model_name}` - Get model details

## Configuration

Configuration is handled in `config.py`. Key settings:

- `MCP_HOST` / `MCP_PORT` - MCP server binding
- `STREAMLIT_HOST` / `STREAMLIT_PORT` - Frontend binding
- `DBT_PROJECT_PATH` - Path to dbt project
- `DUCKDB_PATH` - Path to DuckDB database