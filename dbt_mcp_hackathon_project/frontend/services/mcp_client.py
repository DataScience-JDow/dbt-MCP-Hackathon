"""
MCP Server HTTP client for frontend communication
"""
import requests
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime, timedelta
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    set_mcp_connection_status,
    update_models_cache,
    set_loading_state,
    set_error,
    clear_error
)

class MCPClient:
    """HTTP client for communicating with the MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.last_health_check = None
        self.health_check_interval = timedelta(minutes=5)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        """Make HTTP request with error handling"""
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Clear any previous errors
            clear_error()
            
            # Update connection status
            set_mcp_connection_status(True)
            
            # Parse JSON response
            if response.content:
                return True, response.json()
            else:
                return True, None
                
        except requests.exceptions.ConnectionError:
            error_msg = f"Cannot connect to MCP server at {self.base_url}"
            set_error(error_msg)
            set_mcp_connection_status(False)
            return False, {"error": "connection_error", "message": error_msg}
            
        except requests.exceptions.Timeout:
            error_msg = "Request to MCP server timed out"
            set_error(error_msg)
            return False, {"error": "timeout", "message": error_msg}
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            set_error(error_msg)
            return False, {"error": "http_error", "message": error_msg, "status_code": e.response.status_code}
            
        except json.JSONDecodeError:
            error_msg = "Invalid JSON response from MCP server"
            set_error(error_msg)
            return False, {"error": "json_error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            set_error(error_msg)
            return False, {"error": "unknown_error", "message": error_msg}
    
    def health_check(self) -> bool:
        """Check if MCP server is healthy"""
        
        # Skip frequent health checks
        now = datetime.now()
        if (self.last_health_check and 
            now - self.last_health_check < self.health_check_interval):
            return st.session_state.get('mcp_connected', False)
        
        success, response = self._make_request("GET", "/health")
        self.last_health_check = now
        
        if success:
            set_mcp_connection_status(True)
            return True
        else:
            set_mcp_connection_status(False)
            return False
    
    def get_models(self, force_refresh: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """Get all models from MCP server"""
        
        # Check cache first unless force refresh
        if not force_refresh:
            cached_models = st.session_state.get('models_cache', {})
            cache_time = st.session_state.get('models_last_updated')
            
            if cached_models and cache_time:
                # Use cache if less than 10 minutes old
                if datetime.now() - cache_time < timedelta(minutes=10):
                    return True, cached_models
        
        set_loading_state("models", True)
        
        try:
            success, response = self._make_request("GET", "/models")
            
            if success and response:
                # Update cache
                update_models_cache(response)
                return True, response
            else:
                return False, response or {}
                
        finally:
            set_loading_state("models", False)
    
    def get_model_details(self, model_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Get detailed information for a specific model"""
        
        success, response = self._make_request("GET", f"/models/{model_name}")
        return success, response or {}
    
    def get_model_lineage(self, model_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Get lineage information for a model"""
        
        success, response = self._make_request("GET", f"/lineage/{model_name}")
        return success, response or {}
    
    def create_model(self, model_spec: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Create a new model"""
        
        set_loading_state("chat", True)
        
        try:
            success, response = self._make_request(
                "POST", 
                "/models",
                json=model_spec,
                headers={"Content-Type": "application/json"}
            )
            return success, response or {}
            
        finally:
            set_loading_state("chat", False)
    
    def generate_sql(self, prompt: str, context: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
        """Generate SQL from natural language prompt"""
        
        set_loading_state("chat", True)
        
        try:
            payload = {"prompt": prompt}
            if context:
                payload["context"] = context
            
            success, response = self._make_request(
                "POST",
                "/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            return success, response or {}
            
        finally:
            set_loading_state("chat", False)
    
    def compile_model(self, model_name: str, sql_content: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Compile a model"""
        
        set_loading_state("compilation", True)
        
        try:
            params = {"model_name": model_name}
            
            success, response = self._make_request(
                "POST",
                "/compile",
                params=params,
                headers={"Content-Type": "application/json"}
            )
            return success, response or {}
            
        finally:
            set_loading_state("compilation", False)
    
    def run_model(self, model_name: str, with_dependencies: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """Run a model"""
        
        set_loading_state("execution", True)
        
        try:
            params = {
                "model_name": model_name,
                "with_dependencies": with_dependencies
            }
            
            success, response = self._make_request(
                "POST",
                "/run",
                params=params,
                headers={"Content-Type": "application/json"}
            )
            return success, response or {}
            
        finally:
            set_loading_state("execution", False)
    
    def get_model_results(self, model_name: str, limit: int = 100) -> Tuple[bool, Dict[str, Any]]:
        """Get results from a model execution"""
        
        params = {"limit": limit}
        success, response = self._make_request("GET", f"/results/{model_name}", params=params)
        return success, response or {}
    
    def compile_and_run_model(self, model_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Compile and run a model in one operation"""
        
        set_loading_state("compilation", True)
        set_loading_state("execution", True)
        
        try:
            params = {"model_name": model_name}
            
            success, response = self._make_request(
                "POST",
                "/compile-and-run",
                params=params,
                headers={"Content-Type": "application/json"}
            )
            return success, response or {}
            
        finally:
            set_loading_state("compilation", False)
            set_loading_state("execution", False)
    
    def validate_sql(self, sql: str, model_name: str = "temp_model") -> Tuple[bool, Dict[str, Any]]:
        """Validate SQL syntax"""
        
        payload = {"sql": sql, "model_name": model_name}
        
        success, response = self._make_request(
            "POST",
            "/validate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return success, response or {}
    
    def get_manifest_info(self) -> Tuple[bool, Dict[str, Any]]:
        """Get information about the dbt manifest"""
        
        success, response = self._make_request("GET", "/manifest-info")
        return success, response or {}

# Global client instance
_mcp_client = None

def get_mcp_client() -> MCPClient:
    """Get or create MCP client instance"""
    global _mcp_client
    
    if _mcp_client is None:
        server_url = st.session_state.get('mcp_server_url', 'http://localhost:8000')
        _mcp_client = MCPClient(server_url)
    
    return _mcp_client

def update_mcp_client_url(new_url: str):
    """Update MCP client URL"""
    global _mcp_client
    _mcp_client = MCPClient(new_url)
    st.session_state.mcp_server_url = new_url