# 🤖 dbt MCP Hackathon Project

An AI-powered assistant for dbt development that makes model exploration and generation accessible through natural language conversations.

## Features

- **Model Explorer**: Browse and search your dbt project models with an intuitive interface
- **AI Model Generation**: Create new dbt models using natural language prompts
- **Real-time Compilation**: Test and run generated models instantly
- **Cross-Business Analytics**: Generate models that span multiple data sources
- **MCP Integration**: Built on Model Context Protocol for extensible AI communication

## Quick Start

### 1. Install Dependencies
```bash
python install_deps.py
```

### 2. Start the Application
```bash
python start_full_app.py
```

### 3. Open the App
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000/docs

### 4. Verify Health
```bash
python health_check.py
```

## Sample Data

This project includes two sample businesses:
- **Jaffle Shop**: Coffee business with customers, orders, products, and stores
- **Flower Shop**: Flower delivery with arrangements, orders, and delivery data

The dbt project contains 19 pre-built models across staging, intermediate, and mart layers.

## Architecture

See [APP_ARCHITECTURE.md](APP_ARCHITECTURE.md) for a detailed overview of how the database, MCP server, dbt project, and Streamlit application interact.

## Manual Setup

If the automated scripts don't work, see [FULL_APP_GUIDE.md](FULL_APP_GUIDE.md) for detailed manual setup instructions.

---

*Created for the dbt MCP server hackathon during Coalesce 2025*