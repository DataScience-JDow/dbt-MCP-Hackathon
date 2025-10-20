# 🤖 dbt MCP Hackathon Project

An AI-powered assistant for dbt development that makes model exploration and generation accessible through natural language conversations. Now featuring **real ChatGPT integration** alongside our pattern-based AI system.

## ✨ Features

- **🔍 Model Explorer**: Browse and search your dbt project models with an intuitive interface
- **🤖 Dual AI System**: Choose between ChatGPT (sophisticated) or pattern-based AI (fast & reliable)
- **💬 Natural Language**: "Create a customer lifetime value model" → Working dbt SQL
- **⚡ Real-time Compilation**: Test and run generated models instantly
- **🔄 Hybrid Approach**: Automatically falls back if ChatGPT is unavailable
- **📊 Cross-Business Analytics**: Generate models that span multiple data sources
- **🛠️ Production Ready**: Environment configuration, error handling, and monitoring

## 🚀 Quick Start

### Option 1: Basic Setup (Pattern-Based AI)
```bash
# 1. Install dependencies
python install_deps.py

# 2. Start the application
python start_full_app.py

# 3. Open http://localhost:8501
```

### Option 2: Full Setup (With ChatGPT)
```bash
# 1. Get OpenAI API key from https://platform.openai.com/api-keys
# 2. Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env

# 3. Test ChatGPT integration
python test_chatgpt_integration.py

# 4. Start the application
python start_full_app.py

# 5. Open http://localhost:8501
```

### 🔗 Access Points
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **AI Status**: http://localhost:8000/ai-status

### 🩺 Health Check
```bash
python health_check.py
```

## 🤖 AI Capabilities

### ChatGPT Integration (Recommended)
- **Sophisticated SQL Generation**: Context-aware, follows dbt best practices
- **Natural Language Understanding**: Handles complex, multi-step requests
- **Business Logic**: Understands analytics patterns and metrics
- **Cost**: ~$0.01-0.05 per request

### Pattern-Based AI (Fallback)
- **Fast & Reliable**: <200ms response time, always available
- **Template-Driven**: Good for common dbt patterns
- **No API Dependencies**: Works offline, no costs
- **Predictable**: Consistent results for demos

## 📊 Sample Data

This project includes two sample businesses:
- **Jaffle Shop**: Coffee business with customers, orders, products, and stores
- **Flower Shop**: Flower delivery with arrangements, orders, and delivery data

The dbt project contains 19 pre-built models across staging, intermediate, and mart layers.

## 📚 Documentation

- **[Architecture Overview](APP_ARCHITECTURE.md)**: How everything works together
- **[ChatGPT Integration Guide](CHATGPT_INTEGRATION.md)**: Detailed AI setup and usage
- **[Full Setup Guide](FULL_APP_GUIDE.md)**: Manual installation instructions

## 🎯 Example Prompts

Try these in the chat interface:

```
"Create a customer lifetime value model"
"Build a daily revenue analysis combining both businesses"
"Generate a product performance model with monthly trends"
"Create a customer segmentation based on purchase behavior"
```

## 🛠️ Development

### Testing
```bash
# Test ChatGPT integration
python test_chatgpt_integration.py

# Test overall health
python health_check.py
```

### API Endpoints
- `POST /generate` - Auto-selects best AI
- `POST /generate-chatgpt` - ChatGPT only
- `POST /generate-pattern` - Pattern-based only
- `GET /ai-status` - Check AI service availability

---

*Built with ❤️ for the Coalesce 2025 MCP Hackathon*

**🌟 Now featuring real AI integration - the future of dbt development is conversational!**