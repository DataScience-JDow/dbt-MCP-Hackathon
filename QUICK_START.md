# ⚡ Quick Start Guide

Get up and running with the dbt MCP Hackathon Project in under 2 minutes!

## 🚀 One-Command Start

### 🤖 Full AI Experience (Recommended)
```bash
# 1. Get OpenAI API key from https://platform.openai.com/api-keys
# 2. Set environment variable
export OPENAI_API_KEY='your-api-key-here'

# 3. Launch everything
python start_full_app.py

# 4. Open http://localhost:8502
```

### ⚡ Fast & Reliable (No API Required)
```bash
# 1. Launch application (uses pattern-based AI fallback)
python start_full_app.py

# 2. Open http://localhost:8502
```

## 🧪 Alternative: Step-by-Step
```bash
# Option 1: Use the guided startup
python start_app_simple.py

# Option 2: Test everything first
cd dbt_mcp_hackathon_project
python run_tests.py
```

## 🧪 Test It Out

Once the app is running, try these prompts in the chat interface:

### Simple Requests
- "Show me all customer models"
- "Create a simple revenue analysis"

### Complex Requests (ChatGPT shines here!)
- "create a model to show me the total tax_amt for jaffle_orders?"
- "build a customer lifetime value model that includes total orders, revenue, and average order value"
- "generate a daily revenue analysis combining both jaffle shop and flower shop data"

## 🔍 What You'll See

### With ChatGPT
- Sophisticated, context-aware SQL
- Proper business logic and comments
- Handles complex multi-table requests
- ~3-5 second response time

### With Pattern-Based AI
- Fast, template-driven SQL
- Good for common dbt patterns
- <200ms response time
- Always available

## 🌐 Access Points

- **Main App**: http://localhost:8502
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **AI Status**: http://localhost:8001/ai-status
- **Health Check**: http://localhost:8001/health

## 🆘 Need Help?

- **ChatGPT Issues**: See [CHATGPT_INTEGRATION.md](CHATGPT_INTEGRATION.md)
- **General Setup**: See [FULL_APP_GUIDE.md](FULL_APP_GUIDE.md)
- **Architecture**: See [APP_ARCHITECTURE.md](APP_ARCHITECTURE.md)

---

**Ready to experience the future of dbt development? 🚀**