"""
Test configuration and fixtures for dbt MCP Hackathon Project tests
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest
import duckdb
from unittest.mock import Mock, patch

from dbt_mcp_hackathon_project.config import Config
from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer


@pytest.fixture
def temp_dbt_project():
    """Create a temporary dbt project structure for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create basic dbt project structure
        (project_path / "models").mkdir()
        (project_path / "target").mkdir()
        
        # Create a basic dbt_project.yml
        dbt_project_content = {
            "name": "test_project",
            "version": "1.0.0",
            "profile": "test_profile"
        }
        with open(project_path / "dbt_project.yml", "w") as f:
            json.dump(dbt_project_content, f)
        
        yield project_path


@pytest.fixture
def mock_manifest():
    """Create a mock dbt manifest for testing"""
    return {
        "nodes": {
            "model.test_project.test_model": {
                "name": "test_model",
                "resource_type": "model",
                "original_file_path": "models/test_model.sql",
                "description": "A test model",
                "columns": {
                    "id": {
                        "name": "id",
                        "data_type": "integer",
                        "description": "Primary key",
                        "tests": ["unique", "not_null"]
                    },
                    "name": {
                        "name": "name",
                        "data_type": "varchar",
                        "description": "Name field"
                    }
                },
                "depends_on": {
                    "nodes": ["source.test_project.raw_data"]
                },
                "config": {
                    "materialized": "table"
                },
                "tags": ["test", "core"]
            }
        }
    }


@pytest.fixture
def temp_duckdb():
    """Create a temporary DuckDB database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as temp_file:
        db_path = Path(temp_file.name)
    
    # Remove the empty file first
    db_path.unlink()
    
    # Create a simple test database
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE test_table (id INTEGER, name VARCHAR)")
    conn.execute("INSERT INTO test_table VALUES (1, 'test')")
    conn.close()
    
    yield db_path
    
    # Cleanup with retry for Windows file locking
    import time
    for _ in range(3):
        try:
            if db_path.exists():
                db_path.unlink()
            break
        except PermissionError:
            time.sleep(0.1)


@pytest.fixture
def mock_config(temp_dbt_project, temp_duckdb):
    """Create a mock configuration for testing"""
    with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
         patch.object(Config, 'DUCKDB_PATH', temp_duckdb):
        yield Config


@pytest.fixture
def mcp_server_with_mocks(mock_config, mock_manifest, temp_dbt_project):
    """Create an MCP server instance with mocked dependencies"""
    
    # Create manifest file in the temp project
    manifest_path = temp_dbt_project / "target" / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(mock_manifest, f)
    
    # Mock the Config class
    with patch('dbt_mcp_hackathon_project.backend.mcp_server.Config', return_value=mock_config):
        server = MCPServer()
        yield server
        
        # Cleanup: close database connection
        if hasattr(server, 'db_connection') and server.db_connection:
            try:
                server.db_connection.close()
            except:
                pass