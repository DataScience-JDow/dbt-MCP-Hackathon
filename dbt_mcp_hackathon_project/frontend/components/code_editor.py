"""
Code editor component with syntax highlighting and validation
"""
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    add_chat_message,
    is_mcp_connected
)
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client

def render_code_editor():
    """Render code editor interface for active editing sessions"""
    
    # Check for active editing sessions
    active_editors = []
    for key in st.session_state.keys():
        if key.startswith("editing_code_") and st.session_state.get(key, False):
            message_id = key.replace("editing_code_", "")
            metadata_key = f"edit_metadata_{message_id}"
            if metadata_key in st.session_state:
                active_editors.append((message_id, st.session_state[metadata_key]))
    
    if not active_editors:
        return
    
    st.markdown("---")
    st.header("✏️ Code Editor")
    
    # Render each active editor
    for message_id, metadata in active_editors:
        render_single_code_editor(message_id, metadata)

def render_single_code_editor(message_id: str, metadata: Dict[str, Any]):
    """Render a single code editor instance"""
    
    model_name = metadata.get('model_name', 'generated_model')
    original_code = metadata.get('code', '')
    language = metadata.get('language', 'sql')
    description = metadata.get('description', '')
    materialization = metadata.get('materialization', 'view')
    
    # Editor container
    with st.container():
        st.subheader(f"📝 Editing: {model_name}")
        
        # Model configuration
        col1, col2, col3 = st.columns(3)
        
        with col1:
            edited_name = st.text_input(
                "Model Name",
                value=model_name,
                key=f"edit_name_{message_id}",
                help="Name for the dbt model file"
            )
        
        with col2:
            edited_materialization = st.selectbox(
                "Materialization",
                options=["view", "table", "incremental", "ephemeral"],
                index=["view", "table", "incremental", "ephemeral"].index(materialization),
                key=f"edit_mat_{message_id}",
                help="How the model should be materialized in the database"
            )
        
        with col3:
            layer = st.selectbox(
                "Layer",
                options=["staging", "intermediate", "marts", "other"],
                index=0,
                key=f"edit_layer_{message_id}",
                help="Which layer this model belongs to"
            )
        
        # Description
        edited_description = st.text_area(
            "Description",
            value=description,
            height=60,
            key=f"edit_desc_{message_id}",
            help="Description for the model documentation"
        )
        
        # Code editor
        st.markdown("**SQL Code:**")
        edited_code = st.text_area(
            "SQL Code",
            value=original_code,
            height=400,
            key=f"edit_code_{message_id}",
            help="SQL code for the model"
        )
        
        # Syntax highlighting preview
        if edited_code.strip():
            with st.expander("📖 Code Preview", expanded=False):
                st.code(edited_code, language=language)
        
        # Validation and actions
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            if st.button("✅ Validate", key=f"validate_{message_id}", help="Check SQL syntax"):
                handle_code_validation(edited_code, edited_name, message_id)
        
        with col2:
            if st.button("🔧 Compile", key=f"compile_{message_id}", help="Compile with dbt"):
                handle_compile_model(edited_name, edited_code, message_id)
        
        with col3:
            if st.button("▶️ Run", key=f"run_{message_id}", help="Execute model"):
                handle_run_model(edited_name, message_id)
        
        with col4:
            if st.button("💾 Save", key=f"save_edited_{message_id}", help="Save to dbt project"):
                handle_save_edited_model(
                    edited_name, edited_code, edited_description, 
                    edited_materialization, layer, message_id
                )
        
        with col5:
            if st.button("🔄 Reset", key=f"reset_{message_id}", help="Reset to original code"):
                handle_reset_code(message_id, original_code)
        
        with col6:
            if st.button("❌ Cancel", key=f"cancel_{message_id}", help="Close editor"):
                handle_cancel_edit(message_id)
        
        with col7:
            if st.button("📋 Copy", key=f"copy_{message_id}", help="Copy code to clipboard"):
                handle_copy_code(edited_code, message_id)
        
        # Show validation results
        validation_key = f"validation_result_{message_id}"
        if validation_key in st.session_state:
            render_validation_results(st.session_state[validation_key])
        
        st.markdown("---")

def handle_code_validation(code: str, model_name: str, message_id: str):
    """Validate SQL code syntax and dbt references"""
    
    if not code.strip():
        st.error("❌ Code cannot be empty")
        return
    
    if not is_mcp_connected():
        st.error("❌ MCP server not connected - cannot validate")
        return
    
    # Basic SQL syntax checks
    validation_results = {
        "syntax_errors": [],
        "warnings": [],
        "suggestions": [],
        "is_valid": True
    }
    
    # Check for basic SQL syntax issues
    code_lower = code.lower().strip()
    
    # Check for SELECT statement
    if not code_lower.startswith('select') and 'select' not in code_lower:
        validation_results["syntax_errors"].append("Model should contain a SELECT statement")
        validation_results["is_valid"] = False
    
    # Check for proper dbt references
    import re
    
    # Check for raw table references (should use source() or ref())
    raw_table_pattern = r'\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)\b'
    raw_tables = re.findall(raw_table_pattern, code_lower)
    
    for table in raw_tables:
        if not table.startswith(('ref(', 'source(')):
            if table.startswith('raw_'):
                validation_results["warnings"].append(
                    f"Consider using {{{{ source('schema', '{table}') }}}} instead of raw table '{table}'"
                )
            else:
                validation_results["suggestions"].append(
                    f"Consider using {{{{ ref('{table}') }}}} if '{table}' is a dbt model"
                )
    
    # Check for missing commas
    lines = code.split('\n')
    for i, line in enumerate(lines[:-1], 1):
        line_stripped = line.strip()
        if (line_stripped and 
            not line_stripped.endswith(',') and 
            not line_stripped.endswith('(') and
            not line_stripped.lower().startswith(('select', 'from', 'where', 'group', 'order', 'having', 'limit'))):
            next_line = lines[i].strip() if i < len(lines) else ""
            if (next_line and 
                not next_line.lower().startswith(('from', 'where', 'group', 'order', 'having', 'limit', ')'))):
                validation_results["warnings"].append(f"Line {i} might be missing a comma")
    
    # Use MCP server for advanced validation
    try:
        client = get_mcp_client()
        success, response = client.compile_model(model_name, code)
        
        if success:
            if response.get('compiled'):
                validation_results["suggestions"].append("✅ Model compiles successfully with dbt")
            else:
                compilation_errors = response.get('errors', [])
                for error in compilation_errors:
                    validation_results["syntax_errors"].append(f"dbt compilation error: {error}")
                    validation_results["is_valid"] = False
        else:
            validation_results["warnings"].append("Could not validate with dbt compiler")
    
    except Exception as e:
        validation_results["warnings"].append(f"Validation service error: {str(e)}")
    
    # Store validation results
    st.session_state[f"validation_result_{message_id}"] = validation_results
    
    # Show immediate feedback
    if validation_results["is_valid"]:
        st.success("✅ Code validation passed!")
    else:
        st.error("❌ Code validation failed - see details below")
    
    st.rerun()

def render_validation_results(results: Dict[str, Any]):
    """Render validation results with appropriate styling"""
    
    if results.get("syntax_errors"):
        st.error("**❌ Syntax Errors:**")
        for error in results["syntax_errors"]:
            st.markdown(f"- {error}")
    
    if results.get("warnings"):
        st.warning("**⚠️ Warnings:**")
        for warning in results["warnings"]:
            st.markdown(f"- {warning}")
    
    if results.get("suggestions"):
        st.info("**💡 Suggestions:**")
        for suggestion in results["suggestions"]:
            st.markdown(f"- {suggestion}")
    
    if results.get("is_valid") and not results.get("syntax_errors"):
        st.success("**✅ Validation Summary:** Code looks good!")

def handle_save_edited_model(name: str, code: str, description: str, materialization: str, layer: str, message_id: str):
    """Save the edited model to dbt project"""
    
    if not code.strip():
        st.error("❌ Cannot save empty model")
        return
    
    if not name.strip():
        st.error("❌ Model name is required")
        return
    
    if not is_mcp_connected():
        st.error("❌ MCP server not connected")
        return
    
    # Clean model name
    clean_name = name.strip().lower().replace(' ', '_')
    if not clean_name.endswith('.sql'):
        clean_name += '.sql'
    
    # Build model specification
    model_spec = {
        "name": clean_name.replace('.sql', ''),
        "sql": code,
        "description": description,
        "materialization": materialization,
        "layer": layer
    }
    
    client = get_mcp_client()
    success, response = client.create_model(model_spec)
    
    if success:
        st.success(f"✅ Model '{clean_name}' saved successfully!")
        
        # Add success message to chat
        add_chat_message("assistant", f"""🎉 **Model Saved Successfully!**

**Model:** `{clean_name}`
**Materialization:** {materialization}
**Layer:** {layer}
**Description:** {description}

The model has been saved to your dbt project and is ready to compile and run! 🚀""")
        
        # Close the editor
        handle_cancel_edit(message_id)
        
    else:
        error_msg = response.get('message', 'Unknown error') if response else 'No response from server'
        st.error(f"❌ Failed to save model: {error_msg}")
        
        # Add error message to chat
        add_chat_message("assistant", f"Sorry, I couldn't save the model: {error_msg} 😅", "error", {
            "error_type": "Save Error",
            "error_code": response.get('error_code', 'SAVE_FAILED') if response else 'CONNECTION_ERROR',
            "suggestions": [
                "Check if the MCP server is running",
                "Verify the model name is valid",
                "Ensure the SQL syntax is correct"
            ]
        })

def handle_reset_code(message_id: str, original_code: str):
    """Reset code to original version"""
    
    # Reset the code in session state
    st.session_state[f"edit_code_{message_id}"] = original_code
    
    # Clear validation results
    validation_key = f"validation_result_{message_id}"
    if validation_key in st.session_state:
        del st.session_state[validation_key]
    
    st.success("🔄 Code reset to original version")
    st.rerun()

def handle_cancel_edit(message_id: str):
    """Cancel editing and close editor"""
    
    # Remove editing flags
    edit_key = f"editing_code_{message_id}"
    metadata_key = f"edit_metadata_{message_id}"
    validation_key = f"validation_result_{message_id}"
    
    if edit_key in st.session_state:
        del st.session_state[edit_key]
    if metadata_key in st.session_state:
        del st.session_state[metadata_key]
    if validation_key in st.session_state:
        del st.session_state[validation_key]
    
    # Clear editor form fields
    for field in ['edit_name_', 'edit_mat_', 'edit_layer_', 'edit_desc_', 'edit_code_']:
        field_key = f"{field}{message_id}"
        if field_key in st.session_state:
            del st.session_state[field_key]
    
    st.success("❌ Editor closed")
    st.rerun()

def handle_compile_model(model_name: str, code: str, message_id: str):
    """Handle model compilation"""
    
    if not code.strip():
        st.error("❌ Cannot compile empty model")
        return
    
    if not model_name.strip():
        st.error("❌ Model name is required for compilation")
        return
    
    if not is_mcp_connected():
        st.error("❌ MCP server not connected")
        return
    
    # Clean model name
    clean_name = model_name.strip().lower().replace(' ', '_')
    if clean_name.endswith('.sql'):
        clean_name = clean_name[:-4]
    
    with st.spinner(f"🔧 Compiling model '{clean_name}'..."):
        client = get_mcp_client()
        success, response = client.compile_model(clean_name)
        
        if success:
            compilation_result = response
            
            if compilation_result.get('success'):
                st.success(f"✅ Model '{clean_name}' compiled successfully!")
                
                # Show compilation details
                compilation_time = compilation_result.get('compilation_time')
                if compilation_time:
                    st.info(f"⏱️ Compilation time: {compilation_time:.2f} seconds")
                
                # Show compiled SQL if available
                compiled_sql = compilation_result.get('compiled_sql')
                if compiled_sql:
                    with st.expander("📖 Compiled SQL", expanded=False):
                        st.code(compiled_sql, language="sql")
                
                # Show warnings if any
                warnings = compilation_result.get('warnings', [])
                if warnings:
                    st.warning("⚠️ **Compilation Warnings:**")
                    for warning in warnings:
                        st.markdown(f"- {warning}")
                
                # Add success message to chat
                add_chat_message("assistant", f"""✅ **Compilation Successful!**

**Model:** `{clean_name}`
**Compilation Time:** {compilation_time:.2f}s if compilation_time else 'N/A'

The model compiled successfully and is ready to run! 🚀""")
                
            else:
                # Compilation failed
                errors = compilation_result.get('errors', [])
                suggestions = compilation_result.get('suggestions', [])
                
                st.error(f"❌ Model '{clean_name}' compilation failed")
                
                if errors:
                    st.error("**Compilation Errors:**")
                    for error in errors:
                        st.markdown(f"- {error}")
                
                if suggestions:
                    st.info("**💡 Suggestions:**")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")
                
                # Add error message to chat
                add_chat_message("assistant", f"""❌ **Compilation Failed**

**Model:** `{clean_name}`

**Errors:**
{chr(10).join(f'- {error}' for error in errors)}

{f"**Suggestions:**{chr(10)}{chr(10).join(f'- {suggestion}' for suggestion in suggestions)}" if suggestions else ""}

Please fix the errors and try again. 🔧""", "error")
        
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response from server'
            st.error(f"❌ Compilation request failed: {error_msg}")

def handle_run_model(model_name: str, message_id: str):
    """Handle model execution"""
    
    if not model_name.strip():
        st.error("❌ Model name is required for execution")
        return
    
    if not is_mcp_connected():
        st.error("❌ MCP server not connected")
        return
    
    # Clean model name
    clean_name = model_name.strip().lower().replace(' ', '_')
    if clean_name.endswith('.sql'):
        clean_name = clean_name[:-4]
    
    # Ask user about dependencies
    with_deps = st.checkbox(
        "Run with dependencies", 
        key=f"run_deps_{message_id}",
        help="Also run upstream models that this model depends on"
    )
    
    with st.spinner(f"▶️ Running model '{clean_name}'..."):
        client = get_mcp_client()
        success, response = client.run_model(clean_name, with_dependencies=with_deps)
        
        if success:
            execution_result = response
            
            if execution_result.get('success'):
                st.success(f"✅ Model '{clean_name}' executed successfully!")
                
                # Show execution details
                execution_time = execution_result.get('execution_time')
                rows_affected = execution_result.get('rows_affected')
                
                if execution_time:
                    st.info(f"⏱️ Execution time: {execution_time:.2f} seconds")
                
                if rows_affected is not None:
                    st.info(f"📊 Rows affected: {rows_affected:,}")
                
                # Show preview data if available
                preview_data = execution_result.get('preview_data')
                if preview_data:
                    render_execution_results(clean_name, preview_data)
                
                # Show warnings if any
                warnings = execution_result.get('warnings', [])
                if warnings:
                    st.warning("⚠️ **Execution Warnings:**")
                    for warning in warnings:
                        st.markdown(f"- {warning}")
                
                # Add success message to chat
                add_chat_message("assistant", f"""🎉 **Execution Successful!**

**Model:** `{clean_name}`
**Execution Time:** {execution_time:.2f}s if execution_time else 'N/A'
**Rows Affected:** {rows_affected:,} if rows_affected is not None else 'N/A'

The model has been executed successfully! 🚀""")
                
            else:
                # Execution failed
                errors = execution_result.get('errors', [])
                
                st.error(f"❌ Model '{clean_name}' execution failed")
                
                if errors:
                    st.error("**Execution Errors:**")
                    for error in errors:
                        st.markdown(f"- {error}")
                
                # Add error message to chat
                add_chat_message("assistant", f"""❌ **Execution Failed**

**Model:** `{clean_name}`

**Errors:**
{chr(10).join(f'- {error}' for error in errors)}

Please check the errors and try again. 🔧""", "error")
        
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response from server'
            st.error(f"❌ Execution request failed: {error_msg}")

def render_execution_results(model_name: str, preview_data: List[Dict[str, Any]]):
    """Render execution results with data preview"""
    
    if not preview_data:
        st.info("No preview data available")
        return
    
    st.markdown("### 📊 Execution Results")
    
    # Show data preview
    with st.expander(f"📋 Data Preview ({len(preview_data)} rows)", expanded=True):
        # Convert to DataFrame for better display
        import pandas as pd
        
        try:
            df = pd.DataFrame(preview_data)
            st.dataframe(df, use_container_width=True)
            
            # Show basic statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Rows", len(df))
            
            with col2:
                st.metric("Columns", len(df.columns))
            
            with col3:
                # Show data types
                numeric_cols = len(df.select_dtypes(include=['number']).columns)
                st.metric("Numeric Columns", numeric_cols)
            
            # Show column info
            with st.expander("📋 Column Information", expanded=False):
                col_info = []
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    null_count = df[col].isnull().sum()
                    col_info.append({
                        "Column": col,
                        "Type": dtype,
                        "Null Count": null_count,
                        "Sample Value": str(df[col].iloc[0]) if len(df) > 0 else "N/A"
                    })
                
                col_df = pd.DataFrame(col_info)
                st.dataframe(col_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error displaying results: {e}")
            st.json(preview_data[:5])  # Show first 5 rows as JSON fallback

def handle_copy_code(code: str, message_id: str):
    """Handle copying code to clipboard"""
    
    # Since Streamlit doesn't have direct clipboard access, 
    # we'll show the code in a format that's easy to copy
    st.success("📋 Code ready to copy!")
    
    with st.expander("📋 Copy this code:", expanded=True):
        st.code(code, language="sql")
        st.markdown("*Select all text above and copy with Ctrl+C (Cmd+C on Mac)*")

def render_code_preview_component(code: str, language: str = "sql", title: str = "Code Preview"):
    """Render a standalone code preview component"""
    
    with st.container():
        st.markdown(f"**{title}:**")
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["📖 Formatted", "📝 Raw"])
        
        with tab1:
            st.code(code, language=language)
        
        with tab2:
            st.text_area(
                "Raw Code",
                value=code,
                height=200,
                disabled=True,
                key=f"preview_{hash(code)}"
            )

def get_syntax_highlighting_languages():
    """Get list of supported syntax highlighting languages"""
    
    return [
        "sql", "python", "yaml", "json", "markdown", 
        "bash", "dockerfile", "toml", "ini"
    ]

def validate_sql_syntax(sql_code: str) -> Tuple[bool, List[str]]:
    """Basic SQL syntax validation"""
    
    errors = []
    
    if not sql_code.strip():
        errors.append("SQL code cannot be empty")
        return False, errors
    
    # Basic checks
    sql_lower = sql_code.lower().strip()
    
    # Check for SELECT
    if not sql_lower.startswith('select') and 'select' not in sql_lower:
        errors.append("SQL should contain a SELECT statement")
    
    # Check for balanced parentheses
    open_parens = sql_code.count('(')
    close_parens = sql_code.count(')')
    if open_parens != close_parens:
        errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
    
    # Check for balanced quotes
    single_quotes = sql_code.count("'")
    if single_quotes % 2 != 0:
        errors.append("Unbalanced single quotes")
    
    double_quotes = sql_code.count('"')
    if double_quotes % 2 != 0:
        errors.append("Unbalanced double quotes")
    
    return len(errors) == 0, errors