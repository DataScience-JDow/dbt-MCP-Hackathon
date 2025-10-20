"""
Main Streamlit application for dbt MCP Hackathon Project
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Setup import paths
current_dir = Path(__file__).parent
project_root = current_dir.parent
parent_root = project_root.parent

# Add paths for imports
sys.path.insert(0, str(parent_root))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Change working directory to project root to help with relative imports
os.chdir(str(project_root))

# Import with error handling
def safe_import():
    """Import all required components with fallback handling"""
    try:
        # Try absolute imports first
        from dbt_mcp_hackathon_project.frontend.components.sidebar import render_sidebar
        from dbt_mcp_hackathon_project.frontend.components.model_explorer import render_model_explorer
        from dbt_mcp_hackathon_project.frontend.components.chat_interface import render_chat_interface
        from dbt_mcp_hackathon_project.frontend.components.connection_manager import (
            render_connection_status_banner,
            check_and_initialize_connection
        )
        from dbt_mcp_hackathon_project.frontend.utils.session_state import initialize_session_state
        from dbt_mcp_hackathon_project.frontend.utils.styling import apply_custom_css
        return (render_sidebar, render_model_explorer, render_chat_interface, 
                render_connection_status_banner, check_and_initialize_connection,
                initialize_session_state, apply_custom_css)
    except ImportError as e1:
        try:
            # Try relative imports
            from frontend.components.sidebar import render_sidebar
            from frontend.components.model_explorer import render_model_explorer
            from frontend.components.chat_interface import render_chat_interface
            from frontend.components.connection_manager import (
                render_connection_status_banner,
                check_and_initialize_connection
            )
            from frontend.utils.session_state import initialize_session_state
            from frontend.utils.styling import apply_custom_css
            return (render_sidebar, render_model_explorer, render_chat_interface, 
                    render_connection_status_banner, check_and_initialize_connection,
                    initialize_session_state, apply_custom_css)
        except ImportError as e2:
            # Last resort - direct relative imports
            from components.sidebar import render_sidebar
            from components.model_explorer import render_model_explorer
            from components.chat_interface import render_chat_interface
            from components.connection_manager import (
                render_connection_status_banner,
                check_and_initialize_connection
            )
            from utils.session_state import initialize_session_state
            from utils.styling import apply_custom_css
            return (render_sidebar, render_model_explorer, render_chat_interface, 
                    render_connection_status_banner, check_and_initialize_connection,
                    initialize_session_state, apply_custom_css)

# Import all components
try:
    (render_sidebar, render_model_explorer, render_chat_interface, 
     render_connection_status_banner, check_and_initialize_connection,
     initialize_session_state, apply_custom_css) = safe_import()
except ImportError as e:
    st.error(f"Failed to import required components: {e}")
    st.error("Please check the project structure and dependencies.")
    st.stop()

def main():
    """Main application entry point"""
    # Page configuration
    st.set_page_config(
        page_title="dbt MCP Hackathon Project",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Apply custom styling
    apply_custom_css()
    
    # Check and initialize MCP connection
    check_and_initialize_connection()
    
    # Main header
    st.title("🤖 dbt MCP Hackathon Project")
    st.markdown("*Your AI-powered dbt companion for model exploration and generation*")
    
    # Connection status banner
    render_connection_status_banner()
    
    # Render sidebar navigation
    current_page = render_sidebar()
    
    # Main content area based on navigation
    if current_page == "Model Explorer":
        render_model_explorer()
    elif current_page == "Chat Interface":
        render_chat_interface()
    else:
        # Default to Model Explorer if no valid page selected
        render_model_explorer()

# Removed welcome page function for simplified app

if __name__ == "__main__":
    main()