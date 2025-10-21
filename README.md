# 🤖 dbt MCP Hackathon Project

A production-ready AI-powered assistant for dbt development featuring **official MCP server integration** and **real ChatGPT model generation**. Transform natural language into working dbt models instantly.

## ✨ Features

- **🔧 Official MCP Server**: Standards-compliant server for AI agent integration (Claude, ChatGPT, Kiro IDE)
- **🤖 ChatGPT Integration**: Real AI model generation with comprehensive dbt context (68 models)
- **💬 Intelligent Chat**: "create a model to show me the total tax_amt for jaffle_orders?" → Working dbt SQL
- **⚡ Model Explorer**: Browse, compile, and run models with real results and row counts
- **🔄 Resilient Architecture**: DuckDB connection handling, port conflict resolution, graceful fallbacks
- **📊 Production Data**: 68 real dbt models across jaffle shop and flower shop businesses
- **🛠️ Production Ready**: Comprehensive testing, error handling, and deployment options

## 🚀 Quick Start

### One-Command Launch
```bash
# 1. Optional: Set up ChatGPT (get key from https://platform.openai.com/api-keys)
export OPENAI_API_KEY='your-api-key-here'

# 2. Start everything
python start_full_app.py

# 3. Open http://localhost:8502
```

### Alternative: Guided Setup
```bash
# Interactive startup with options
python start_app_simple.py
```

### 🔗 Access Points
- **Frontend**: http://localhost:8502
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **AI Status**: http://localhost:8001/ai-status

### 🩺 Health Check
```bash
cd dbt_mcp_hackathon_project
python run_tests.py
```

## 🤖 AI Capabilities

### ChatGPT Integration (Production Ready)
- **Comprehensive dbt Context**: Full access to 68 models, relationships, and metadata
- **Real-time Generation**: Instant model creation directly in chat interface
- **Production SQL**: Proper {{ ref() }} syntax, dbt best practices, business logic
- **Cost**: ~$0.01-0.05 per request

### Pattern-Based AI (Intelligent Fallback)
- **Zero Latency**: <200ms response time, always available
- **Reliable**: Works offline, no API dependencies or costs
- **Smart Routing**: Automatically used when ChatGPT unavailable

## 📊 Production Data

This project includes comprehensive sample data:
- **Jaffle Shop**: Coffee business with customers, orders, products, and stores
- **Flower Shop**: Flower delivery with arrangements, orders, and delivery data

The dbt project contains **68 production models** across staging, intermediate, and mart layers with full lineage and documentation.

## 📚 Documentation

- **[Architecture Overview](APP_ARCHITECTURE.md)**: How everything works together
- **[ChatGPT Integration Guide](CHATGPT_INTEGRATION.md)**: Detailed AI setup and usage
- **[Full Setup Guide](FULL_APP_GUIDE.md)**: Manual installation instructions

## 🎯 Example Prompts

Try these in the chat interface (http://localhost:8502):

```
"create a model to show me the total tax_amt for jaffle_orders?"
"build a customer lifetime value model with total orders and revenue"
"generate a daily revenue analysis combining both businesses"
"show me all customer-related models in my project"
```

## 🛠️ Development & Integration

### Testing
```bash
# Comprehensive test suite
cd dbt_mcp_hackathon_project
python run_tests.py

# Test MCP server
python test_mcp_client.py
```

### MCP Server (For AI Agents)
```bash
# Start MCP server for Claude, ChatGPT, Kiro IDE
cd dbt_mcp_hackathon_project
python mcp_main.py
```

### API Endpoints (Legacy)
- `POST /generate` - Auto-selects best AI (port 8001)
- `GET /ai-status` - Check AI service availability
- `GET /models` - List all dbt models
- `POST /compile` - Compile dbt models
- `POST /run` - Execute dbt models

---

*Built with ❤️ for the Coalesce 2025 MCP Hackathon*

**🏆 Production-ready with official MCP server, real ChatGPT integration, and 68 working dbt models - the future of dbt development is here!**