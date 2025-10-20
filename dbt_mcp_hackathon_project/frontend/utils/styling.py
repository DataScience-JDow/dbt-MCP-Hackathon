"""
Custom CSS styling for the Streamlit app
"""
import streamlit as st

def apply_custom_css():
    """Apply custom CSS styles to the Streamlit app"""
    
    css = """
    <style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Chat message styling - improved contrast and readability */
    .chat-message {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        border-left: 4px solid #007acc;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        line-height: 1.6;
    }
    
    .chat-message.user {
        background-color: #f8f9ff;
        border-left-color: #4285f4;
        margin-left: 2rem;
        color: #1a1a1a;
    }
    
    .chat-message.assistant {
        background-color: #f9f9f9;
        border-left-color: #34a853;
        margin-right: 2rem;
        color: #1a1a1a;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .message-content {
        line-height: 1.7;
        color: #2c3e50;
        font-size: 1rem;
    }
    
    .timestamp {
        color: #7f8c8d;
        font-size: 0.85rem;
        font-weight: normal;
    }
    
    /* Typing indicator */
    .typing-indicator {
        background-color: #f0f0f0 !important;
        border-left-color: #999 !important;
    }
    
    .typing-dots {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    
    .typing-dots .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #999;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots .dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots .dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { 
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% { 
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Model card styling */
    .model-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
        transition: box-shadow 0.2s ease;
    }
    
    .model-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .model-card.selected {
        border-color: #007acc;
        background-color: #e3f2fd;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-connected {
        background-color: #4caf50;
    }
    
    .status-disconnected {
        background-color: #f44336;
    }
    
    .status-loading {
        background-color: #ff9800;
        animation: pulse 1.5s ease-in-out infinite alternate;
    }
    
    @keyframes pulse {
        from { opacity: 1; }
        to { opacity: 0.5; }
    }
    
    /* Code block styling */
    .stCodeBlock {
        background-color: #f8f8f8;
        border: 1px solid #e0e0e0;
        border-radius: 0.25rem;
    }
    
    /* Code editor styling */
    .code-editor-container {
        background-color: #fafafa;
        border: 2px solid #007acc;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .code-editor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .validation-success {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 0.25rem;
        padding: 0.5rem;
        color: #2e7d32;
        margin: 0.5rem 0;
    }
    
    .validation-error {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 0.25rem;
        padding: 0.5rem;
        color: #c62828;
        margin: 0.5rem 0;
    }
    
    .validation-warning {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 0.25rem;
        padding: 0.5rem;
        color: #ef6c00;
        margin: 0.5rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 0.25rem;
        border: 1px solid #007acc;
        background-color: #007acc;
        color: white;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #005a9e;
        border-color: #005a9e;
    }
    
    /* Metric styling */
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
    }
    
    /* Loading animations */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #007acc;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Skeleton loading for model cards */
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .skeleton-card {
        height: 120px;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .skeleton-text {
        height: 1rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    
    .skeleton-text.short {
        width: 60%;
    }
    
    .skeleton-text.medium {
        width: 80%;
    }
    
    /* Progress indicators */
    .progress-container {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 3px;
        margin: 1rem 0;
    }
    
    .progress-bar {
        background: linear-gradient(45deg, #007acc, #0099ff);
        height: 20px;
        border-radius: 8px;
        transition: width 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background-image: linear-gradient(
            -45deg,
            rgba(255, 255, 255, .2) 25%,
            transparent 25%,
            transparent 50%,
            rgba(255, 255, 255, .2) 50%,
            rgba(255, 255, 255, .2) 75%,
            transparent 75%,
            transparent
        );
        background-size: 50px 50px;
        animation: move 2s linear infinite;
    }
    
    @keyframes move {
        0% { background-position: 0 0; }
        100% { background-position: 50px 50px; }
    }
    
    /* Error message styling */
    .error-message {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #c62828;
    }
    
    /* Success message styling */
    .success-message {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #2e7d32;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .chat-message.user {
            margin-left: 0.5rem;
        }
        
        .chat-message.assistant {
            margin-right: 0.5rem;
        }
        
        .model-card {
            padding: 0.75rem;
        }
    }
    
    @media (max-width: 480px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .chat-message {
            padding: 0.75rem;
        }
        
        .model-card {
            padding: 0.5rem;
        }
    }
    
    /* Smooth transitions */
    .model-card, .chat-message, .stButton > button {
        transition: all 0.2s ease-in-out;
    }
    
    /* Focus states for accessibility */
    .stButton > button:focus {
        outline: 2px solid #007acc;
        outline-offset: 2px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #007acc;
        box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
    }
    
    /* Chat-specific input styling */
    .chat-page .stTextArea > div > div > textarea {
        border: 2px solid #e1e5e9 !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        padding: 1rem !important;
        color: #2c3e50 !important;
        background-color: #ffffff !important;
    }
    
    .chat-page .stTextArea > div > div > textarea:focus {
        border-color: #4285f4 !important;
        box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.2) !important;
    }
    
    .chat-page .stTextArea > div > div > textarea::placeholder {
        color: #7f8c8d !important;
        font-style: italic;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Tour modal styling */
    .tour-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
        z-index: 999;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .tour-content {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        max-width: 600px;
        margin: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1000;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    /* Performance optimizations */
    .model-list-container {
        contain: layout style paint;
    }
    
    .chat-container {
        contain: layout style paint;
    }
    
    /* Fade-in animations */
    .fade-in {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Connection status styling */
    .connection-banner {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .connection-banner.connected {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        color: #2e7d32;
    }
    
    .connection-banner.disconnected {
        background-color: #ffebee;
        border: 1px solid #f44336;
        color: #c62828;
    }
    
    .connection-banner.connecting {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        color: #ef6c00;
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)