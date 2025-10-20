"""
Configuration settings for dbt MCP Hackathon Project
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class for dbt MCP Hackathon Project application"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DBT_PROJECT_PATH = PROJECT_ROOT
    
    # MCP Server settings
    MCP_HOST = os.getenv("MCP_HOST", "localhost")
    MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
    
    # Streamlit settings
    STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "localhost")
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Database settings
    DUCKDB_PATH = PROJECT_ROOT / "jaffle_and_flower_shop.duckdb"
    
    # AI settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.DBT_PROJECT_PATH.exists():
            raise ValueError(f"dbt project path does not exist: {cls.DBT_PROJECT_PATH}")
        
        if not cls.DUCKDB_PATH.exists():
            raise ValueError(f"DuckDB database does not exist: {cls.DUCKDB_PATH}")
        
        return True