"""
Loading components and animations for better UX
"""
import streamlit as st
import time
from typing import List, Optional


def render_loading_spinner(text: str = "Loading...", size: str = "medium"):
    """Render a loading spinner with text"""
    
    size_classes = {
        "small": "width: 16px; height: 16px; border-width: 2px;",
        "medium": "width: 24px; height: 24px; border-width: 3px;",
        "large": "width: 32px; height: 32px; border-width: 4px;"
    }
    
    spinner_style = size_classes.get(size, size_classes["medium"])
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; padding: 1rem;">
        <div class="loading-spinner" style="{spinner_style}"></div>
        <span>{text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_skeleton_model_cards(count: int = 3):
    """Render skeleton loading cards for model list"""
    
    for i in range(count):
        st.markdown(f"""
        <div class="skeleton skeleton-card" key="skeleton_{i}">
            <div style="padding: 1rem;">
                <div class="skeleton skeleton-text medium"></div>
                <div class="skeleton skeleton-text short"></div>
                <div class="skeleton skeleton-text medium"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_progress_bar(progress: float, text: str = "", show_percentage: bool = True):
    """Render an animated progress bar"""
    
    percentage = min(100, max(0, progress * 100))
    
    progress_text = text
    if show_percentage:
        progress_text += f" ({percentage:.0f}%)"
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {percentage}%"></div>
    </div>
    <div style="text-align: center; margin-top: 0.5rem; color: #666;">
        {progress_text}
    </div>
    """, unsafe_allow_html=True)


def render_loading_overlay(message: str = "Processing..."):
    """Render a full-screen loading overlay"""
    
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 1rem;
    ">
        <div class="loading-spinner" style="width: 40px; height: 40px; border-width: 4px;"></div>
        <div style="font-size: 1.2rem; color: #333;">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_typing_indicator():
    """Render typing indicator for chat"""
    
    st.markdown("""
    <div class="chat-message assistant typing-indicator fade-in">
        <div class="message-header">
            <strong>🤖 dbt MCP Hackathon Project</strong>
            <small style="color: #666;">is typing...</small>
        </div>
        <div class="typing-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_connection_status_banner():
    """Render connection status banner with animations"""
    
    from dbt_mcp_hackathon_project.frontend.utils.session_state import is_mcp_connected
    
    if is_mcp_connected():
        st.markdown("""
        <div class="connection-banner connected fade-in">
            <div class="status-indicator status-connected"></div>
            <strong>Connected to MCP Server</strong>
            <span style="margin-left: auto; font-size: 0.9rem;">Ready for model operations</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="connection-banner disconnected fade-in">
            <div class="status-indicator status-disconnected"></div>
            <strong>MCP Server Disconnected</strong>
            <span style="margin-left: auto; font-size: 0.9rem;">Some features may be unavailable</span>
        </div>
        """, unsafe_allow_html=True)


def render_model_card_skeleton():
    """Render a single skeleton model card"""
    
    st.markdown("""
    <div class="model-card skeleton">
        <div style="padding: 1rem;">
            <div class="skeleton skeleton-text medium" style="margin-bottom: 0.5rem;"></div>
            <div class="skeleton skeleton-text short" style="margin-bottom: 0.5rem;"></div>
            <div class="skeleton skeleton-text medium" style="margin-bottom: 0.5rem;"></div>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <div class="skeleton skeleton-text short" style="width: 60px; height: 24px;"></div>
                <div class="skeleton skeleton-text short" style="width: 80px; height: 24px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_loading_message(message: str, duration: float = 2.0):
    """Show a temporary loading message"""
    
    placeholder = st.empty()
    
    with placeholder.container():
        render_loading_spinner(message)
    
    time.sleep(duration)
    placeholder.empty()


def render_operation_progress(steps: List[str], current_step: int):
    """Render progress for multi-step operations"""
    
    total_steps = len(steps)
    progress = (current_step - 1) / total_steps if total_steps > 0 else 0
    
    st.markdown("### Operation Progress")
    
    render_progress_bar(progress, f"Step {current_step} of {total_steps}")
    
    # Show steps
    for i, step in enumerate(steps, 1):
        if i < current_step:
            # Completed step
            st.markdown(f"✅ **{i}.** {step}")
        elif i == current_step:
            # Current step
            st.markdown(f"🔄 **{i}.** {step} *(in progress)*")
        else:
            # Future step
            st.markdown(f"⏳ **{i}.** {step}")


def render_data_loading_placeholder(rows: int = 5):
    """Render placeholder for data tables while loading"""
    
    st.markdown("### Loading Data...")
    
    # Create skeleton table
    cols = st.columns([2, 1, 1, 1])
    
    with cols[0]:
        st.markdown("**Name**")
    with cols[1]:
        st.markdown("**Type**")
    with cols[2]:
        st.markdown("**Layer**")
    with cols[3]:
        st.markdown("**Status**")
    
    st.markdown("---")
    
    for i in range(rows):
        cols = st.columns([2, 1, 1, 1])
        
        with cols[0]:
            st.markdown('<div class="skeleton skeleton-text medium"></div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown('<div class="skeleton skeleton-text short"></div>', unsafe_allow_html=True)
        with cols[2]:
            st.markdown('<div class="skeleton skeleton-text short"></div>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown('<div class="skeleton skeleton-text short"></div>', unsafe_allow_html=True)


class LoadingContext:
    """Context manager for loading states"""
    
    def __init__(self, component: str, message: str = "Loading..."):
        self.component = component
        self.message = message
        self.placeholder = None
    
    def __enter__(self):
        from dbt_mcp_hackathon_project.frontend.utils.session_state import set_loading_state
        
        set_loading_state(self.component, True)
        self.placeholder = st.empty()
        
        with self.placeholder.container():
            render_loading_spinner(self.message)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from dbt_mcp_hackathon_project.frontend.utils.session_state import set_loading_state
        
        set_loading_state(self.component, False)
        
        if self.placeholder:
            self.placeholder.empty()
    
    def update_message(self, message: str):
        """Update the loading message"""
        if self.placeholder:
            with self.placeholder.container():
                render_loading_spinner(message)


def with_loading(component: str, message: str = "Loading..."):
    """Decorator for functions that need loading states"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoadingContext(component, message):
                return func(*args, **kwargs)
        return wrapper
    
    return decorator


def render_empty_state(title: str, description: str, action_text: Optional[str] = None, action_callback = None):
    """Render an empty state with optional action"""
    
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        color: #666;
    ">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
        <h3 style="color: #333; margin-bottom: 0.5rem;">{title}</h3>
        <p style="margin-bottom: 2rem;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if action_text and action_callback:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(action_text, use_container_width=True):
                action_callback()


def render_error_state(title: str, description: str, error_details: Optional[str] = None):
    """Render an error state with details"""
    
    st.markdown(f"""
    <div class="error-message fade-in">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem;">⚠️</span>
            <strong>{title}</strong>
        </div>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if error_details:
        with st.expander("Error Details"):
            st.code(error_details, language="text")


def render_success_state(title: str, description: str):
    """Render a success state"""
    
    st.markdown(f"""
    <div class="success-message fade-in">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem;">✅</span>
            <strong>{title}</strong>
        </div>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)