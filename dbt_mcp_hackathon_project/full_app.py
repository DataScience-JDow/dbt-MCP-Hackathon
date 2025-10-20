#!/usr/bin/env python3
"""
Complete dbt MCP Hackathon Project Streamlit Application
Single-file version to avoid import issues
"""
import streamlit as st
import requests
import json
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Page configuration
st.set_page_config(
    page_title="dbt MCP Hackathon Project",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .model-card {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'backend_connected' not in st.session_state:
    st.session_state.backend_connected = False
if 'models_cache' not in st.session_state:
    st.session_state.models_cache = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'backend_url' not in st.session_state:
    st.session_state.backend_url = "http://localhost:8000"

def check_backend_connection():
    """Check if backend is connected"""
    try:
        response = requests.get(f"{st.session_state.backend_url}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.backend_connected = True
            return True, response.json()
        else:
            st.session_state.backend_connected = False
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        st.session_state.backend_connected = False
        return False, str(e)

def load_models():
    """Load models from backend"""
    if not st.session_state.backend_connected:
        return None
    
    try:
        response = requests.get(f"{st.session_state.backend_url}/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.session_state.models_cache = data
            return data
        else:
            st.error(f"Failed to load models: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None

def get_ai_status():
    """Get AI service status"""
    try:
        response = requests.get(f"{st.session_state.backend_url}/ai-status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_model(prompt: str, materialization: str = "view"):
    """Generate a model using AI"""
    try:
        payload = {
            "prompt": prompt,
            "materialization": materialization
        }
        response = requests.post(
            f"{st.session_state.backend_url}/generate", 
            json=payload, 
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def compile_model(model_name: str):
    """Compile a model"""
    try:
        response = requests.post(
            f"{st.session_state.backend_url}/compile",
            params={"model_name": model_name},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_model(model_name: str, with_dependencies: bool = False):
    """Run a model"""
    try:
        response = requests.post(
            f"{st.session_state.backend_url}/run",
            params={"model_name": model_name, "with_dependencies": with_dependencies},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_models(query: str):
    """Search models by name or description"""
    try:
        response = requests.get(
            f"{st.session_state.backend_url}/search/models",
            params={"q": query, "limit": 10},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_model_details(model_name: str):
    """Get detailed information about a specific model"""
    try:
        response = requests.get(
            f"{st.session_state.backend_url}/models/{model_name}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def generate_intelligent_response(user_input: str) -> str:
    """Generate an intelligent response based on user input and available data"""
    user_lower = user_input.lower()
    
    # Load models if not cached
    if st.session_state.models_cache is None:
        load_models()
    
    # Special handling for model generation requests
    if any(word in user_lower for word in ["generate", "create", "build", "make"]) and "model" in user_lower:
        # Check if this looks like a specific model generation request
        if any(indicator in user_lower for indicator in ["show", "total", "sum", "calculate", "aggregate", "count"]):
            try:
                result = generate_model(user_input, "view")
                
                if result.get('success'):
                    response = f"✅ **I've generated that model for you!**\n\n"
                    response += f"**Model Name**: `{result.get('model_name', 'Unknown')}`\n"
                    response += f"**Description**: {result.get('description', 'No description')}\n\n"
                    response += "**Generated SQL**:\n```sql\n"
                    response += result.get('sql', 'No SQL generated')
                    response += "\n```\n\n"
                    
                    if result.get('confidence'):
                        response += f"**Confidence**: {result.get('confidence'):.1%}\n"
                    
                    if result.get('reasoning'):
                        response += f"**How I built this**: {result.get('reasoning')}\n\n"
                    
                    response += "💡 **Next steps**:\n"
                    response += "• Copy this SQL to create a new `.sql` file in your `models/` folder\n"
                    response += "• Use the **Model Generation** page to save it directly\n"
                    response += "• Ask me to modify or improve the model\n"
                    
                    if result.get('warnings'):
                        response += f"\n⚠️ **Notes**:\n"
                        for warning in result['warnings']:
                            response += f"• {warning}\n"
                    
                    return response
                else:
                    error_msg = result.get('error', 'Unknown error')
                    return f"❌ I had trouble generating that model: {error_msg}\n\n" + \
                           "Let me help you differently:\n" + \
                           "• Try being more specific about the calculation\n" + \
                           "• Tell me which table/model to use as the source\n" + \
                           "• Use the **Model Generation** page for a guided experience\n\n" + \
                           "Or ask me: 'What models do I have?' to see your available data sources."
            
            except Exception as e:
                return f"❌ I encountered an error: {str(e)}\n\n" + \
                       "Please try the **Model Generation** page or ask me to list your models first."
    
    # Handle model-related queries
    if any(word in user_lower for word in ["models", "model", "table", "view"]):
        if "how many" in user_lower or "count" in user_lower:
            if st.session_state.models_cache:
                count = st.session_state.models_cache.get('total_count', 0)
                return f"You have **{count} models** in your dbt project. Here's a breakdown:\n\n" + \
                       f"• Total models: {count}\n" + \
                       f"• Database connected: {'✅ Yes' if st.session_state.backend_connected else '❌ No'}\n\n" + \
                       "Would you like me to show you specific models or help you explore them?"
            else:
                return "I'm having trouble accessing your models right now. Please make sure the backend is connected."
        
        elif "list" in user_lower or "show" in user_lower:
            if st.session_state.models_cache:
                models = st.session_state.models_cache.get('models', [])[:5]  # Show first 5
                if models:
                    response = "Here are some of your dbt models:\n\n"
                    for model in models:
                        response += f"**{model['name']}**\n"
                        response += f"• Type: {model.get('materialization', 'Unknown')}\n"
                        response += f"• Description: {model.get('description', 'No description')}\n"
                        response += f"• Columns: {len(model.get('columns', []))}\n\n"
                    response += f"And {st.session_state.models_cache.get('total_count', 0) - 5} more models. "
                    response += "Use the Model Explorer to see all models or ask me about specific ones!"
                    return response
                else:
                    return "I couldn't find any models. Please check if your dbt project is properly configured."
            else:
                return "Let me load your models first... Please make sure the backend is connected."
        
        elif "search" in user_lower or "find" in user_lower:
            # Extract search term (simple approach)
            words = user_input.split()
            search_terms = [word for word in words if word.lower() not in ["search", "find", "for", "model", "models", "me", "a", "the"]]
            if search_terms:
                search_term = " ".join(search_terms)
                search_results = search_models(search_term)
                if search_results and search_results.get('results'):
                    response = f"I found **{len(search_results['results'])} models** matching '{search_term}':\n\n"
                    for model in search_results['results'][:3]:  # Show top 3
                        response += f"**{model['name']}**\n"
                        response += f"• Type: {model.get('materialization', 'Unknown')}\n"
                        response += f"• Description: {model.get('description', 'No description')}\n\n"
                    if len(search_results['results']) > 3:
                        response += f"And {len(search_results['results']) - 3} more results. "
                    response += "Would you like details about any specific model?"
                    return response
                else:
                    return f"I couldn't find any models matching '{search_term}'. Try a different search term or browse all models in the Model Explorer."
            else:
                return "What would you like me to search for? Please specify a model name or keyword."
    
    # Handle other generation queries (non-specific)
    elif any(word in user_lower for word in ["generate", "create", "build", "make"]) and "model" in user_lower:
        return "I can help you generate a new dbt model! 🎯\n\n" + \
               "Here's what I need:\n" + \
               "• **Description**: What should the model do?\n" + \
               "• **Data source**: Which tables/models should it use?\n" + \
               "• **Business logic**: Any specific calculations or transformations?\n\n" + \
               "Try asking something like:\n" + \
               "• 'Create a model to show total revenue by customer'\n" + \
               "• 'Build a model that calculates monthly sales'\n" + \
               "• 'Generate a customer lifetime value model'\n\n" + \
               "Or use the **Model Generation** page for a guided experience!"
    
    # Handle specific model name queries (e.g., "tell me about dim_customers")
    elif "about" in user_lower or "details" in user_lower or "info" in user_lower:
        # Try to extract model name
        words = user_input.split()
        potential_model_names = []
        for word in words:
            if len(word) > 3 and word.lower() not in ["about", "tell", "details", "info", "model", "the", "me"]:
                potential_model_names.append(word)
        
        if potential_model_names and st.session_state.models_cache:
            # Look for exact or partial matches
            models = st.session_state.models_cache.get('models', [])
            for potential_name in potential_model_names:
                for model in models:
                    if potential_name.lower() in model.get('name', '').lower():
                        model_details = get_model_details(model['name'])
                        if model_details:
                            response = f"Here's information about **{model['name']}**:\n\n"
                            response += f"• **Type**: {model_details.get('materialization', 'Unknown')}\n"
                            response += f"• **Description**: {model_details.get('description', 'No description')}\n"
                            response += f"• **Path**: {model_details.get('path', 'Unknown')}\n"
                            response += f"• **Columns**: {len(model_details.get('columns', []))}\n"
                            
                            if model_details.get('depends_on'):
                                response += f"• **Depends on**: {', '.join(model_details['depends_on'][:3])}"
                                if len(model_details['depends_on']) > 3:
                                    response += f" and {len(model_details['depends_on']) - 3} more"
                                response += "\n"
                            
                            if model_details.get('referenced_by'):
                                response += f"• **Used by**: {', '.join(model_details['referenced_by'][:3])}"
                                if len(model_details['referenced_by']) > 3:
                                    response += f" and {len(model_details['referenced_by']) - 3} more"
                                response += "\n"
                            
                            if model_details.get('columns'):
                                response += f"\n**Key Columns**:\n"
                                for col in model_details['columns'][:5]:  # Show first 5 columns
                                    response += f"• `{col['name']}` ({col.get('data_type', 'unknown')})"
                                    if col.get('description'):
                                        response += f": {col['description']}"
                                    response += "\n"
                                if len(model_details['columns']) > 5:
                                    response += f"• ... and {len(model_details['columns']) - 5} more columns\n"
                            
                            response += "\nWould you like me to compile or run this model?"
                            return response
        
        return "I'd be happy to tell you about a specific model! Please provide the model name, like 'Tell me about dim_customers' or 'What is the orders model?'"
    
    # Handle specific model queries by keyword
    elif any(model_word in user_lower for model_word in ["customer", "order", "product", "sales", "revenue"]):
        # Try to find models with these keywords
        if st.session_state.models_cache:
            models = st.session_state.models_cache.get('models', [])
            matching_models = []
            for model in models:
                model_name_lower = model.get('name', '').lower()
                model_desc_lower = model.get('description', '').lower()
                if any(keyword in model_name_lower or keyword in model_desc_lower 
                       for keyword in ["customer", "order", "product", "sales", "revenue"] 
                       if keyword in user_lower):
                    matching_models.append(model)
            
            if matching_models:
                response = f"I found **{len(matching_models)} models** related to your query:\n\n"
                for model in matching_models[:3]:
                    response += f"**{model['name']}**\n"
                    response += f"• Type: {model.get('materialization', 'Unknown')}\n"
                    response += f"• Description: {model.get('description', 'No description')}\n\n"
                response += "Would you like more details about any of these models?"
                return response
    
    # Handle help queries
    elif any(word in user_lower for word in ["help", "what", "how", "can you"]):
        return "I'm your dbt AI assistant! Here's what I can help you with:\n\n" + \
               "🔍 **Explore Models**: Ask about your models, search for specific ones\n" + \
               "📊 **Model Details**: Get information about columns, dependencies, descriptions\n" + \
               "🎯 **Generate Models**: Create new dbt models from natural language\n" + \
               "⚡ **Model Actions**: Help with compiling and running models\n" + \
               "💡 **Best Practices**: dbt modeling advice and suggestions\n\n" + \
               "Try asking:\n" + \
               "• 'How many models do I have?'\n" + \
               "• 'Show me customer-related models'\n" + \
               "• 'Create a model that calculates customer lifetime value'\n" + \
               "• 'Tell me about the dim_customers model'\n\n" + \
               "What would you like to know?"
    
    # Default response with context
    else:
        model_count = st.session_state.models_cache.get('total_count', 0) if st.session_state.models_cache else 0
        return f"I'm here to help with your dbt project! You have {model_count} models available.\n\n" + \
               "I can help you:\n" + \
               "• Explore and search your models\n" + \
               "• Generate new models with AI\n" + \
               "• Get details about specific models\n" + \
               "• Compile and run models\n\n" + \
               "What would you like to do? Try asking about your models or describe a new model you'd like to create!"

# Main header
st.markdown('<h1 class="main-header">🤖 dbt MCP Hackathon Project</h1>', unsafe_allow_html=True)
st.markdown("*Your AI-powered dbt companion for model exploration and generation*")

# Sidebar
with st.sidebar:
    st.title("🤖 Navigation")
    
    # Backend connection settings
    st.subheader("🔗 Backend Connection")
    new_url = st.text_input("Backend URL", value=st.session_state.backend_url)
    if new_url != st.session_state.backend_url:
        st.session_state.backend_url = new_url
        st.session_state.backend_connected = False
    
    # Connection status
    connected, status_info = check_backend_connection()
    if connected:
        st.success("✅ Backend Connected")
        if isinstance(status_info, dict):
            st.write(f"Models: {status_info.get('models_count', 0)}")
            st.write(f"Database: {'✅' if status_info.get('database_connected') else '❌'}")
    else:
        st.error(f"❌ Backend Disconnected: {status_info}")
    
    # Navigation
    st.subheader("📋 Navigation")
    page = st.selectbox(
        "Choose a page:",
        ["Model Explorer", "Chat Interface", "Model Generation", "AI Status"]
    )
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    if st.button("🔄 Refresh Models"):
        if connected:
            load_models()
            st.success("Models refreshed!")
        else:
            st.error("Backend not connected")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.success("Chat cleared!")

# Connection status banner
if connected:
    st.markdown('<div class="status-success">✅ Backend connected and ready</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status-error">❌ Backend not connected. Please check the backend URL and ensure the server is running.</div>', unsafe_allow_html=True)

# Main content based on selected page
if page == "Model Explorer":
    st.header("📊 Model Explorer")
    
    if not connected:
        st.warning("Please connect to the backend to explore models.")
    else:
        # Load models if not cached
        if st.session_state.models_cache is None:
            with st.spinner("Loading models..."):
                load_models()
        
        if st.session_state.models_cache:
            models_data = st.session_state.models_cache
            st.success(f"Found {models_data.get('total_count', 0)} models")
            
            # Search and filter
            col1, col2 = st.columns([2, 1])
            with col1:
                search_term = st.text_input("🔍 Search models", placeholder="Enter model name or description...")
            with col2:
                materialization_filter = st.selectbox(
                    "Filter by materialization",
                    ["All", "table", "view", "incremental", "ephemeral"]
                )
            
            # Filter models
            models = models_data.get('models', [])
            if search_term:
                models = [m for m in models if search_term.lower() in m.get('name', '').lower() 
                         or search_term.lower() in m.get('description', '').lower()]
            
            if materialization_filter != "All":
                models = [m for m in models if m.get('materialization') == materialization_filter]
            
            # Display models
            st.write(f"Showing {len(models)} models")
            
            for model in models[:20]:  # Limit to first 20 for performance
                with st.expander(f"📊 {model['name']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {model.get('description', 'No description')}")
                        st.write(f"**Materialization:** {model.get('materialization', 'Unknown')}")
                        st.write(f"**Path:** {model.get('path', 'Unknown')}")
                        if model.get('tags'):
                            st.write(f"**Tags:** {', '.join(model['tags'])}")
                        st.write(f"**Columns:** {len(model.get('columns', []))}")
                    
                    with col2:
                        st.write("**Actions:**")
                        if st.button(f"🔧 Compile", key=f"compile_{model['name']}"):
                            with st.spinner(f"Compiling {model['name']}..."):
                                result = compile_model(model['name'])
                                if result.get('success'):
                                    st.success("✅ Compilation successful!")
                                    if result.get('compiled_sql'):
                                        st.code(result['compiled_sql'], language='sql')
                                else:
                                    st.error(f"❌ Compilation failed: {result.get('error', 'Unknown error')}")
                        
                        if st.button(f"▶️ Run", key=f"run_{model['name']}"):
                            with st.spinner(f"Running {model['name']}..."):
                                result = run_model(model['name'])
                                if result.get('success'):
                                    st.success(f"✅ Model ran successfully! Rows affected: {result.get('rows_affected', 'Unknown')}")
                                else:
                                    st.error(f"❌ Run failed: {result.get('error', 'Unknown error')}")
                    
                    # Show columns
                    if model.get('columns'):
                        st.write("**Columns:**")
                        cols_df = pd.DataFrame(model['columns'])
                        st.dataframe(cols_df, use_container_width=True)

elif page == "Chat Interface":
    st.header("💬 Chat Interface")
    
    if not connected:
        st.warning("Please connect to the backend to use the chat interface.")
    else:
        # Display chat history
        for i, message in enumerate(st.session_state.chat_history):
            with st.container():
                if message['role'] == 'user':
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**Assistant:** {message['content']}")
        
        # Chat input
        user_input = st.text_area("Ask me anything about your dbt models:", height=100)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Send", type="primary"):
                if user_input:
                    # Add user message
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': user_input,
                        'timestamp': datetime.now()
                    })
                    
                    # Generate intelligent response using the backend
                    with st.spinner("Thinking..."):
                        response = generate_intelligent_response(user_input)
                    
                    # Add assistant response
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now()
                    })
                    
                    st.rerun()
        
        with col2:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()

elif page == "Model Generation":
    st.header("🎯 AI Model Generation")
    
    if not connected:
        st.warning("Please connect to the backend to generate models.")
    else:
        st.write("Generate new dbt models using natural language descriptions!")
        
        # Model generation form
        with st.form("model_generation"):
            prompt = st.text_area(
                "Describe the model you want to create:",
                height=100,
                placeholder="Example: Create a customer lifetime value model that calculates total revenue per customer from the orders table"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                materialization = st.selectbox(
                    "Materialization:",
                    ["view", "table", "incremental"]
                )
            
            with col2:
                model_name = st.text_input(
                    "Model name (optional):",
                    placeholder="Leave empty for auto-generation"
                )
            
            submitted = st.form_submit_button("🚀 Generate Model", type="primary")
            
            if submitted and prompt:
                with st.spinner("Generating model with AI... This may take a moment."):
                    result = generate_model(prompt, materialization)
                    
                    if result.get('success'):
                        st.success("✅ Model generated successfully!")
                        
                        # Display results
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.subheader("Generated SQL:")
                            st.code(result.get('sql', ''), language='sql')
                        
                        with col2:
                            st.subheader("Model Details:")
                            st.write(f"**Name:** {result.get('model_name', 'Unknown')}")
                            st.write(f"**Description:** {result.get('description', 'No description')}")
                            st.write(f"**Materialization:** {result.get('materialization', 'view')}")
                            st.write(f"**Confidence:** {result.get('confidence', 0):.2f}")
                            
                            if result.get('reasoning'):
                                st.write(f"**AI Reasoning:** {result.get('reasoning')}")
                        
                        # Warnings
                        if result.get('warnings'):
                            st.warning("⚠️ Warnings:")
                            for warning in result['warnings']:
                                st.write(f"- {warning}")
                    
                    else:
                        st.error(f"❌ Generation failed: {result.get('error', 'Unknown error')}")

elif page == "AI Status":
    st.header("🤖 AI Services Status")
    
    if not connected:
        st.warning("Please connect to the backend to check AI status.")
    else:
        ai_status = get_ai_status()
        
        if ai_status:
            st.success("✅ AI services information retrieved")
            
            # ChatGPT Status
            st.subheader("🧠 ChatGPT Service")
            chatgpt_info = ai_status.get('chatgpt', {})
            if chatgpt_info.get('available'):
                st.success(f"✅ Available - Model: {chatgpt_info.get('model', 'Unknown')}")
            else:
                st.error(f"❌ Not available - {chatgpt_info.get('status', 'Unknown status')}")
            
            # Pattern AI Status
            st.subheader("🔧 Pattern AI Service")
            pattern_info = ai_status.get('pattern_ai', {})
            if pattern_info.get('available'):
                st.success("✅ Available")
            else:
                st.warning("⚠️ Not available")
            
            # Recommended service
            st.subheader("💡 Recommended Service")
            recommended = ai_status.get('recommended', 'Unknown')
            st.info(f"Currently using: **{recommended}**")
            
            # Full status
            st.subheader("📊 Full Status")
            st.json(ai_status)
        else:
            st.error("❌ Could not retrieve AI status")

# Footer
st.markdown("---")
st.markdown("**dbt MCP Hackathon Project** - AI-powered dbt model exploration and generation")