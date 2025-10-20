"""
Tests for model exploration features
"""
import json
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from dbt_mcp_hackathon_project.backend.model_service import ModelMetadataService
from dbt_mcp_hackathon_project.shared.models import ModelMetadata, ColumnInfo


class TestModelMetadataExtraction:
    """Test model metadata extraction with sample dbt project"""
    
    def test_extract_model_metadata_complete(self, mock_manifest):
        """Test extraction of complete model metadata"""
        service = ModelMetadataService()
        service.manifest = mock_manifest
        
        models = service.get_all_models()
        
        assert len(models) == 1
        model = models[0]
        
        # Verify basic model properties
        assert model.name == "test_model"
        assert model.path == "models/test_model.sql"
        assert model.description == "A test model"
        assert model.materialization == "table"
        assert model.tags == ["test", "core"]
        
        # Verify column information
        assert len(model.columns) == 2
        
        id_column = next(col for col in model.columns if col.name == "id")
        assert id_column.data_type == "integer"
        assert id_column.description == "Primary key"
        assert "unique" in id_column.tests
        assert "not_null" in id_column.tests
        
        name_column = next(col for col in model.columns if col.name == "name")
        assert name_column.data_type == "varchar"
        assert name_column.description == "Name field"
    
    def test_extract_model_metadata_minimal(self):
        """Test extraction with minimal model information"""
        minimal_manifest = {
            "nodes": {
                "model.test_project.minimal_model": {
                    "name": "minimal_model",
                    "resource_type": "model",
                    "original_file_path": "models/minimal.sql"
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = minimal_manifest
        
        models = service.get_all_models()
        
        assert len(models) == 1
        model = models[0]
        
        assert model.name == "minimal_model"
        assert model.path == "models/minimal.sql"
        assert model.description is None
        assert model.materialization == "view"  # default
        assert len(model.columns) == 0
        assert len(model.depends_on) == 0
        assert len(model.referenced_by) == 0
        assert len(model.tags) == 0
    
    def test_extract_model_with_dependencies(self):
        """Test extraction of model with dependencies"""
        manifest_with_deps = {
            "nodes": {
                "model.test_project.parent_model": {
                    "name": "parent_model",
                    "resource_type": "model",
                    "original_file_path": "models/parent.sql",
                    "depends_on": {"nodes": []}
                },
                "model.test_project.child_model": {
                    "name": "child_model",
                    "resource_type": "model", 
                    "original_file_path": "models/child.sql",
                    "depends_on": {"nodes": ["model.test_project.parent_model"]}
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = manifest_with_deps
        
        models = service.get_all_models()
        
        parent_model = next(m for m in models if m.name == "parent_model")
        child_model = next(m for m in models if m.name == "child_model")
        
        # Parent should be referenced by child
        assert "child_model" in parent_model.referenced_by
        assert len(parent_model.depends_on) == 0
        
        # Child should depend on parent
        assert "parent_model" in child_model.depends_on
        assert len(child_model.referenced_by) == 0
    
    def test_get_model_by_name_exists(self, mock_manifest):
        """Test retrieving existing model by name"""
        service = ModelMetadataService()
        service.manifest = mock_manifest
        
        model = service.get_model_by_name("test_model")
        
        assert model is not None
        assert model.name == "test_model"
        assert model.description == "A test model"
    
    def test_get_model_by_name_not_exists(self, mock_manifest):
        """Test retrieving non-existent model by name"""
        service = ModelMetadataService()
        service.manifest = mock_manifest
        
        model = service.get_model_by_name("nonexistent_model")
        
        assert model is None
    
    def test_get_model_dependencies_complete(self):
        """Test getting complete dependency information"""
        manifest_with_deps = {
            "nodes": {
                "model.test_project.source_model": {
                    "name": "source_model",
                    "resource_type": "model",
                    "original_file_path": "models/source.sql",
                    "depends_on": {"nodes": []}
                },
                "model.test_project.intermediate_model": {
                    "name": "intermediate_model",
                    "resource_type": "model",
                    "original_file_path": "models/intermediate.sql",
                    "depends_on": {"nodes": ["model.test_project.source_model"]}
                },
                "model.test_project.final_model": {
                    "name": "final_model",
                    "resource_type": "model",
                    "original_file_path": "models/final.sql",
                    "depends_on": {"nodes": ["model.test_project.intermediate_model"]}
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = manifest_with_deps
        
        deps = service.get_model_dependencies("intermediate_model")
        
        assert "source_model" in deps["upstream"]
        assert "final_model" in deps["downstream"]
        assert len(deps["upstream"]) == 1
        assert len(deps["downstream"]) == 1
    
    def test_get_model_dependencies_nonexistent(self, mock_manifest):
        """Test getting dependencies for non-existent model"""
        service = ModelMetadataService()
        service.manifest = mock_manifest
        
        deps = service.get_model_dependencies("nonexistent_model")
        
        assert deps["upstream"] == []
        assert deps["downstream"] == []


class TestModelSearchAndFiltering:
    """Test search and filtering functionality"""
    
    def test_search_by_name(self):
        """Test searching models by name"""
        search_manifest = {
            "nodes": {
                "model.test_project.customer_orders": {
                    "name": "customer_orders",
                    "resource_type": "model",
                    "original_file_path": "models/customer_orders.sql",
                    "description": "Customer order data"
                },
                "model.test_project.product_sales": {
                    "name": "product_sales", 
                    "resource_type": "model",
                    "original_file_path": "models/product_sales.sql",
                    "description": "Product sales metrics"
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = search_manifest
        
        # Search for "customer"
        results = service.search_models("customer")
        
        assert len(results) == 1
        assert results[0].name == "customer_orders"
    
    def test_search_by_description(self):
        """Test searching models by description"""
        search_manifest = {
            "nodes": {
                "model.test_project.model_a": {
                    "name": "model_a",
                    "resource_type": "model",
                    "original_file_path": "models/model_a.sql",
                    "description": "Contains customer information"
                },
                "model.test_project.model_b": {
                    "name": "model_b",
                    "resource_type": "model", 
                    "original_file_path": "models/model_b.sql",
                    "description": "Product catalog data"
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = search_manifest
        
        # Search for "customer" in description
        results = service.search_models("customer")
        
        assert len(results) == 1
        assert results[0].name == "model_a"
    
    def test_search_by_tags(self):
        """Test searching models by tags"""
        search_manifest = {
            "nodes": {
                "model.test_project.staging_model": {
                    "name": "staging_model",
                    "resource_type": "model",
                    "original_file_path": "models/staging_model.sql",
                    "tags": ["staging", "raw_data"]
                },
                "model.test_project.mart_model": {
                    "name": "mart_model",
                    "resource_type": "model",
                    "original_file_path": "models/mart_model.sql", 
                    "tags": ["mart", "analytics"]
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = search_manifest
        
        # Search for "staging" in tags
        results = service.search_models("staging")
        
        assert len(results) == 1
        assert results[0].name == "staging_model"
    
    def test_filter_by_materialization(self):
        """Test filtering models by materialization type"""
        filter_manifest = {
            "nodes": {
                "model.test_project.view_model": {
                    "name": "view_model",
                    "resource_type": "model",
                    "original_file_path": "models/view_model.sql",
                    "config": {"materialized": "view"}
                },
                "model.test_project.table_model": {
                    "name": "table_model",
                    "resource_type": "model",
                    "original_file_path": "models/table_model.sql",
                    "config": {"materialized": "table"}
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = filter_manifest
        
        # Filter by table materialization
        results = service.search_models("", {"materialization": "table"})
        
        assert len(results) == 1
        assert results[0].name == "table_model"
        assert results[0].materialization == "table"
    
    def test_filter_by_tags(self):
        """Test filtering models by tags"""
        filter_manifest = {
            "nodes": {
                "model.test_project.core_model": {
                    "name": "core_model",
                    "resource_type": "model",
                    "original_file_path": "models/core_model.sql",
                    "tags": ["core", "important"]
                },
                "model.test_project.experimental_model": {
                    "name": "experimental_model",
                    "resource_type": "model",
                    "original_file_path": "models/experimental_model.sql",
                    "tags": ["experimental", "test"]
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = filter_manifest
        
        # Filter by core tag
        results = service.search_models("", {"tags": ["core"]})
        
        assert len(results) == 1
        assert results[0].name == "core_model"
    
    def test_filter_by_layer(self):
        """Test filtering models by layer based on path"""
        filter_manifest = {
            "nodes": {
                "model.test_project.stg_customers": {
                    "name": "stg_customers",
                    "resource_type": "model",
                    "original_file_path": "models/staging/stg_customers.sql"
                },
                "model.test_project.dim_customers": {
                    "name": "dim_customers",
                    "resource_type": "model",
                    "original_file_path": "models/marts/dim_customers.sql"
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = filter_manifest
        
        # Filter by staging layer
        results = service.search_models("", {"layer": "staging"})
        
        assert len(results) == 1
        assert results[0].name == "stg_customers"
    
    def test_combined_search_and_filter(self):
        """Test combining search query with filters"""
        combined_manifest = {
            "nodes": {
                "model.test_project.stg_customer_orders": {
                    "name": "stg_customer_orders",
                    "resource_type": "model",
                    "original_file_path": "models/staging/stg_customer_orders.sql",
                    "description": "Staging customer orders",
                    "config": {"materialized": "view"},
                    "tags": ["staging"]
                },
                "model.test_project.customer_metrics": {
                    "name": "customer_metrics",
                    "resource_type": "model",
                    "original_file_path": "models/marts/customer_metrics.sql",
                    "description": "Customer analytics metrics",
                    "config": {"materialized": "table"},
                    "tags": ["mart"]
                }
            }
        }
        
        service = ModelMetadataService()
        service.manifest = combined_manifest
        
        # Search for "customer" with staging filter
        results = service.search_models("customer", {"layer": "staging"})
        
        assert len(results) == 1
        assert results[0].name == "stg_customer_orders"
    
    def test_empty_search_returns_all(self, mock_manifest):
        """Test that empty search returns all models"""
        service = ModelMetadataService()
        service.manifest = mock_manifest
        
        results = service.search_models("")
        
        assert len(results) == 1  # All models from mock_manifest
        assert results[0].name == "test_model"
    
    def test_no_matches_returns_empty(self, mock_manifest):
        """Test that search with no matches returns empty list"""
        service = ModelMetadataService()
        service.manifest = mock_manifest
        
        results = service.search_models("nonexistent_search_term")
        
        assert len(results) == 0


class TestAPIEndpointDataFormats:
    """Test API endpoints return correct data formats"""
    
    def test_list_models_endpoint_format(self, mcp_server_with_mocks):
        """Test /models endpoint returns correct data format"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "models" in data
        assert "total_count" in data
        assert "offset" in data
        assert "limit" in data
        
        # Verify model data format
        models = data["models"]
        assert len(models) == 1
        
        model = models[0]
        required_fields = ["name", "path", "description", "materialization", 
                          "tags", "depends_on", "referenced_by", "columns"]
        for field in required_fields:
            assert field in model
        
        # Verify column format
        columns = model["columns"]
        if columns:
            column = columns[0]
            column_fields = ["name", "data_type", "description", "tests"]
            for field in column_fields:
                assert field in column
    
    def test_get_model_details_endpoint_format(self, mcp_server_with_mocks):
        """Test /models/{model_name} endpoint returns correct data format"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/models/test_model")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        required_fields = ["name", "path", "description", "columns", 
                          "depends_on", "referenced_by", "materialization", "tags"]
        for field in required_fields:
            assert field in data
        
        # Verify data types
        assert isinstance(data["name"], str)
        assert isinstance(data["columns"], list)
        assert isinstance(data["depends_on"], list)
        assert isinstance(data["referenced_by"], list)
        assert isinstance(data["tags"], list)
    
    def test_get_model_lineage_endpoint_format(self, mcp_server_with_mocks):
        """Test /lineage/{model_name} endpoint returns correct data format"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/lineage/test_model")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "model" in data
        assert "upstream" in data
        assert "downstream" in data
        
        # Verify data types
        assert isinstance(data["model"], str)
        assert isinstance(data["upstream"], list)
        assert isinstance(data["downstream"], list)
        
        assert data["model"] == "test_model"
    
    def test_search_models_endpoint_format(self, mcp_server_with_mocks):
        """Test /search/models endpoint returns correct data format"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/search/models?q=test")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        required_fields = ["results", "query", "total_count", "offset", 
                          "limit", "filters_applied"]
        for field in required_fields:
            assert field in data
        
        # Verify search result format
        results = data["results"]
        if results:
            result = results[0]
            result_fields = ["name", "path", "description", "materialization", 
                           "tags", "column_count", "dependency_count"]
            for field in result_fields:
                assert field in result
    
    def test_list_models_with_pagination(self, mcp_server_with_mocks):
        """Test /models endpoint with pagination parameters"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/models?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert isinstance(data["total_count"], int)
    
    def test_list_models_with_filters(self, mcp_server_with_mocks):
        """Test /models endpoint with filter parameters"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/models?materialization=table&layer=staging&tags=test,core")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return valid response structure even with filters
        assert "models" in data
        assert "total_count" in data
    
    def test_model_not_found_error_format(self, mcp_server_with_mocks):
        """Test error format for non-existent model"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.get("/models/nonexistent_model")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert "nonexistent_model" in data["detail"]
    
    def test_refresh_endpoint_format(self, mcp_server_with_mocks):
        """Test /refresh endpoint returns correct format"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            response = client.post("/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "message" in data
        assert data["status"] == "success"


class TestModelExplorationIntegration:
    """Integration tests for model exploration features"""
    
    def test_end_to_end_model_exploration(self, mcp_server_with_mocks):
        """Test complete model exploration workflow"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            # 1. List all models
            list_response = client.get("/models")
            assert list_response.status_code == 200
            models = list_response.json()["models"]
            assert len(models) > 0
            
            model_name = models[0]["name"]
            
            # 2. Get specific model details
            detail_response = client.get(f"/models/{model_name}")
            assert detail_response.status_code == 200
            model_detail = detail_response.json()
            assert model_detail["name"] == model_name
            
            # 3. Get model lineage
            lineage_response = client.get(f"/lineage/{model_name}")
            assert lineage_response.status_code == 200
            lineage = lineage_response.json()
            assert lineage["model"] == model_name
            
            # 4. Search for the model
            search_response = client.get(f"/search/models?q={model_name}")
            assert search_response.status_code == 200
            search_results = search_response.json()["results"]
            assert any(result["name"] == model_name for result in search_results)
    
    def test_manifest_reload_affects_endpoints(self, mcp_server_with_mocks):
        """Test that manifest reload affects all endpoints"""
        server = mcp_server_with_mocks
        
        with TestClient(server.app) as client:
            # Initial state
            initial_response = client.get("/models")
            initial_count = initial_response.json()["total_count"]
            
            # Refresh manifest
            refresh_response = client.post("/refresh")
            assert refresh_response.status_code == 200
            
            # Verify endpoints still work after refresh
            post_refresh_response = client.get("/models")
            assert post_refresh_response.status_code == 200
            
            # Count should be the same (using same mock data)
            post_refresh_count = post_refresh_response.json()["total_count"]
            assert post_refresh_count == initial_count