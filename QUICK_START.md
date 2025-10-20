# ⚡ Quick Start Guide

Get up and running with the dbt MCP Hackathon Project in under 5 minutes!

## 🎯 Choose Your Experience

### 🤖 Full AI Experience (Recommended)
Get the best results with ChatGPT integration.

```bash
# 1. Get OpenAI API key
# Visit: https://platform.openai.com/api-keys

# 2. Configure environment
echo "OPENAI_API_KEY=your-api-key-here" > .env

# 3. Test ChatGPT integration
python test_chatgpt_integration.py

# 4. Launch application
python start_full_app.py

# 5. Open http://localhost:8501
```

### ⚡ Fast & Reliable (No API Required)
Use pattern-based AI for instant, reliable results.

```bash
# 1. Launch application
python start_full_app.py

# 2. Open http://localhost:8501
```

## 🧪 Test It Out

Once the app is running, try these prompts in the chat interface:

### Simple Requests
- "Show me all customer models"
- "Create a simple revenue analysis"

### Complex Requests (ChatGPT shines here!)
- "Build a customer lifetime value model that includes total orders, revenue, and average order value"
- "Create a daily revenue analysis combining both jaffle shop and flower shop data"
- "Generate a customer segmentation model based on purchase behavior and frequency"

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

- **Main App**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **AI Status**: http://localhost:8000/ai-status
- **Health Check**: http://localhost:8000/health

## 🆘 Need Help?

- **ChatGPT Issues**: See [CHATGPT_INTEGRATION.md](CHATGPT_INTEGRATION.md)
- **General Setup**: See [FULL_APP_GUIDE.md](FULL_APP_GUIDE.md)
- **Architecture**: See [APP_ARCHITECTURE.md](APP_ARCHITECTURE.md)

---

**Ready to experience the future of dbt development? 🚀**