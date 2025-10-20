"""
Main Streamlit application for dbt MCP Hackathon Project
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dbt_mcp_hackathon_project.frontend.components.sidebar import render_sidebar
from dbt_mcp_hackathon_project.frontend.components.model_explorer import render_model_explorer
from dbt_mcp_hackathon_project.frontend.components.chat_interface import render_chat_interface
from dbt_mcp_hackathon_project.frontend.components.connection_manager import (
    render_connection_status_banner,
    check_and_initialize_connection
)
# Removed demo content imports for simplified app
from dbt_mcp_hackathon_project.frontend.utils.session_state import initialize_session_state
from dbt_mcp_hackathon_project.frontend.utils.styling import apply_custom_css

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