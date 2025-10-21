# 🚀 dbt MCP Hackathon Project Full Application Guide

*Production-ready with official MCP server and ChatGPT integration!*

## 🎯 What You Get

- **Official MCP Server**: Standards-compliant for AI agent integration
- **ChatGPT Integration**: Real AI model generation with comprehensive dbt context
- **Intelligent Streamlit Frontend**: Single-file app with working chat interface
- **68 dbt Models**: Complete jaffle shop and flower shop analytics
- **Production Features**: Error handling, connection resilience, comprehensive testing

## ⚡ Quick Start

### 1. Start Full Application
```bash
python start_full_app.py
```

### 2. Verify Everything Works
```bash
cd dbt_mcp_hackathon_project
python run_tests.py
```

### 3. Open the App
- **Frontend:** http://localhost:8502
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

---

## Manual Setup (if scripts don't work)

### Step 1: Install Dependencies
```bash
pip install -r dbt_mcp_hackathon_project/requirements.txt
pip install dbt-core dbt-duckdb
```

### Step 1.5: Setup ChatGPT (Optional but Recommended)
```bash
# Get API key from https://platform.openai.com/api-keys
# Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Test integration
cd dbt_mcp_hackathon_project
python run_tests.py
```

### Step 2: Setup dbt Profile
Create `~/.dbt/profiles.yml`:
```yaml
default:
  outputs:
    dev:
      type: duckdb
      path: 'data/dbt_mcp_hackathon_project.duckdb'
      threads: 4
  target: dev
```

### Step 3: Compile dbt Project
```bash
dbt compile
```

### Step 4: Start Backend (Terminal 1)
```bash
cd dbt_mcp_hackathon_project
python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd().parent)); from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer; import uvicorn; mcp_server = MCPServer(); app = mcp_server.get_app(); uvicorn.run(app, host='127.0.0.1', port=8001)"
```

### Step 5: Start Frontend (Terminal 2)
```bash
cd dbt_mcp_hackathon_project
streamlit run full_app.py --server.port 8502
```

---

## 🤖 AI Model Generation Features

### What You Can Do:
1. **Natural Language Prompts:**
   - "create a model to show me the total tax_amt for jaffle_orders?"
   - "build a customer lifetime value model"
   - "generate a daily revenue analysis combining both businesses"

2. **Real SQL Generation:**
   - ChatGPT generates production-ready dbt SQL code
   - Uses your existing 68 models as references
   - Follows dbt best practices with proper {{ ref() }} syntax

3. **Instant Testing:**
   - Compile generated models in Model Explorer
   - Run them against your DuckDB data
   - See actual results and row counts

### Example Workflow:
1. Go to Chat Interface (http://localhost:8502)
2. Type: "create a model to show me the total tax_amt for jaffle_orders?"
3. ChatGPT generates complete dbt SQL with explanation
4. Copy SQL or go to Model Explorer
5. Use Compile/Run buttons to test existing models
6. View actual data results

---

## 🔧 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8001 is in use
netstat -an | grep 8001

# Use the simple startup script
python start_app_simple.py
# Choose option 1 to start backend only
```

### Frontend Issues
```bash
# Check if port 8502 is in use
netstat -an | grep 8502

# Use the simple startup script
python start_app_simple.py
# Choose option 2 to start frontend only
```

### dbt Compilation Errors
```bash
# Check dbt installation
dbt --version

# Debug dbt project
dbt debug

# Clean and recompile
dbt clean
dbt compile
```

### AI Generation Not Working
- Check backend logs for errors
- Verify MCP server is running (http://localhost:8001/health)
- Check if ChatGPT is available (http://localhost:8001/ai-status)
- Ensure OPENAI_API_KEY environment variable is set
- The system automatically falls back to pattern-based AI if ChatGPT unavailable

---

## 🎯 Demo Features

### Model Explorer
- Browse all 68 models from your dbt project
- Search and filter functionality with real-time results
- Compile and run models directly in the interface
- View actual execution results and row counts

### AI Chat Interface
- Real-time ChatGPT model generation
- Intelligent responses using actual project data
- Complete dbt SQL with explanations and next steps
- Context-aware suggestions and help

### Cross-Business Analytics
- Generate models that join jaffle shop + flower shop data
- Customer analysis across both businesses
- Revenue comparisons and trends
- Cross-sell opportunity identification

---

## 📊 API Endpoints

Once running, you can also use the API directly:

### Health Check
```bash
curl http://localhost:8001/health
```

### List Models
```bash
curl http://localhost:8001/models
```

### Generate Model
```bash
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create customer analysis model", "materialization": "view"}'
```

### Compile Model
```bash
curl -X POST "http://localhost:8001/compile?model_name=fct_jaffle_orders"
```

### Run Model
```bash
curl -X POST "http://localhost:8001/run?model_name=fct_jaffle_orders"
```

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Backend health check returns status "healthy" (http://localhost:8001/health)
2. ✅ Frontend loads at http://localhost:8502 with "Backend connected and ready"
3. ✅ Model Explorer shows your 68 dbt models with search and filtering
4. ✅ Chat Interface generates actual SQL from natural language prompts
5. ✅ You can compile and run models with real results and row counts

---

## 💡 Tips for Best Results

1. **Be Specific:** "Create a customer analysis model with total orders and revenue" works better than "analyze customers"

2. **Reference Existing Models:** "Use the stg_jaffle__customers table" helps the AI understand your schema

3. **Specify Materialization:** "Create a table that..." vs "Create a view that..."

4. **Test Incrementally:** Start with simple models, then build complexity

5. **Use the Examples:** The built-in example prompts are designed for your specific data

---

🚀 **You're ready to generate dbt models with AI!**