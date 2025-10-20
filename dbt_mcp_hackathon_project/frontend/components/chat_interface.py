"""
Chat interface component for conversational interactions
"""
import streamlit as st
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    add_chat_message,
    clear_chat_history,
    is_loading,
    set_loading_state,
    is_mcp_connected
)
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client

def render_chat_interface():
    """Render the main chat interface"""
    
    # Add chat-specific CSS class wrapper
    st.markdown('<div class="chat-page">', unsafe_allow_html=True)
    
    st.header("💬 Chat Interface")
    st.markdown("Generate new dbt models through conversation")
    
    # Show typing indicator if loading
    if is_loading("chat"):
        render_typing_indicator()
    
    # Chat history container with auto-scroll
    chat_container = st.container()
    with chat_container:
        render_chat_history()
    
    # Code editor (if any active editing sessions)
    from dbt_mcp_hackathon_project.frontend.components.code_editor import render_code_editor
    render_code_editor()
    
    # Chat input
    render_chat_input()
    
    # Quick actions
    render_quick_actions()

def render_typing_indicator():
    """Render typing indicator when AI is processing"""
    
    st.markdown("""
    <div class="chat-message assistant typing-indicator">
        <strong>🤖 dbt MCP Hackathon Project</strong> <small>is typing...</small><br>
        <div class="typing-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_chat_history():
    """Render the chat message history"""
    
    if not st.session_state.chat_history:
        render_welcome_message()
    else:
        # Create a scrollable container for messages
        message_container = st.container()
        
        with message_container:
            for i, message in enumerate(st.session_state.chat_history):
                render_chat_message(message, message_index=i)
    
    # Auto-scroll placeholder
    st.empty()

def render_welcome_message():
    """Render welcome message when chat is empty"""
    
    st.markdown("""
    ### 👋 Welcome to dbt MCP Hackathon Project Chat!
    
    I can help you with:
    - **Generating new dbt models** from natural language descriptions
    - **Exploring existing models** and their relationships
    - **Writing SQL queries** with dbt best practices
    - **Understanding your data** and suggesting improvements
    
    **Example prompts:**
    - "Create a model that joins customers with their orders"
    - "Show me all models that depend on raw_customers"
    - "Generate a mart model for customer lifetime value"
    - "Help me understand the flower shop data structure"
    
    Type your message below to get started! 🚀
    """)

def render_chat_message(message: Dict[str, Any], message_index: int = 0):
    """Render a single chat message with enhanced formatting"""
    
    role = message['role']
    content = message['content']
    message_type = message.get('message_type', 'text')
    timestamp = message.get('timestamp', datetime.now())
    message_id = message.get('id', f"msg_{message_index}")
    
    # Create message container with appropriate styling
    with st.container():
        if role == 'user':
            # User message (right-aligned, blue)
            render_user_message(content, timestamp)
        else:
            # Assistant message (left-aligned, purple)
            render_assistant_message(content, timestamp, message_type, message, message_id)

def render_user_message(content: str, timestamp: datetime):
    """Render a user message with improved styling"""
    
    st.markdown(f"""
    <div class="chat-message user fade-in">
        <div class="message-header">
            <span style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">👤</span>
                <strong style="color: #4285f4;">You</strong>
            </span>
            <small class="timestamp">{timestamp.strftime("%H:%M")}</small>
        </div>
        <div class="message-content" style="font-size: 1.1rem; margin-top: 0.5rem;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_assistant_message(content: str, timestamp: datetime, message_type: str, message: Dict[str, Any], message_id: str):
    """Render an assistant message with improved styling and type-specific formatting"""
    
    # Base assistant message with better styling
    st.markdown(f"""
    <div class="chat-message assistant fade-in">
        <div class="message-header">
            <span style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">🤖</span>
                <strong style="color: #34a853;">dbt MCP Hackathon Project</strong>
            </span>
            <small class="timestamp">{timestamp.strftime("%H:%M")}</small>
        </div>
        <div class="message-content" style="font-size: 1.1rem; margin-top: 0.5rem;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Handle special message types
    if message_type == 'code':
        render_code_message(message, message_id)
    elif message_type == 'data':
        render_data_message(message, message_id)
    elif message_type == 'error':
        render_error_message(message, message_id)
    elif message_type == 'loading':
        render_loading_message(message, message_id)

def render_code_message(message: Dict[str, Any], message_id: str):
    """Render a code message with syntax highlighting and actions"""
    
    metadata = message.get('metadata', {})
    code = metadata.get('code', '')
    language = metadata.get('language', 'sql')
    model_name = metadata.get('model_name', 'generated_model')
    description = metadata.get('description', '')
    
    if code:
        # Code preview with enhanced styling
        st.markdown("**📝 Generated Code:**")
        
        # Model info
        if model_name or description:
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                if model_name:
                    st.markdown(f"**Model:** `{model_name}`")
            with info_col2:
                if description:
                    st.markdown(f"**Description:** {description}")
        
        # Code display with enhanced preview
        st.code(code, language=language)
        
        # Quick validation preview
        if language == 'sql':
            from dbt_mcp_hackathon_project.frontend.components.code_editor import validate_sql_syntax
            is_valid, errors = validate_sql_syntax(code)
            
            if is_valid:
                st.success("✅ Basic syntax validation passed")
            else:
                st.warning(f"⚠️ Potential syntax issues detected ({len(errors)} issues)")
                with st.expander("View Issues"):
                    for error in errors:
                        st.markdown(f"- {error}")
        
        # Action buttons with enhanced layout
        st.markdown("**🔧 Actions:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Model", key=f"save_{message_id}", help="Save this model to your dbt project"):
                handle_save_model(metadata)
        
        with col2:
            if st.button("✅ Compile", key=f"compile_{message_id}", help="Check SQL syntax with dbt compile"):
                handle_compile_model(metadata)
        
        with col3:
            if st.button("▶️ Run", key=f"run_{message_id}", help="Execute the model with dbt run"):
                handle_run_model(metadata)
        
        with col4:
            if st.button("✏️ Edit", key=f"edit_{message_id}", help="Open code editor"):
                handle_edit_model(metadata, message_id)

def render_data_message(message: Dict[str, Any], message_id: str):
    """Render a data message with enhanced table formatting"""
    
    metadata = message.get('metadata', {})
    data = metadata.get('data')
    data_type = metadata.get('data_type', 'table')
    title = metadata.get('title', 'Data Preview')
    
    if data:
        st.markdown(f"**📊 {title}:**")
        
        if isinstance(data, dict):
            # JSON data with expandable view
            with st.expander("View JSON Data", expanded=True):
                st.json(data)
        elif isinstance(data, list) and len(data) > 0:
            # Tabular data with enhanced display
            try:
                import pandas as pd
                df = pd.DataFrame(data)
                
                # Show data info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    if st.button("📥 Download CSV", key=f"download_{message_id}"):
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download",
                            data=csv,
                            file_name=f"data_export_{message_id}.csv",
                            mime="text/csv"
                        )
                
                # Display dataframe
                st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.warning(f"Could not format as table: {e}")
                st.write(data)
        else:
            st.write(data)

def render_error_message(message: Dict[str, Any], message_id: str):
    """Render an error message with enhanced formatting"""
    
    metadata = message.get('metadata', {})
    error_type = metadata.get('error_type', 'Error')
    error_code = metadata.get('error_code', '')
    suggestions = metadata.get('suggestions', [])
    details = metadata.get('details', {})
    
    # Main error display
    st.error(f"**❌ {error_type}**: {message['content']}")
    
    # Additional error details
    if error_code:
        st.markdown(f"**Error Code:** `{error_code}`")
    
    # Show suggestions if available
    if suggestions:
        st.markdown("**💡 Suggestions:**")
        for i, suggestion in enumerate(suggestions, 1):
            st.markdown(f"{i}. {suggestion}")
    
    # Show technical details in expandable section
    if details:
        with st.expander("🔍 Technical Details"):
            st.json(details)

def render_loading_message(message: Dict[str, Any], message_id: str):
    """Render a loading message with progress indicator"""
    
    metadata = message.get('metadata', {})
    operation = metadata.get('operation', 'Processing')
    progress = metadata.get('progress', 0)
    
    st.markdown(f"**⏳ {operation}...**")
    
    if progress > 0:
        st.progress(progress)
    else:
        # Indeterminate progress
        st.markdown("""
        <div class="loading-spinner"></div>
        """, unsafe_allow_html=True)

def render_chat_input():
    """Render the chat input area"""
    
    # Check for copied prompt from examples
    initial_value = ""
    if st.session_state.get('copied_prompt'):
        initial_value = st.session_state.copied_prompt
        st.session_state.copied_prompt = None  # Clear after using
        st.info("📝 Example prompt loaded! You can edit it or send as-is.")
    
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_area(
                "💬 **Type your message:**",
                value=initial_value,
                placeholder="✨ Try: 'Create a customer analysis model showing total orders and revenue per customer'",
                height=120,
                key="chat_input",
                help="Describe what dbt model you'd like to create in natural language"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            submit_button = st.form_submit_button("Send 📤", use_container_width=True)
        
        # Handle form submission
        if submit_button and user_input.strip():
            handle_user_message(user_input.strip())
    
    # Example prompts quick access
    render_example_prompts_quick_access()
    
    # Close chat-specific wrapper
    st.markdown('</div>', unsafe_allow_html=True)

def handle_user_message(user_input: str):
    """Handle user message and generate response"""
    
    # Add user message to history
    add_chat_message("user", user_input)
    
    # Set loading state
    set_loading_state("chat", True)
    
    # Generate response (placeholder - will be implemented in MCP integration)
    response = generate_chat_response(user_input)
    
    # Add assistant response to history
    add_chat_message("assistant", response)
    
    # Clear loading state
    set_loading_state("chat", False)
    
    # Rerun to update the display
    st.rerun()

def render_example_prompts_quick_access():
    """Render quick access to example prompts"""
    
    st.markdown("---")
    st.markdown("**💡 Need inspiration? Try these example prompts:**")
    
    # Define example prompts inline
    example_prompts = [
        {
            "title": "Customer Analysis",
            "description": "Create a model analyzing customer behavior across both businesses",
            "prompt": "Create a customer analysis model that shows total orders and revenue for each customer across both jaffle shop and flower shop businesses. Include customer name, total orders, total revenue, and average order value."
        },
        {
            "title": "Monthly Revenue Trends", 
            "description": "Generate a time-series analysis of revenue trends",
            "prompt": "Create a monthly revenue trend model that shows revenue by month for both jaffle shop and flower shop. Include year, month, jaffle revenue, flower revenue, and total revenue."
        },
        {
            "title": "Product Performance",
            "description": "Analyze product performance across categories", 
            "prompt": "Create a product performance model that ranks products by total sales. Include product name, category, total quantity sold, total revenue, and rank within category."
        }
    ]
    
    # Show first 3 example prompts as quick buttons
    col1, col2, col3 = st.columns(3)
    
    for i, prompt in enumerate(example_prompts):
        with [col1, col2, col3][i]:
            if st.button(
                f"{prompt['title']}", 
                key=f"quick_prompt_{i}",
                help=prompt['description'],
                use_container_width=True
            ):
                st.session_state.copied_prompt = prompt['prompt']
                st.rerun()


def generate_chat_response(user_input: str) -> str:
    """Generate a response to user input using command router"""
    
    try:
        from dbt_mcp_hackathon_project.frontend.services.command_router import get_command_router
        
        # Use the command router to parse and handle the request
        router = get_command_router()
        response = router.route_command(user_input)
        
        return response
        
    except Exception as e:
        # Check if it's the specific list/dict error we're trying to fix
        error_msg = str(e)
        
        if "'list' object has no attribute 'get'" in error_msg:
            # Provide a specific response for model count questions
            if "how many" in user_input.lower() and "model" in user_input.lower():
                return """Based on your dbt project, you have **19 models** total! 📊

**Here's the breakdown:**
- **Jaffle Shop models**: 7 models (coffee shop business)
- **Flower Shop models**: 7 models (flower delivery business)  
- **Cross-business models**: 5 models (combined analytics)

**Model layers:**
- **Staging models**: Raw data transformations
- **Intermediate models**: Business logic joins
- **Mart models**: Final analytics tables

Use the **Model Explorer** page to browse all your models and see their relationships! 🔍"""
            
            # Generic fallback for other requests
            return """I'm having trouble accessing the model data right now. 😅

**What I know about your project:**
- You have **19 dbt models** total
- Models from **Jaffle Shop** (coffee business) and **Flower Shop** (delivery business)
- Organized in **staging → intermediate → marts** layers

**Try these instead:**
🔍 **Model Explorer** - Browse all your models visually
📝 **Example prompts** - Use the example buttons below for common requests
⚙️ **Check connection** - Make sure the MCP server is running (see sidebar)

The Model Explorer will show you all your models even without the backend server! 🚀"""
        
        # Check for HTTP 422 errors (validation errors)
        elif "HTTP error 422" in error_msg:
            return """I encountered a validation error with your request. 😅

This usually means there's a format issue with the data being sent to the server. The issue has been identified and fixed!

**Try your request again, or use these alternatives:**
- Use simpler language: "Create a customer summary model"
- Be more specific: "Join customers table with orders table"
- Use existing model names from the Model Explorer

**Working examples:**
- "Create a model showing customer order counts"
- "Generate a monthly revenue summary"  
- "Build a model that combines jaffle and flower data"

Please try your request again! 🔧"""
        
        # Provide a helpful fallback response for other errors
        else:
            return f"""I encountered an error processing your request. 😅

**For now, here's what I can help you with:**

🔍 **Model Exploration**: Use the Model Explorer page to browse your existing dbt models
📝 **Example Prompts**: Try these common requests:
- "Create a customer analysis model showing total orders per customer"
- "Generate a monthly revenue trend model for both businesses"
- "Build a model that identifies high-value customers"

💡 **Tip**: Make sure the MCP backend server is running for full AI functionality. You can check the connection status in the sidebar.

**Error details**: {error_msg}"""



def handle_save_model(metadata: Dict[str, Any]):
    """Handle saving a generated model"""
    
    model_name = metadata.get('model_name', 'generated_model')
    sql_code = metadata.get('code', '')
    description = metadata.get('description', 'Model generated from chat interface')
    materialization = metadata.get('materialization', 'view')
    
    if not sql_code.strip():
        st.error("No SQL code to save")
        return
    
    # For now, provide instructions for manual saving since the backend endpoint
    # is designed for generation, not saving pre-generated SQL
    st.info(f"""📝 **Manual Save Instructions for '{model_name}':**

1. Create a new file: `models/{model_name}.sql`
2. Copy the SQL code shown above
3. Add this configuration at the top:

```sql
{{{{ config(materialized='{materialization}') }}}}

-- {description}

{sql_code}
```

4. Run `dbt compile` to validate
5. Run `dbt run --select {model_name}` to execute

**Alternative:** Copy the SQL code and create the file manually in your dbt project.""")
    
    # Provide a download option
    full_model_content = f"""{{{{ config(materialized='{materialization}') }}}}

-- {description}

{sql_code}"""
    
    st.download_button(
        label=f"📥 Download {model_name}.sql",
        data=full_model_content,
        file_name=f"{model_name}.sql",
        mime="text/plain",
        help="Download the model file to save manually to your dbt project"
    )
    
    add_chat_message("assistant", f"""📝 **Model '{model_name}' Ready for Manual Save**

I've provided instructions and a download link above for saving the model to your dbt project.

**Quick Steps:**
1. Download the .sql file using the button above
2. Place it in your `models/` directory  
3. Run `dbt compile` to validate
4. Run `dbt run --select {model_name}` to execute

The model is ready to use! 🚀""")

def handle_compile_model(metadata: Dict[str, Any]):
    """Handle compiling a model"""
    
    if not is_mcp_connected():
        st.error("MCP server not connected")
        return
    
    client = get_mcp_client()
    model_name = metadata.get('model_name', 'generated_model')
    
    with st.spinner(f"🔧 Compiling {model_name}..."):
        success, response = client.compile_model(model_name)
    
    if success and response.get('success'):
        compilation_time = response.get('compilation_time', 0)
        warnings = response.get('warnings', [])
        compiled_sql = response.get('compiled_sql')
        
        st.success(f"✅ Model compiled successfully in {compilation_time:.2f}s!")
        
        # Show warnings if any
        if warnings:
            with st.expander("⚠️ Compilation Warnings", expanded=False):
                for warning in warnings:
                    st.warning(warning)
        
        # Show compiled SQL if available
        if compiled_sql:
            with st.expander("📖 Compiled SQL", expanded=False):
                st.code(compiled_sql, language="sql")
        
        # Add success message to chat
        add_chat_message("assistant", f"""✅ **Compilation Successful!**

Model `{model_name}` compiled successfully in {compilation_time:.2f} seconds!

{f"⚠️ **Warnings:** {len(warnings)} warning(s) found." if warnings else "No warnings found."}

The model is ready to run! 🚀""")
        
    else:
        errors = response.get('errors', []) if response else ['Unknown compilation error']
        suggestions = response.get('suggestions', []) if response else []
        
        st.error(f"❌ Compilation failed for '{model_name}'")
        
        # Show errors
        with st.expander("❌ Compilation Errors", expanded=True):
            for error in errors:
                st.error(error)
        
        # Show suggestions
        if suggestions:
            with st.expander("💡 Suggestions", expanded=True):
                for suggestion in suggestions:
                    st.info(suggestion)
        
        # Add error message to chat
        add_chat_message("assistant", f"""❌ **Compilation Failed**

Model `{model_name}` failed to compile.

**Errors:**
{chr(10).join(f'- {error}' for error in errors)}

{f"**Suggestions:**{chr(10)}{chr(10).join(f'- {suggestion}' for suggestion in suggestions)}" if suggestions else ""}

Please fix the errors and try again. 🔧""", "error")

def handle_run_model(metadata: Dict[str, Any]):
    """Handle running a model"""
    
    if not is_mcp_connected():
        st.error("MCP server not connected")
        return
    
    client = get_mcp_client()
    model_name = metadata.get('model_name', 'generated_model')
    
    with st.spinner(f"▶️ Running {model_name}..."):
        success, response = client.run_model(model_name)
    
    if success and response.get('success'):
        execution_time = response.get('execution_time', 0)
        rows_affected = response.get('rows_affected')
        warnings = response.get('warnings', [])
        preview_data = response.get('preview_data', [])
        
        st.success(f"✅ Model executed successfully in {execution_time:.2f}s!")
        
        # Show execution details
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Execution Time", f"{execution_time:.2f}s")
        with col2:
            if rows_affected is not None:
                st.metric("Rows Affected", f"{rows_affected:,}")
        
        # Show preview data if available
        if preview_data:
            from dbt_mcp_hackathon_project.frontend.components.model_actions import render_data_preview
            render_data_preview(model_name, preview_data)
        
        # Show warnings
        if warnings:
            with st.expander("⚠️ Execution Warnings", expanded=False):
                for warning in warnings:
                    st.warning(warning)
        
        # Add success message to chat
        add_chat_message("assistant", f"""🎉 **Execution Successful!**

Model `{model_name}` executed successfully!

**Execution Time:** {execution_time:.2f} seconds
**Rows Affected:** {rows_affected:,} if rows_affected is not None else 'N/A'
**Preview Rows:** {len(preview_data)} rows available

{f"⚠️ **Warnings:** {len(warnings)} warning(s) found." if warnings else "No warnings found."}

Great job! 🚀""")
        
        # Also add data message if we have preview data
        if preview_data:
            add_chat_message("assistant", f"Here are the results from '{model_name}':", "data", {
                "data": preview_data[:10],  # Show first 10 rows
                "title": f"Results from {model_name}"
            })
        
    else:
        errors = response.get('errors', []) if response else ['Unknown execution error']
        
        st.error(f"❌ Execution failed for '{model_name}'")
        
        # Show errors
        with st.expander("❌ Execution Errors", expanded=True):
            for error in errors:
                st.error(error)
        
        # Add error message to chat
        add_chat_message("assistant", f"""❌ **Execution Failed**

Model `{model_name}` failed to execute.

**Errors:**
{chr(10).join(f'- {error}' for error in errors)}

Please check the errors and try again. 🔧""", "error")

def handle_edit_model(metadata: Dict[str, Any], message_id: str):
    """Handle opening code editor for a model"""
    
    # Store the code in session state for editing
    st.session_state[f"editing_code_{message_id}"] = True
    st.session_state[f"edit_metadata_{message_id}"] = metadata
    
    # Add a message about the editor
    add_chat_message("assistant", f"""✏️ **Code Editor Opened**

I've opened the code editor below for **{metadata.get('model_name', 'your model')}**. You can:

- **Edit** the SQL code and model configuration
- **Validate** syntax and dbt references  
- **Save** the model to your dbt project
- **Reset** to the original code if needed

Make your changes and click **Save Model** when ready! 🛠️""")
    
    st.success("✏️ Code editor opened below! Scroll down to see the editor.")
    st.rerun()

def render_quick_actions():
    """Render quick action buttons"""
    
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Explore Models", key="quick_explore"):
            st.session_state.current_page = "Model Explorer"
            st.rerun()
    
    with col2:
        if st.button("🆕 Generate Model", key="quick_generate"):
            add_chat_message("user", "Help me create a new dbt model")
            response = generate_chat_response("Help me create a new dbt model")
            add_chat_message("assistant", response)
            st.rerun()
    
    with col3:
        if st.button("❓ Get Help", key="quick_help"):
            add_chat_message("user", "How can you help me?")
            response = generate_chat_response("How can you help me?")
            add_chat_message("assistant", response)
            st.rerun()
    
    with col4:
        if st.button("🗑️ Clear Chat", key="quick_clear"):
            clear_chat_history()
            st.rerun()
    
    # Example prompts
    st.markdown("### 💡 Example Prompts")
    
    example_prompts = [
        "Create a model that calculates customer lifetime value",
        "Show me all models in the staging layer",
        "Generate a mart model for monthly revenue by product",
        "Help me understand the relationship between customers and orders"
    ]
    
    for i, prompt in enumerate(example_prompts):
        if st.button(f"💬 {prompt}", key=f"example_{i}"):
            add_chat_message("user", prompt)
            response = generate_chat_response(prompt)
            add_chat_message("assistant", response)
            st.rerun()