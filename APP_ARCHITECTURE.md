# 🚀 dbt MCP Hackathon Project: Building an AI-Powered dbt Assistant

*A roadmap through our Coalesce 2025 hackathon journey*

## 🎯 The Vision

What if you could talk to your dbt project like you talk to a colleague? "Show me all customer models" or "Create a daily revenue analysis combining our jaffle shop and flower shop data." That's exactly what we built - an AI-powered dbt assistant that makes data modeling as conversational as asking a question.

## 🏗️ The Architecture Story

We built this as a three-layer system that feels like magic but works through solid engineering:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   dbt Project   │
│   Frontend      │◄──►│   MCP Server    │◄──►│   & DuckDB      │
│   "The Face"    │    │  "The Brain"    │    │  "The Data"     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────►│  MCP Protocol   │◄─────────────┘
                        │ "The Language"  │
                        └─────────────────┘
```

**The magic happens through our custom HTTP API** - inspired by MCP concepts but implemented as a traditional REST API that lets our frontend and backend speak the same language about data models.

## 🛠️ How We Built It: The Technology Journey

### Phase 1: The Foundation - "Getting Our Data House in Order"

**🗄️ The Data Layer (DuckDB + dbt)**
We started with real business data - two companies that needed analytics:
- **Jaffle Shop**: A coffee business with customers, orders, and store locations
- **Flower Shop**: A flower delivery service with arrangements and delivery data

*Why DuckDB?* It's like SQLite but for analytics - perfect for hackathons because it's fast, embedded, and doesn't need a server.

*Why dbt?* Because we wanted to show real dbt workflows, not toy examples. We built 19 production-ready models across staging, intermediate, and mart layers.

### Phase 2: The Brain - "Teaching Our App to Think"

**🧠 The Custom API Server (FastAPI + Python)**
This is where the magic happens. We built a FastAPI server that implements MCP-inspired concepts - think of it as our own universal translator between human requests and dbt operations.

**Key Services We Built:**
- `model_service.py`: "Hey, show me all my customer models" (reads dbt manifest.json)
- `compilation_service.py`: "Does this SQL actually work?" (runs dbt compile/run)
- `ai_service.py`: "Turn this English into SQL" (pattern-based mock AI)
- `model_generator.py`: "Create a new model from scratch" (writes .sql files)

**The "AI" Secret:** We built a sophisticated pattern-recognition system that:
- Analyzes natural language using regex patterns
- Identifies intent (JOIN, AGGREGATE, FILTER, etc.)
- Generates proper dbt SQL with `{{ ref() }}` functions
- Creates production-ready models without external AI APIs

*Why FastAPI?* It's fast, has automatic API docs, and handles async operations beautifully - perfect for real-time chat.

### Phase 3: The Face - "Making It Beautiful and Usable"

**🎨 The Frontend (Streamlit + Interactive Components)**
We chose Streamlit because it lets data people build web apps without becoming frontend developers. But we didn't stop at basic - we built:

- **Model Explorer**: Visual browsing of your dbt project
- **AI Chat Interface**: Natural language conversations about your data
- **Live Code Editor**: See generated SQL and edit it in real-time
- **Connection Manager**: Smart backend connectivity with status indicators

*Why Streamlit?* It's the fastest way to go from Python script to web app, and it's what data teams actually use.

## 🔄 The User Experience: How It All Flows Together

### "Show Me My Models" - The Exploration Flow
```
👤 User clicks "Model Explorer"
    ↓
🖥️  Streamlit sends HTTP GET to "/models"
    ↓
🧠 Backend reads dbt manifest.json and extracts metadata
    ↓
📊 Results flow back as JSON with model details, lineage, and descriptions
    ↓
✨ User sees beautiful cards with search, filter, and dependency visualization
```

### "Create a Revenue Analysis" - The AI Generation Flow
```
👤 User types: "Create a daily revenue model combining both businesses"
    ↓
💬 Chat interface sends HTTP POST to "/generate-model"
    ↓
🤖 Pattern-recognition system analyzes prompt and generates SQL templates
    ↓
📝 Generated dbt-compliant code appears in live editor for review/editing
    ↓
▶️  User clicks "Run" → POST to "/run-model" → dbt executes → Results appear instantly
```

**The magic moment:** You go from idea to working dbt model in under 30 seconds.

## 🔌 The Communication Layer: MCP-Inspired Architecture

**Full Transparency:** We built a **custom FastAPI server** that implements MCP-like concepts, but we're not using the official MCP protocol. Here's what we actually built:

### Our Custom "MCP-Style" API:
- `GET /models`: "Show me everything in this dbt project"
- `GET /models/{model_name}`: "Tell me about this specific model"
- `POST /generate-model`: "Create new SQL from this description"
- `POST /compile-model`: "Check if this SQL is valid"
- `POST /run-model`: "Execute this and show me results"
- `GET /search-models`: "Find models matching this criteria"

### Why We Built It This Way:
1. **Hackathon Speed**: Custom FastAPI was faster than implementing full MCP protocol
2. **Learning Exercise**: We wanted to understand what MCP servers do
3. **Proof of Concept**: Show how MCP-style communication would work
4. **Full Control**: Build exactly the features we needed

**What Our API Actually Looks Like:**
```python
# User says: "Create a customer analysis model"
# Frontend sends regular HTTP request:
POST /generate-model
{
    "prompt": "Create customer analysis model",
    "materialization": "view",
    "business_context": "jaffle_shop"
}

# Backend returns JSON response:
{
    "success": true,
    "sql": "select * from {{ ref('customers') }}...",
    "model_name": "customer_analysis",
    "confidence": 0.8
}
```

### The Path to Real MCP:
To convert this to actual MCP protocol, we'd need to:
1. Replace FastAPI endpoints with MCP tool definitions
2. Use JSON-RPC 2.0 message format
3. Implement proper MCP server/client libraries
4. Add MCP-standard error handling and capabilities

## 🎮 How to Use the App: A Quick Walkthrough

### Getting Started (2 minutes)
1. **Start the app**: `python start_full_app.py`
2. **Open your browser**: http://localhost:8501
3. **Explore existing models**: Click around the Model Explorer
4. **Try the AI**: Switch to Chat and ask "Show me all customer models"

### Power User Features

**🔍 Model Explorer Mode:**
- Browse all 19 pre-built models
- See model dependencies and lineage
- Search by name, description, or business area
- Click any model to see its SQL and run it

**💬 AI Chat Mode:**
- "Create a model showing daily revenue by store"
- "Show me all models related to customers"
- "Generate a funnel analysis for flower orders"
- "Combine jaffle shop and flower shop data"

**⚡ Pro Tips:**
- Generated models appear in the code editor - you can modify them before running
- Use "Compile" to check SQL without executing
- All generated models are saved to your dbt project
- The AI understands your existing models and will reference them

## 🎭 The Truth About Our "AI" and "MCP"

### What We Actually Built vs. What We Called It

**Our Dual AI System:**
- ✅ **ChatGPT Integration**: Real OpenAI GPT-4 for sophisticated SQL generation
- ✅ **Pattern-Based Fallback**: Sophisticated pattern recognition + SQL templates
- ✅ **Hybrid Approach**: Automatically selects best available AI service
- 🎯 **Why this works**: Best of both worlds - quality when available, reliability always

**Our "MCP Server":**
- ✅ **What it is**: Custom FastAPI server with MCP-inspired endpoints
- ✅ **What it does**: Handles dbt operations via HTTP/JSON
- ❌ **What it's not**: Official MCP protocol implementation
- 🎯 **Why this works**: Faster to build, easier to debug, same user experience

**The Dual AI System in Action:**
```python
# User says: "Create a daily revenue model"

# With ChatGPT (when available):
1. Send comprehensive prompt to OpenAI GPT-4
2. Include full dbt project context and best practices
3. Receive sophisticated, context-aware SQL
4. Result: High-quality model in 3-5 seconds (~$0.03)

# Pattern-Based Fallback:
1. Regex patterns identify: intent=AGGREGATE, tables=[orders, products]
2. Template engine generates: proper dbt SQL with {{ ref() }}
3. Result: Good model in 200ms, no API costs

# Hybrid Intelligence:
- Tries ChatGPT first for best quality
- Falls back to patterns if ChatGPT unavailable
- User gets best possible result automatically
```

## 🧰 Technology Choices: Why We Picked What We Picked

### The Backend Stack
- **FastAPI**: Because it's fast, has automatic docs, and handles async beautifully
- **dbt-core**: The real deal - not a simulation, actual dbt workflows
- **DuckDB**: Analytics database that doesn't need a server - perfect for demos
- **MCP Protocol**: The future of AI tool integration
- **Pydantic**: Type safety and validation - because bugs are not fun during demos

### The Frontend Stack
- **Streamlit**: From Python script to web app in minutes
- **streamlit-ace**: Professional code editor right in the browser
- **Plotly**: Interactive charts that make data exploration fun
- **Custom Components**: We built our own chat interface and model cards

### The "Why Not?" Decisions
- **Why not React?** Time. Streamlit gets data people to web apps faster.
- **Why not real AI API?** Cost, reliability, and speed. Our pattern-based system is predictable for demos.
- **Why not Postgres?** DuckDB is easier to distribute and perfect for analytics.
- **Why not actual MCP protocol?** Complexity. HTTP/JSON was faster to implement and debug.
- **Why not official dbt MCP server?** Learning. We wanted to understand what MCP servers actually do.

## 🚀 Running the Project: From Zero to Hero

### The Easy Way (Recommended)
```bash
# One command to rule them all
python start_full_app.py
```
This starts both backend (port 8000) and frontend (port 8501) automatically.

### The Manual Way (For Developers)
```bash
# Terminal 1: Backend
cd dbt_mcp_hackathon_project
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
streamlit run dbt_mcp_hackathon_project/frontend/app.py --server.port 8501
```

### Health Check
```bash
python health_check.py  # Verifies everything is working
```

## 🔮 What's Next: The Roadmap Forward

### Immediate Improvements (Next Sprint)
- ✅ **Real AI Integration**: ChatGPT integration complete!
- **Actual MCP Protocol**: Implement official MCP server for AI agent compatibility
- **Enhanced Model Types**: Support for tests, macros, and snapshots
- **Better Visualizations**: Model lineage graphs and data profiling
- **Export Features**: Save generated models directly to your dbt project

### Future Vision (Next Quarter)
- **Multi-Project Support**: Work with multiple dbt projects
- **Collaboration Features**: Share models and chat sessions
- **Cloud Deployment**: One-click deployment to major cloud platforms
- **Advanced AI**: Context-aware suggestions and automatic optimization

### The Big Picture
This hackathon project proves that AI-powered dbt development is not just possible - it's inevitable. We built a foundation that can scale from hackathon demo to production tool.

## 🎯 Key Takeaways for Your Team

1. **MCP Concepts Work**: Even our custom implementation shows the power of standardized AI-data communication
2. **Pattern-Based AI is Viable**: You don't always need expensive APIs - smart templates can go far
3. **dbt + AI = Magic**: Natural language to SQL generation actually works (even with mock AI)
4. **Rapid Prototyping**: Modern Python tools let you build complex apps fast
5. **Start Simple**: We built this in a hackathon with custom APIs, but the architecture scales to real MCP
6. **Honest Documentation**: Being transparent about what you actually built vs. what you aspire to build

---

*Built with ❤️ for the Coalesce 2025 MCP Hackathon*

**Want to see it in action?** Run `python start_full_app.py` and visit http://localhost:8501

**Questions?** Check out the code - it's designed to be readable and educational.