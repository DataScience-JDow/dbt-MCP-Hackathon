# 🏗️ dbt MCP Hackathon Project Architecture Overview

## High-Level System Architecture

dbt MCP Hackathon Project is an AI-powered assistant for dbt development that combines multiple technologies to provide an intuitive interface for model exploration and generation. Here's how all the components work together:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   dbt Project   │
│   Frontend      │◄──►│   Backend       │◄──►│   & Database    │
│   (Port 8501)   │    │   (Port 8000)   │    │   (DuckDB)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────►│  MCP Protocol   │◄─────────────┘
                        │  Communication  │
                        └─────────────────┘
```

## Component Breakdown

### 1. Database Layer (DuckDB)
- **File**: `jaffle_and_flower_shop.duckdb`
- **Purpose**: Stores all business data for two sample companies
- **Data Sources**:
  - Jaffle Shop: Coffee business (customers, orders, products, stores)
  - Flower Shop: Flower delivery business (flowers, arrangements, orders)
- **Access**: Connected via dbt profiles and direct database connections

### 2. dbt Project Layer
- **Files**: `dbt_project.yml`, `models/`, `seeds/`, `macros/`
- **Purpose**: Defines data transformations and business logic
- **Models**: 19 pre-built models across staging, intermediate, and mart layers
- **Configuration**: Profiles in `profiles.yml` define database connections

### 3. MCP Server (Backend)
- **File**: `dbt_mcp_hackathon_project/backend/mcp_server.py`
- **Port**: 8000
- **Purpose**: Implements Model Context Protocol for AI communication
- **Key Services**:
  - `model_service.py`: Manages dbt model operations
  - `compilation_service.py`: Handles dbt compile/run operations
  - `ai_service.py`: Processes AI model generation requests
  - `model_generator.py`: Creates SQL code from natural language

### 4. Streamlit Frontend
- **File**: `dbt_mcp_hackathon_project/frontend/app.py`
- **Port**: 8501
- **Purpose**: Provides user interface for model exploration and AI interaction
- **Key Components**:
  - `model_explorer.py`: Browse and search existing models
  - `chat_interface.py`: AI conversation interface
  - `code_editor.py`: SQL code editing and preview
  - `connection_manager.py`: Manages backend connectivity

## Data Flow Architecture

### Model Exploration Flow
```
User Request → Streamlit UI → MCP Client → Backend API → dbt Project → Database
     ↓              ↓            ↓           ↓            ↓           ↓
Display Results ← UI Update ← MCP Response ← JSON Data ← Model Info ← Query Results
```

### AI Model Generation Flow
```
Natural Language → Chat Interface → MCP Protocol → AI Service → Model Generator
      ↓                 ↓              ↓            ↓            ↓
   SQL Code ← Code Editor ← MCP Response ← Generated SQL ← Template Engine
      ↓
   Compile/Run → dbt Commands → Database Execution → Results Display
```

## MCP Protocol Integration

The Model Context Protocol (MCP) serves as the communication bridge between the frontend and backend:

### MCP Tools Available:
1. **list_models**: Retrieve all dbt models with metadata
2. **get_model_details**: Get specific model information and dependencies
3. **generate_model**: Create new dbt models from natural language
4. **compile_model**: Test model compilation without execution
5. **run_model**: Execute models and return results
6. **search_models**: Find models by name or description

### MCP Communication Pattern:
```python
# Frontend sends MCP request
request = {
    "method": "tools/call",
    "params": {
        "name": "generate_model",
        "arguments": {
            "prompt": "Create customer analysis model",
            "materialization": "view"
        }
    }
}

# Backend processes via MCP server
response = await mcp_server.handle_request(request)

# Returns structured result
{
    "content": [
        {
            "type": "text",
            "text": "Generated SQL model code..."
        }
    ]
}
```

## Key Interactions

### 1. Model Discovery
- User opens Model Explorer
- Frontend calls `list_models` via MCP
- Backend queries dbt project metadata
- Results displayed with search/filter capabilities

### 2. AI Model Generation
- User enters natural language prompt
- Frontend sends prompt via MCP `generate_model`
- Backend AI service processes request
- Model generator creates SQL using existing models as context
- Generated code returned to frontend for preview/editing

### 3. Model Compilation & Execution
- User clicks "Compile" or "Run" on generated model
- Frontend sends MCP request to backend
- Backend executes dbt commands
- Results streamed back to frontend
- Success/error status displayed to user

## Technology Stack

### Backend Technologies:
- **FastAPI**: Web framework for MCP server
- **dbt-core**: Data transformation engine
- **DuckDB**: Embedded analytical database
- **Pydantic**: Data validation and serialization
- **asyncio**: Asynchronous request handling

### Frontend Technologies:
- **Streamlit**: Web application framework
- **streamlit-ace**: Code editor component
- **pandas**: Data manipulation and display
- **plotly**: Interactive visualizations
- **requests**: HTTP client for MCP communication

### Development Tools:
- **pytest**: Testing framework
- **uvicorn**: ASGI server for FastAPI
- **python-multipart**: File upload handling

## Deployment Architecture

### Local Development:
```bash
# Terminal 1: Start MCP Backend
python start_full_app.py  # Starts both backend and frontend

# Or manually:
# Terminal 1: Backend
cd dbt_mcp_hackathon_project && python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend  
streamlit run dbt_mcp_hackathon_project/frontend/app.py --server.port 8501
```

### Production Considerations:
- Backend can be deployed as containerized FastAPI service
- Frontend can be deployed via Streamlit Cloud or containerized
- Database can be replaced with cloud data warehouse (Snowflake, BigQuery, etc.)
- MCP protocol enables distributed deployment across services

## Security & Configuration

### Environment Variables:
- Database connection strings in `profiles.yml`
- API keys for AI services (if using real AI instead of mock)
- CORS settings for cross-origin requests

### Data Access:
- Read-only access to source data
- Generated models create new views/tables
- No modification of existing business data
- Sandbox environment for testing generated models

This architecture provides a scalable, maintainable foundation for AI-powered dbt development while maintaining clear separation of concerns between data, logic, and presentation layers.