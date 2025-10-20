"""
Session state management for Streamlit app
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Navigation state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Model Explorer"
    
    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Model data cache
    if 'models_cache' not in st.session_state:
        st.session_state.models_cache = {}
    
    if 'models_last_updated' not in st.session_state:
        st.session_state.models_last_updated = None
    
    # Selected model for detail view
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None
    
    # Search and filter state
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    if 'filter_materialization' not in st.session_state:
        st.session_state.filter_materialization = "All"
    
    if 'filter_layer' not in st.session_state:
        st.session_state.filter_layer = "All"
    
    # MCP server connection state
    if 'mcp_connected' not in st.session_state:
        st.session_state.mcp_connected = False
    
    if 'mcp_server_url' not in st.session_state:
        st.session_state.mcp_server_url = "http://localhost:8000"
    
    # Loading states
    if 'loading_models' not in st.session_state:
        st.session_state.loading_models = False
    
    if 'loading_chat' not in st.session_state:
        st.session_state.loading_chat = False
    
    # Error states
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None

def add_chat_message(role: str, content: str, message_type: str = "text", metadata: Optional[Dict[str, Any]] = None):
    """Add a message to chat history"""
    import uuid
    message = {
        "id": str(uuid.uuid4()),
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "message_type": message_type,
        "metadata": metadata or {}
    }
    st.session_state.chat_history.append(message)

def clear_chat_history():
    """Clear all chat messages"""
    st.session_state.chat_history = []

def update_models_cache(models_data: Dict[str, Any]):
    """Update the models cache with new data"""
    st.session_state.models_cache = models_data
    st.session_state.models_last_updated = datetime.now()

def get_models_cache() -> Dict[str, Any]:
    """Get cached models data"""
    return st.session_state.models_cache

def set_selected_model(model_name: Optional[str]):
    """Set the currently selected model"""
    st.session_state.selected_model = model_name

def get_selected_model() -> Optional[str]:
    """Get the currently selected model"""
    return st.session_state.selected_model

def set_mcp_connection_status(connected: bool):
    """Update MCP server connection status"""
    st.session_state.mcp_connected = connected

def is_mcp_connected() -> bool:
    """Check if MCP server is connected"""
    return st.session_state.mcp_connected

def set_loading_state(component: str, loading: bool):
    """Set loading state for a component"""
    if component == "models":
        st.session_state.loading_models = loading
    elif component == "chat":
        st.session_state.loading_chat = loading

def is_loading(component: str) -> bool:
    """Check if a component is in loading state"""
    if component == "models":
        return st.session_state.loading_models
    elif component == "chat":
        return st.session_state.loading_chat
    return False

def set_error(error_message: Optional[str]):
    """Set the last error message"""
    st.session_state.last_error = error_message

def get_last_error() -> Optional[str]:
    """Get the last error message"""
    return st.session_state.last_error

def clear_error():
    """Clear the last error message"""
    st.session_state.last_error = None