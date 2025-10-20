"""
Sidebar navigation component
"""
import streamlit as st
from dbt_mcp_hackathon_project.frontend.utils.session_state import is_mcp_connected
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client, update_mcp_client_url

def render_sidebar() -> str:
    """Render the sidebar navigation and return current page"""
    
    with st.sidebar:
        st.title("🤖 dbt MCP Hackathon Project")
        
        # Connection status indicator
        render_connection_status()
        
        st.markdown("---")
        
        # Navigation menu
        st.subheader("Navigation")
        
        # Page selection
        pages = ["Model Explorer", "Chat Interface"]
        
        # Use radio buttons for navigation
        selected_page = st.radio(
            "Choose a page:",
            pages,
            index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0,
            key="sidebar_navigation"
        )
        
        # Update session state if page changed
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("Quick Actions")
        
        if st.button("🔄 Refresh Models", help="Refresh model data from MCP server"):
            if is_mcp_connected():
                from dbt_mcp_hackathon_project.frontend.components.model_explorer import load_models_from_server
                load_models_from_server(force_refresh=True)
            else:
                st.error("MCP server not connected")
        
        if st.button("🗑️ Clear Chat", help="Clear chat history"):
            from dbt_mcp_hackathon_project.frontend.utils.session_state import clear_chat_history
            clear_chat_history()
            st.success("Chat history cleared!")
        
        st.markdown("---")
        
        # Settings section
        render_settings_section()
        
        # Help section
        render_help_section()
    
    return selected_page

def render_connection_status():
    """Render MCP server connection status"""
    st.subheader("Connection Status")
    
    if is_mcp_connected():
        st.markdown(
            '<div style="color: green;">🟢 MCP Server Connected</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="color: red;">🔴 MCP Server Disconnected</div>',
            unsafe_allow_html=True
        )
        
        if st.button("🔄 Retry Connection", key="retry_connection"):
            client = get_mcp_client()
            if client.health_check():
                st.success("✅ Connected to MCP server!")
                st.rerun()
            else:
                st.error("❌ Still cannot connect to MCP server")

def render_settings_section():
    """Render settings section"""
    with st.expander("⚙️ Settings"):
        st.subheader("MCP Server")
        
        # Server URL configuration
        server_url = st.text_input(
            "Server URL:",
            value=st.session_state.mcp_server_url,
            help="URL of the MCP server"
        )
        
        if server_url != st.session_state.mcp_server_url:
            update_mcp_client_url(server_url)
            st.info("Server URL updated. Connection will be retried on next request.")
        
        # Auto-refresh settings
        st.subheader("Display Options")
        
        auto_refresh = st.checkbox(
            "Auto-refresh models",
            value=st.session_state.get('auto_refresh_models', True),
            help="Automatically refresh model data periodically"
        )
        st.session_state.auto_refresh_models = auto_refresh
        
        # Results per page
        results_per_page = st.slider(
            "Models per page:",
            min_value=10,
            max_value=100,
            value=st.session_state.get('results_per_page', 25),
            step=5,
            help="Number of models to display per page"
        )
        st.session_state.results_per_page = results_per_page

def render_help_section():
    """Render help and information section"""
    with st.expander("❓ Help & Info"):
        st.markdown("""
        ### How to use dbt MCP Hackathon Project
        
        **Model Explorer:**
        - Browse all your dbt models
        - Search by name or description
        - Filter by materialization type
        - View model details and dependencies
        
        **Chat Interface:**
        - Generate new dbt models with AI
        - Ask questions about your data
        - Get help with SQL and dbt best practices
        
        **Tips:**
        - Ensure the MCP server is running (green status)
        - Use specific, descriptive language when generating models
        - Test generated models before using in production
        """)
        
        st.markdown("---")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**dbt MCP Hackathon Project** - AI-powered dbt companion")