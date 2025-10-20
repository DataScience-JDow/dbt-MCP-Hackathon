# 🚀 dbt MCP Hackathon Project Full Application Guide

*Now featuring real ChatGPT integration alongside pattern-based AI!*

## Quick Start Options

### Option A: With ChatGPT (Recommended)
For the full AI experience with sophisticated model generation.

### Option B: Pattern-Based Only
For reliable, fast generation without external API dependencies.

### 1. Install Dependencies
```bash
python install_deps.py
```

### 2. Start Full Application
```bash
python start_full_app.py
```

### 3. Verify Everything Works
```bash
python health_check.py
```

### 4. Open the App
- **Frontend:** http://localhost:8501
- **Backend API:** http://localhost:8000/docs

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
python test_chatgpt_integration.py
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
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Start Frontend (Terminal 2)
```bash
streamlit run dbt_mcp_hackathon_project/frontend/app.py --server.port 8501
```

---

## 🤖 AI Model Generation Features

### What You Can Do:
1. **Natural Language Prompts:**
   - "Create a customer analysis model"
   - "Show monthly revenue trends"
   - "Find customers who shop at both businesses"

2. **Real SQL Generation:**
   - AI generates actual dbt SQL code
   - Uses your existing models as references
   - Follows dbt best practices

3. **Instant Testing:**
   - Compile generated models
   - Run them against your data
   - See results immediately

### Example Workflow:
1. Go to Chat Interface
2. Type: "Create a model showing total orders per customer"
3. AI generates SQL code
4. Click "Compile Model" to test
5. Click "Run Model" to execute
6. View results in the interface

---

## 🔧 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
netstat -an | grep 8000

# Try different port
python -m uvicorn dbt_mcp_hackathon_project.main:app --port 8001
```

### Frontend Issues
```bash
# Check if port 8501 is in use
netstat -an | grep 8501

# Try different port
streamlit run dbt_mcp_hackathon_project/frontend/app.py --server.port 8502
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
- Verify MCP server is running (http://localhost:8000/health)
- The AI service uses mock generation by default
- For real AI, you'd need to configure OpenAI API key

---

## 🎯 Demo Features

### Model Explorer
- Browse all 19 models from your dbt project
- Search and filter functionality
- View model dependencies and lineage
- Real-time model metadata

### AI Chat Interface
- Natural language model generation
- Example prompts for common scenarios
- SQL code preview and editing
- Compile and run capabilities

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
curl http://localhost:8000/health
```

### List Models
```bash
curl http://localhost:8000/models
```

### Generate Model
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create customer analysis model", "materialization": "view"}'
```

### Compile Model
```bash
curl -X POST http://localhost:8000/compile/model_name
```

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Backend health check returns status "healthy"
2. ✅ Frontend loads at http://localhost:8501
3. ✅ Model Explorer shows your 19 dbt models
4. ✅ Chat Interface accepts prompts and generates SQL
5. ✅ You can compile and run generated models

---

## 💡 Tips for Best Results

1. **Be Specific:** "Create a customer analysis model with total orders and revenue" works better than "analyze customers"

2. **Reference Existing Models:** "Use the stg_jaffle__customers table" helps the AI understand your schema

3. **Specify Materialization:** "Create a table that..." vs "Create a view that..."

4. **Test Incrementally:** Start with simple models, then build complexity

5. **Use the Examples:** The built-in example prompts are designed for your specific data

---

🚀 **You're ready to generate dbt models with AI!**