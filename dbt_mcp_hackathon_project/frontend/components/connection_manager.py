"""
Connection manager component for MCP server
"""
import streamlit as st
from typing import Optional
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    is_mcp_connected,
    set_mcp_connection_status,
    get_last_error,
    clear_error
)
from dbt_mcp_hackathon_project.frontend.components.loading_components import (
    render_connection_status_banner as render_enhanced_connection_banner,
    render_loading_spinner
)

def render_connection_status_banner():
    """Render enhanced connection status banner at the top of pages"""
    
    # Use the enhanced connection banner from loading components
    render_enhanced_connection_banner()

def render_disconnected_banner():
    """Render disconnected state banner with retry options"""
    
    error_msg = get_last_error()
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if error_msg:
                st.error(f"❌ MCP Server Disconnected: {error_msg}")
            else:
                st.error("❌ MCP Server Disconnected")
        
        with col2:
            if st.button("🔄 Retry", key="banner_retry"):
                attempt_connection_retry()

def attempt_connection_retry():
    """Attempt to reconnect to MCP server with enhanced loading"""
    
    placeholder = st.empty()
    
    with placeholder.container():
        render_loading_spinner("Connecting to MCP server...")
    
    client = get_mcp_client()
    
    if client.health_check():
        set_mcp_connection_status(True)
        clear_error()
        st.session_state.show_connection_success = True
        st.success("✅ Successfully connected to MCP server!")
        st.rerun()
    else:
        st.error("❌ Still unable to connect to MCP server")

def render_connection_diagnostics():
    """Render detailed connection diagnostics"""
    
    with st.expander("🔧 Connection Diagnostics"):
        client = get_mcp_client()
        
        st.markdown("**Server Configuration:**")
        st.code(f"URL: {client.base_url}")
        st.code(f"Timeout: {client.session.timeout}s")
        
        st.markdown("**Connection Test:**")
        
        if st.button("Test Connection", key="test_connection"):
            with st.spinner("Testing connection..."):
                success = client.health_check()
                
                if success:
                    st.success("✅ Connection test successful")
                else:
                    error_msg = get_last_error()
                    st.error(f"❌ Connection test failed: {error_msg}")
        
        st.markdown("**Troubleshooting:**")
        st.markdown("""
        1. **Check if MCP server is running:**
           ```bash
           python -m dbt_mcp_hackathon_project server
           ```
        
        2. **Verify server URL in sidebar settings**
        
        3. **Check firewall/network settings**
        
        4. **Ensure dbt project is properly configured**
        """)

def check_and_initialize_connection():
    """Check connection on app startup and initialize if needed"""
    
    # Only check once per session
    if st.session_state.get('connection_checked', False):
        return
    
    st.session_state.connection_checked = True
    
    # Attempt initial connection
    client = get_mcp_client()
    
    with st.spinner("Checking MCP server connection..."):
        if client.health_check():
            set_mcp_connection_status(True)
            # Load initial model data
            try:
                from dbt_mcp_hackathon_project.frontend.components.model_explorer import load_models_from_server
                load_models_from_server()
            except Exception:
                pass  # Ignore errors during initial load
        else:
            set_mcp_connection_status(False)

def render_connection_settings():
    """Render connection settings in sidebar"""
    
    st.subheader("🔗 MCP Server")
    
    # Server URL input
    current_url = st.session_state.get('mcp_server_url', 'http://localhost:8000')
    new_url = st.text_input(
        "Server URL:",
        value=current_url,
        help="URL of the MCP server (e.g., http://localhost:8000)"
    )
    
    if new_url != current_url:
        from dbt_mcp_hackathon_project.frontend.services.mcp_client import update_mcp_client_url
        update_mcp_client_url(new_url)
        st.info("Server URL updated")
    
    # Connection actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Test", key="sidebar_test"):
            client = get_mcp_client()
            if client.health_check():
                st.success("✅ Connected!")
            else:
                st.error("❌ Failed")
    
    with col2:
        if st.button("🔧 Diagnose", key="sidebar_diagnose"):
            st.session_state.show_diagnostics = True
    
    # Show diagnostics if requested
    if st.session_state.get('show_diagnostics', False):
        render_connection_diagnostics()
        if st.button("Close Diagnostics"):
            st.session_state.show_diagnostics = False

def get_connection_status_indicator() -> str:
    """Get connection status indicator for UI"""
    
    if is_mcp_connected():
        return "🟢"
    else:
        return "🔴"

def get_connection_status_text() -> str:
    """Get connection status text for UI"""
    
    if is_mcp_connected():
        return "Connected"
    else:
        return "Disconnected"