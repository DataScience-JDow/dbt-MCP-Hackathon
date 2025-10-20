"""
Unit tests for MCP Server foundation
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import duckdb
from fastapi.testclient import TestClient

from dbt_mcp_hackathon_project.backend.mcp_server import MCPServer
from dbt_mcp_hackathon_project.config import Config


class TestMCPServerInitialization:
    """Test MCP Server initialization and basic functionality"""
    
    def test_server_initialization_success(self, mcp_server_with_mocks):
        """Test successful server initialization"""
        server = mcp_server_with_mocks
        
        # Verify server components are initialized
        assert server.app is not None
        assert server.config is not None
        assert server.db_connection is not None
        assert server.dbt_manifest is not None
        
        # Verify FastAPI app is configured
        assert server.app.title == "dbt MCP Hackathon Project MCP Server"
        assert server.app.version == "0.1.0"
    
    def test_server_initialization_missing_dbt_project(self, temp_duckdb):
        """Test server initialization with missing dbt project"""
        with patch.object(Config, 'DBT_PROJECT_PATH', Path("/nonexistent")), \
             patch.object(Config, 'DUCKDB_PATH', temp_duckdb):
            
            with pytest.raises(ValueError, match="dbt project path does not exist"):
                MCPServer()
    
    def test_server_initialization_missing_database(self, temp_dbt_project):
        """Test server initialization with missing database"""
        with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
             patch.object(Config, 'DUCKDB_PATH', Path("/nonexistent.duckdb")):
            
            with pytest.raises(ValueError, match="DuckDB database does not exist"):
                MCPServer()
    
    def test_database_connection_success(self, mock_config):
        """Test successful database connection"""
        with patch('dbt_mcp_hackathon_project.backend.mcp_server.Config', return_value=mock_config):
            server = MCPServer()
            
            # Verify database connection is established
            assert server.db_connection is not None
            assert isinstance(server.db_connection, duckdb.DuckDBPyConnection)
    
    def test_database_connection_failure(self, temp_dbt_project):
        """Test database connection failure handling"""
        with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
             patch.object(Config, 'DUCKDB_PATH', Path("/invalid/path.duckdb")), \
             patch.object(Config, 'validate', return_value=True):
            
            with pytest.raises(Exception):
                MCPServer()


class TestMCPServerHealthCheck:
    """Test health check endpoint functionality"""
    
    def test_health_check_success(self, mcp_server_with_mocks):
        """Test successful health check"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "dbt_project_path" in data
        assert data["database_connected"] is True
        assert data["models_count"] == 1  # From mock manifest
    
    def test_health_check_no_manifest(self, mock_config):
        """Test health check with no manifest loaded"""
        with patch('dbt_mcp_hackathon_project.backend.mcp_server.Config', return_value=mock_config):
            server = MCPServer()
            server.dbt_manifest = None
            
            with TestClient(server.app) as client:
                response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["models_count"] == 0
    
    def test_health_check_database_disconnected(self, mcp_server_with_mocks):
        """Test health check with database disconnected"""
        server = mcp_server_with_mocks
        server.db_connection = None
        
        with TestClient(server.app) as client:
            response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["database_connected"] is False


class TestMCPServerManifestLoading:
    """Test dbt manifest loading functionality"""
    
    def test_manifest_loading_success(self, temp_dbt_project, mock_manifest):
        """Test successful manifest loading"""
        # Create manifest file
        manifest_path = temp_dbt_project / "target" / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(mock_manifest, f)
        
        with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
             patch.object(Config, 'DUCKDB_PATH', Path(":memory:")), \
             patch.object(Config, 'validate', return_value=True), \
             patch('duckdb.connect') as mock_connect:
            
            mock_connect.return_value = MagicMock()
            server = MCPServer()
            
            assert server.dbt_manifest is not None
            assert len(server.dbt_manifest["nodes"]) == 1
    
    def test_manifest_loading_missing_file(self, temp_dbt_project):
        """Test manifest loading with missing manifest file"""
        with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
             patch.object(Config, 'DUCKDB_PATH', Path(":memory:")), \
             patch.object(Config, 'validate', return_value=True), \
             patch('duckdb.connect') as mock_connect:
            
            mock_connect.return_value = MagicMock()
            server = MCPServer()
            
            # Server should initialize without manifest
            assert server.dbt_manifest is None
    
    def test_manifest_loading_invalid_json(self, temp_dbt_project):
        """Test manifest loading with invalid JSON"""
        # Create invalid manifest file
        manifest_path = temp_dbt_project / "target" / "manifest.json"
        with open(manifest_path, "w") as f:
            f.write("invalid json content")
        
        with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
             patch.object(Config, 'DUCKDB_PATH', Path(":memory:")), \
             patch.object(Config, 'validate', return_value=True), \
             patch('duckdb.connect') as mock_connect:
            
            mock_connect.return_value = MagicMock()
            server = MCPServer()
            
            # Server should initialize without manifest due to JSON error
            assert server.dbt_manifest is None


class TestMCPServerErrorScenarios:
    """Test error handling scenarios"""
    
    def test_config_validation_failure(self):
        """Test server initialization with config validation failure"""
        with patch.object(Config, 'validate', side_effect=ValueError("Config validation failed")):
            with pytest.raises(ValueError, match="Config validation failed"):
                MCPServer()
    
    def test_database_connection_exception(self, temp_dbt_project):
        """Test database connection exception handling"""
        with patch.object(Config, 'DBT_PROJECT_PATH', temp_dbt_project), \
             patch.object(Config, 'DUCKDB_PATH', Path("test.duckdb")), \
             patch.object(Config, 'validate', return_value=True), \
             patch('duckdb.connect', side_effect=Exception("Database error")):
            
            with pytest.raises(Exception, match="Database error"):
                MCPServer()
    
    def test_health_check_exception_handling(self, mcp_server_with_mocks):
        """Test health check endpoint exception handling"""
        server = mcp_server_with_mocks
        
        # Mock an exception by making the model service raise an error
        original_model_service = server.model_service
        mock_model_service = Mock()
        mock_model_service.get_all_models.side_effect = Exception("Test error")
        mock_model_service.manifest = True  # Make it appear to have a manifest
        
        server.model_service = mock_model_service
        
        with TestClient(server.app) as client:
            response = client.get("/health")
        
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]
        
        # Restore original model service
        server.model_service = original_model_service


class TestMCPServerConfiguration:
    """Test server configuration and setup"""
    
    def test_cors_middleware_setup(self, mcp_server_with_mocks):
        """Test CORS middleware is properly configured"""
        server = mcp_server_with_mocks
        
        # Test CORS functionality by making a preflight request
        with TestClient(server.app) as client:
            response = client.options("/health", headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            })
            
            # CORS should allow the request (status 200) and include CORS headers
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers
    
    def test_routes_setup(self, mcp_server_with_mocks):
        """Test that all required routes are set up"""
        server = mcp_server_with_mocks
        
        # Get all route paths
        route_paths = [route.path for route in server.app.routes]
        
        # Verify required endpoints exist
        assert "/health" in route_paths
        assert "/models" in route_paths
        assert "/models/{model_name}" in route_paths
        assert "/lineage/{model_name}" in route_paths
        assert "/search/models" in route_paths
        assert "/refresh" in route_paths
    
    def test_get_app_method(self, mcp_server_with_mocks):
        """Test get_app method returns FastAPI instance"""
        server = mcp_server_with_mocks
        app = server.get_app()
        
        assert app is server.app
        assert app.title == "dbt MCP Hackathon Project MCP Server"