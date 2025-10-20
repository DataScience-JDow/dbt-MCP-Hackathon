# 🚀 dbt MCP Hackathon Project: Building an AI-Powered dbt Assistant

*A roadmap through our Coalesce 2025 hackathon journey*

## 🎯 The Vision

What if you could talk to your dbt project like you talk to a colleague? "Show me all customer models" or "Create a daily revenue analysis combining our jaffle shop and flower shop data." That's exactly what we built - an AI-powered dbt assistant that makes data modeling as conversational as asking a question.

## 🏗️ The Architecture Story

We built this as an AI-powered system that combines multiple intelligence sources with solid engineering:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Custom MCP    │    │   dbt-core      │
│   Frontend      │◄──►│   Server        │◄──►│   Engine        │
│   "The Face"    │    │  "The Brain"    │    │                 │
└─────────────────┘    └─────────────────┘    │ • Compilation   │
         │                       │             │ • Execution     │
         │              ┌─────────────────┐    │ • Manifest      │
         └─────────────►│ MCP-Inspired    │    └─────────────────┘
                        │ HTTP Protocol   │             │
                        └─────────────────┘             │
                                 │                      │
                    ┌────────────┴────────────┐         │
                    │                         │         │
          ┌─────────────────┐       ┌─────────────────┐ │
          │   OpenAI GPT-4  │       │  Pattern-Based  │ │
          │   "Smart AI"    │       │  "Reliable AI"  │ │
          │                 │       │                 │ │
          │ • Context-aware │       │ • Always works  │ │
          │ • Sophisticated │       │ • <200ms speed  │ │
          │ • $0.01-0.05    │       │ • Zero cost     │ │
          └─────────────────┘       └─────────────────┘ │
                                                        │
                              ┌─────────────────────────┘
                              │
                    ┌─────────────────┐
                    │    DuckDB       │
                    │   Database      │
                    │                 │
                    │ • Jaffle Shop   │
                    │ • Flower Shop   │
                    │ • 19 Models     │
                    └─────────────────┘
```

**The magic happens through intelligent AI routing** - our system automatically chooses the best available AI service, ensuring users get sophisticated results when possible and reliable results always.

## 🔌 MCP Integration Strategy

### How We Implement MCP Concepts

**Tool-Based Architecture (MCP Pattern):**
```
MCP Tools We Implement:
├── list_models      → GET /models (browse dbt project)
├── get_model_info   → GET /models/{name} (model details)
├── generate_model   → POST /generate (AI SQL generation)
├── compile_model    → POST /compile (dbt compile)
├── run_model        → POST /run (dbt run)
└── validate_sql     → POST /validate (SQL validation)
```

**Structured Communication (MCP Style):**
```json
// Request Format (MCP-inspired)
{
  "tool": "generate_model",
  "arguments": {
    "prompt": "Create customer analysis model",
    "materialization": "view",
    "context": ["customers", "orders"]
  }
}

// Response Format (MCP-compatible)
{
  "success": true,
  "content": [
    {
      "type": "text", 
      "text": "Generated SQL with dbt best practices..."
    }
  ],
  "metadata": {
    "model_name": "customer_analysis",
    "confidence": 0.95
  }
}
```

### Integration with Official dbt MCP Server

**Current State:**
- **Custom Implementation**: We built our own dbt integration for rapid prototyping
- **MCP Concepts**: Using MCP design patterns without official protocol
- **Direct dbt-core**: Calling dbt compile/run commands directly

**Future Migration Path:**
```
Phase 1: Current (Custom FastAPI)
├── Direct dbt-core integration
├── Custom HTTP/JSON protocol  
└── MCP-inspired tool structure

Phase 2: Hybrid (Both Systems)
├── Keep custom server for UI
├── Add official dbt MCP server
└── Route complex queries to dbt MCP

Phase 3: Full MCP (Standardized)
├── Migrate to official dbt MCP server
├── Use JSON-RPC 2.0 protocol
└── Compatible with all MCP clients
```

**Why This Architecture Works:**
- **Rapid Development**: Custom server let us iterate quickly during hackathon
- **MCP Compatibility**: Easy migration path to official protocol
- **AI Integration**: Our dual AI system works with any MCP backend
- **Future-Proof**: Architecture scales from prototype to production

### Custom MCP vs Official dbt MCP Server

| Aspect | Our Custom MCP Server | Official dbt MCP Server |
|--------|----------------------|-------------------------|
| **Protocol** | HTTP/JSON (MCP-inspired) | JSON-RPC 2.0 (Official MCP) |
| **dbt Integration** | Direct dbt-core calls | Standardized dbt operations |
| **AI Integration** | Built-in dual AI system | External AI agent required |
| **Development Speed** | Very fast (hackathon-friendly) | Slower (protocol compliance) |
| **Standardization** | Custom implementation | Industry standard |
| **Agent Compatibility** | Limited to our frontend | Works with any MCP client |
| **Maintenance** | We maintain everything | Community-maintained dbt parts |

**Our Strategic Approach:**
1. **Hackathon Phase**: Custom MCP server for rapid prototyping ✅
2. **Production Phase**: Migrate to official dbt MCP server for standardization
3. **AI Layer**: Keep our dual AI system as a wrapper around any MCP backend
4. **Best of Both**: Maintain the user experience while gaining MCP ecosystem benefits

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
- `chatgpt_service.py`: "Turn this English into SQL" (OpenAI GPT-4 integration)
- `ai_service.py`: "Backup AI system" (pattern-based fallback for reliability)
- `model_generator.py`: "Create a new model from scratch" (writes .sql files)

**The AI Intelligence:** We built a dual AI system that combines the best of both worlds:
- **Primary**: OpenAI GPT-4 for sophisticated, context-aware SQL generation
- **Fallback**: Pattern-recognition system for reliability and speed
- **Smart Routing**: Automatically selects the best available AI service
- **dbt Context**: Both systems understand your project structure and best practices

*Why FastAPI?* It's fast, has automatic API docs, and handles async operations beautifully - perfect for real-time AI chat.

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
🤖 ChatGPT analyzes prompt with full dbt project context and generates sophisticated SQL
    ↓
📝 Generated dbt-compliant code appears in live editor for review/editing
    ↓
▶️  User clicks "Run" → POST to "/run-model" → dbt executes → Results appear instantly
```

**Intelligent AI Selection Flow:**
```
👤 User Request: "Create a customer analysis model"
    ↓
💬 Chat Interface → FastAPI Server
    ↓
🧠 AI Router Decision Tree:
    ├─ OpenAI Available? ✅ → ChatGPT Service
    │   ├─ API Key configured? ✅
    │   ├─ Credits available? ✅  
    │   ├─ API responding? ✅
    │   └─ Generate with GPT-4 (3-5s, high quality)
    │
    └─ OpenAI Unavailable? ❌ → Pattern AI Service
        ├─ Instant fallback (no delay)
        ├─ Parse intent with regex patterns
        └─ Generate with templates (<200ms, reliable)
    ↓
📝 Generated SQL → Code Editor → User Review → dbt Execution
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

## 🎭 Our AI-Powered Architecture

### The Intelligent System We Built

**Our Dual AI Engine:**
- 🧠 **Primary AI**: OpenAI GPT-4 integration for sophisticated, context-aware SQL generation
- ⚡ **Backup AI**: Pattern-based system for instant reliability and zero-cost operation
- 🔄 **Smart Routing**: Automatically selects optimal AI service based on availability
- 🎯 **Why this works**: Users get the best possible experience with built-in reliability

**Our MCP-Inspired Server:**
- ✅ **What it is**: Custom FastAPI server implementing MCP-style communication patterns
- ✅ **What it does**: Handles dbt operations via structured HTTP/JSON API
- ✅ **MCP Concepts Used**: Tool-based architecture, structured requests/responses, capability discovery
- ✅ **dbt Integration**: Direct dbt-core integration for compilation, execution, and manifest parsing
- 🎯 **Future path**: Migration to official dbt MCP server for standardized AI agent compatibility

**The AI System in Action:**
```python
# User says: "Create a daily revenue model"

# Primary Path (ChatGPT):
1. Send comprehensive prompt to OpenAI GPT-4
2. Include full dbt project context and best practices
3. Receive sophisticated, context-aware SQL
4. Result: High-quality model in 3-5 seconds (~$0.03)

# Fallback Path (Pattern AI):
1. Regex patterns identify: intent=AGGREGATE, tables=[orders, products]
2. Template engine generates: proper dbt SQL with {{ ref() }}
3. Result: Reliable model in 200ms, no API costs

# Intelligent Routing:
- Always attempts ChatGPT first for best quality
- Seamlessly falls back if API unavailable
- User experience remains consistent regardless of backend
```

## 🧰 Technology Choices: Why We Picked What We Picked

### The Backend Stack
- **FastAPI**: Because it's fast, has automatic docs, and handles async beautifully
- **OpenAI GPT-4**: Primary AI engine for sophisticated SQL generation
- **dbt-core**: The real deal - not a simulation, actual dbt workflows
- **DuckDB**: Analytics database that doesn't need a server - perfect for demos
- **Custom AI Router**: Intelligent selection between ChatGPT and pattern-based AI
- **Pydantic**: Type safety and validation - because bugs are not fun during demos

### The Frontend Stack
- **Streamlit**: From Python script to web app in minutes
- **streamlit-ace**: Professional code editor right in the browser
- **Plotly**: Interactive charts that make data exploration fun
- **Custom Components**: We built our own chat interface and model cards

### The "Why Not?" Decisions
- **Why not React?** Time. Streamlit gets data people to web apps faster.
- **Why dual AI instead of just ChatGPT?** Reliability. We wanted guaranteed uptime even if APIs fail.
- **Why not Postgres?** DuckDB is easier to distribute and perfect for analytics.
- **Why custom MCP vs official protocol?** Speed. HTTP/JSON let us iterate faster during hackathon development.
- **Why not official dbt MCP server?** Learning. We wanted to understand the full stack and customize for our use case.

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
- **Official MCP Protocol**: Migrate from custom HTTP API to official MCP standard
- **Enhanced Model Types**: Support for tests, macros, and snapshots
- **Better Visualizations**: Model lineage graphs and data profiling
- **Advanced AI Features**: Streaming responses, model optimization suggestions
- **Multi-Model Conversations**: Handle complex requests spanning multiple models

### Future Vision (Next Quarter)
- **Multi-Project Support**: Work with multiple dbt projects
- **Collaboration Features**: Share models and chat sessions
- **Cloud Deployment**: One-click deployment to major cloud platforms
- **Advanced AI**: Context-aware suggestions and automatic optimization

### The Big Picture
This hackathon project proves that AI-powered dbt development is not just possible - it's inevitable. We built a foundation that can scale from hackathon demo to production tool.

## 🎯 Key Takeaways for Your Team

1. **AI-First Architecture**: Building with real AI from day one creates fundamentally better user experiences
2. **Reliability Through Redundancy**: Dual AI systems ensure users always get results, regardless of external dependencies
3. **dbt + AI = Magic**: Natural language to SQL generation transforms how teams interact with data
4. **Rapid Prototyping**: Modern Python tools + AI APIs let you build sophisticated apps incredibly fast
5. **MCP Design Patterns**: Even custom implementations benefit from MCP's structured approach to AI communication
6. **Production Considerations**: Environment management, cost optimization, and fallback strategies are crucial for real deployments

---

*Built with ❤️ for the Coalesce 2025 MCP Hackathon*

**Want to see it in action?** Run `python start_full_app.py` and visit http://localhost:8501

**Questions?** Check out the code - it's designed to be readable and educational.