"""
Model action components for compilation and execution
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    add_chat_message,
    is_mcp_connected
)
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client

def render_model_action_buttons(model_name: str, show_compile: bool = True, show_run: bool = True, show_results: bool = True):
    """Render action buttons for a model"""
    
    if not is_mcp_connected():
        st.warning("⚠️ MCP server not connected - actions unavailable")
        return
    
    # Clean model name
    clean_name = model_name.strip().lower().replace(' ', '_')
    if clean_name.endswith('.sql'):
        clean_name = clean_name[:-4]
    
    # Create columns for buttons
    cols = []
    if show_compile:
        cols.append("compile")
    if show_run:
        cols.append("run")
    if show_results:
        cols.append("results")
    
    if not cols:
        return
    
    button_cols = st.columns(len(cols))
    
    # Compile button
    if show_compile and "compile" in cols:
        col_idx = cols.index("compile")
        with button_cols[col_idx]:
            if st.button(f"🔧 Compile", key=f"compile_action_{clean_name}", help="Compile model with dbt"):
                handle_model_compile_action(clean_name)
    
    # Run button
    if show_run and "run" in cols:
        col_idx = cols.index("run")
        with button_cols[col_idx]:
            if st.button(f"▶️ Run", key=f"run_action_{clean_name}", help="Execute model"):
                handle_model_run_action(clean_name)
    
    # Results button
    if show_results and "results" in cols:
        col_idx = cols.index("results")
        with button_cols[col_idx]:
            if st.button(f"📊 Results", key=f"results_action_{clean_name}", help="View execution results"):
                handle_model_results_action(clean_name)

def handle_model_compile_action(model_name: str):
    """Handle model compilation action"""
    
    with st.spinner(f"🔧 Compiling {model_name}..."):
        client = get_mcp_client()
        success, response = client.compile_model(model_name)
        
        if success and response.get('success'):
            compilation_time = response.get('compilation_time', 0)
            warnings = response.get('warnings', [])
            
            # Show success message
            st.success(f"✅ Model '{model_name}' compiled successfully in {compilation_time:.2f}s!")
            
            # Show warnings if any
            if warnings:
                with st.expander("⚠️ Compilation Warnings", expanded=False):
                    for warning in warnings:
                        st.warning(warning)
            
            # Show compiled SQL if available
            compiled_sql = response.get('compiled_sql')
            if compiled_sql:
                with st.expander("📖 Compiled SQL", expanded=False):
                    st.code(compiled_sql, language="sql")
            
            # Add to chat
            add_chat_message("assistant", f"""✅ **Compilation Successful!**

Model `{model_name}` compiled successfully in {compilation_time:.2f} seconds.

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
            
            # Add to chat
            add_chat_message("assistant", f"""❌ **Compilation Failed**

Model `{model_name}` failed to compile.

**Errors:**
{chr(10).join(f'- {error}' for error in errors)}

{f"**Suggestions:**{chr(10)}{chr(10).join(f'- {suggestion}' for suggestion in suggestions)}" if suggestions else ""}

Please fix the errors and try again. 🔧""", "error")

def handle_model_run_action(model_name: str):
    """Handle model execution action"""
    
    # Options for execution
    col1, col2 = st.columns(2)
    
    with col1:
        with_deps = st.checkbox(
            "Include dependencies", 
            key=f"run_deps_action_{model_name}",
            help="Also run upstream models"
        )
    
    with col2:
        if st.button("Execute Now", key=f"execute_now_{model_name}"):
            _execute_model(model_name, with_deps)

def _execute_model(model_name: str, with_dependencies: bool = False):
    """Execute the model"""
    
    with st.spinner(f"▶️ Running {model_name}..."):
        client = get_mcp_client()
        success, response = client.run_model(model_name, with_dependencies)
        
        if success and response.get('success'):
            execution_time = response.get('execution_time', 0)
            rows_affected = response.get('rows_affected')
            warnings = response.get('warnings', [])
            preview_data = response.get('preview_data', [])
            
            # Show success message
            st.success(f"✅ Model '{model_name}' executed successfully in {execution_time:.2f}s!")
            
            # Show execution details
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Execution Time", f"{execution_time:.2f}s")
            with col2:
                if rows_affected is not None:
                    st.metric("Rows Affected", f"{rows_affected:,}")
            
            # Show preview data
            if preview_data:
                render_data_preview(model_name, preview_data)
            
            # Show warnings
            if warnings:
                with st.expander("⚠️ Execution Warnings", expanded=False):
                    for warning in warnings:
                        st.warning(warning)
            
            # Add to chat
            add_chat_message("assistant", f"""🎉 **Execution Successful!**

Model `{model_name}` executed successfully!

**Execution Time:** {execution_time:.2f} seconds
**Rows Affected:** {rows_affected:,} if rows_affected is not None else 'N/A'
**Preview Rows:** {len(preview_data)} rows available

{f"⚠️ **Warnings:** {len(warnings)} warning(s) found." if warnings else "No warnings found."}

Great job! 🚀""")
            
        else:
            errors = response.get('errors', []) if response else ['Unknown execution error']
            
            st.error(f"❌ Execution failed for '{model_name}'")
            
            # Show errors
            with st.expander("❌ Execution Errors", expanded=True):
                for error in errors:
                    st.error(error)
            
            # Add to chat
            add_chat_message("assistant", f"""❌ **Execution Failed**

Model `{model_name}` failed to execute.

**Errors:**
{chr(10).join(f'- {error}' for error in errors)}

Please check the errors and try again. 🔧""", "error")

def handle_model_results_action(model_name: str):
    """Handle viewing model results"""
    
    # Options for results
    col1, col2 = st.columns(2)
    
    with col1:
        limit = st.number_input(
            "Row limit", 
            min_value=10, 
            max_value=1000, 
            value=100,
            key=f"results_limit_{model_name}"
        )
    
    with col2:
        if st.button("Load Results", key=f"load_results_{model_name}"):
            _load_model_results(model_name, limit)

def _load_model_results(model_name: str, limit: int):
    """Load and display model results"""
    
    with st.spinner(f"📊 Loading results for {model_name}..."):
        client = get_mcp_client()
        success, response = client.get_model_results(model_name, limit)
        
        if success:
            data = response.get('data', [])
            row_count = response.get('row_count', 0)
            columns = response.get('columns', [])
            
            if data:
                st.success(f"✅ Loaded {row_count} rows from '{model_name}'")
                render_data_preview(model_name, data, show_title=False)
                
                # Add to chat
                add_chat_message("assistant", f"""📊 **Results Loaded**

Successfully loaded {row_count} rows from model `{model_name}`.

**Columns:** {len(columns)}
**Sample data is displayed above.**

The model results are ready for analysis! 📈""")
                
            else:
                st.warning(f"No data found for model '{model_name}'")
                add_chat_message("assistant", f"No data found for model `{model_name}`. The model may not have been executed yet. 🤔")
        
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response from server'
            st.error(f"❌ Failed to load results: {error_msg}")

def render_data_preview(model_name: str, data: List[Dict[str, Any]], show_title: bool = True):
    """Render data preview with statistics"""
    
    if not data:
        st.info("No data to display")
        return
    
    if show_title:
        st.markdown(f"### 📊 Results: {model_name}")
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Show basic info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Rows", len(df))
        
        with col2:
            st.metric("Columns", len(df.columns))
        
        with col3:
            numeric_cols = len(df.select_dtypes(include=['number']).columns)
            st.metric("Numeric Columns", numeric_cols)
        
        # Show data table
        st.dataframe(df, use_container_width=True, height=400)
        
        # Show column details
        with st.expander("📋 Column Details", expanded=False):
            col_details = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_count = df[col].isnull().sum()
                unique_count = df[col].nunique()
                
                col_details.append({
                    "Column": col,
                    "Type": dtype,
                    "Null Count": null_count,
                    "Unique Values": unique_count,
                    "Sample": str(df[col].iloc[0]) if len(df) > 0 else "N/A"
                })
            
            details_df = pd.DataFrame(col_details)
            st.dataframe(details_df, use_container_width=True)
        
        # Show basic statistics for numeric columns
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            with st.expander("📈 Numeric Statistics", expanded=False):
                st.dataframe(numeric_df.describe(), use_container_width=True)
    
    except Exception as e:
        st.error(f"Error displaying data: {e}")
        # Fallback to JSON display
        with st.expander("Raw Data (JSON)", expanded=False):
            st.json(data[:10])  # Show first 10 rows

def render_compile_and_run_component(model_name: str):
    """Render a combined compile and run component"""
    
    if not is_mcp_connected():
        st.warning("⚠️ MCP server not connected")
        return
    
    st.markdown(f"### 🔧 Compile & Run: {model_name}")
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        with_deps = st.checkbox(
            "Include dependencies", 
            key=f"compile_run_deps_{model_name}",
            help="Also run upstream models"
        )
    
    with col2:
        show_results = st.checkbox(
            "Show results after execution", 
            value=True,
            key=f"compile_run_results_{model_name}",
            help="Display data preview after successful execution"
        )
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 Compile Only", key=f"compile_only_{model_name}"):
            handle_model_compile_action(model_name)
    
    with col2:
        if st.button("▶️ Run Only", key=f"run_only_{model_name}"):
            _execute_model(model_name, with_deps)
    
    with col3:
        if st.button("🚀 Compile & Run", key=f"compile_and_run_{model_name}"):
            handle_compile_and_run_action(model_name, with_deps, show_results)

def handle_compile_and_run_action(model_name: str, with_dependencies: bool = False, show_results: bool = True):
    """Handle combined compile and run action"""
    
    with st.spinner(f"🚀 Compiling and running {model_name}..."):
        client = get_mcp_client()
        success, response = client.compile_and_run_model(model_name)
        
        if success:
            compilation = response.get('compilation', {})
            execution = response.get('execution')
            
            # Show compilation results
            if compilation.get('success'):
                comp_time = compilation.get('compilation_time', 0)
                st.success(f"✅ Compilation successful in {comp_time:.2f}s")
                
                # Show execution results if available
                if execution:
                    if execution.get('success'):
                        exec_time = execution.get('execution_time', 0)
                        rows_affected = execution.get('rows_affected')
                        
                        st.success(f"✅ Execution successful in {exec_time:.2f}s")
                        
                        if rows_affected is not None:
                            st.info(f"📊 Rows affected: {rows_affected:,}")
                        
                        # Show results if requested
                        if show_results:
                            preview_data = execution.get('preview_data', [])
                            if preview_data:
                                render_data_preview(model_name, preview_data)
                        
                        # Add success message to chat
                        add_chat_message("assistant", f"""🎉 **Compile & Run Successful!**

Model `{model_name}` compiled and executed successfully!

**Compilation Time:** {comp_time:.2f} seconds
**Execution Time:** {exec_time:.2f} seconds
**Rows Affected:** {rows_affected:,} if rows_affected is not None else 'N/A'

Everything looks great! 🚀""")
                        
                    else:
                        # Execution failed
                        exec_errors = execution.get('errors', [])
                        st.error("❌ Execution failed after successful compilation")
                        
                        for error in exec_errors:
                            st.error(error)
                        
                        add_chat_message("assistant", f"""⚠️ **Partial Success**

Model `{model_name}` compiled successfully but execution failed.

**Compilation:** ✅ Success
**Execution:** ❌ Failed

**Execution Errors:**
{chr(10).join(f'- {error}' for error in exec_errors)}

Please fix the execution errors and try again. 🔧""", "error")
                
            else:
                # Compilation failed
                comp_errors = compilation.get('errors', [])
                st.error("❌ Compilation failed")
                
                for error in comp_errors:
                    st.error(error)
                
                add_chat_message("assistant", f"""❌ **Compilation Failed**

Model `{model_name}` failed to compile.

**Compilation Errors:**
{chr(10).join(f'- {error}' for error in comp_errors)}

Please fix the compilation errors before running. 🔧""", "error")
        
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response from server'
            st.error(f"❌ Request failed: {error_msg}")