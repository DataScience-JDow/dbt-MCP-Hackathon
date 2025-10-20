"""
Integration tests with real dbt project data
Tests for task 7.1: Integrate with existing dbt project data
"""
import pytest
from pathlib import Path

from dbt_mcp_hackathon_project.backend.model_service import ModelMetadataService
from dbt_mcp_hackathon_project.config import Config


class TestRealProjectIntegration:
    """Test integration with actual jaffle shop and flower shop data"""
    
    def test_model_exploration_with_real_data(self):
        """Verify model exploration works with all existing models"""
        config = Config()
        service = ModelMetadataService(config)
        
        # Should be able to load the real manifest
        assert service.manifest is not None, "Failed to load dbt manifest - run 'dbt compile' first"
        
        # Get all models
        models = service.get_all_models()
        
        # Should have models from both jaffle shop and flower shop
        assert len(models) > 0, "No models found in dbt project"
        
        # Check for expected model patterns
        model_names = [model.name for model in models]
        
        # Should have staging models for both businesses
        jaffle_staging = [name for name in model_names if name.startswith('stg_jaffle')]
        flower_staging = [name for name in model_names if name.startswith('stg_flower_shop')]
        
        assert len(jaffle_staging) > 0, "No jaffle shop staging models found"
        assert len(flower_staging) > 0, "No flower shop staging models found"
        
        # Should have intermediate models
        intermediate_models = [name for name in model_names if name.startswith('int_')]
        assert len(intermediate_models) > 0, "No intermediate models found"
        
        # Should have mart models
        mart_models = [name for name in model_names if name.startswith(('fct_', 'dim_', 'agg_'))]
        assert len(mart_models) > 0, "No mart models found"
    
    def test_cross_business_model_references(self):
        """Test that cross-business model creation is properly handled"""
        config = Config()
        service = ModelMetadataService(config)
        
        models = service.get_all_models()
        model_names = [model.name for model in models]
        
        # Look for cross-business models
        cross_business_models = [name for name in model_names if 'cross_business' in name]
        
        if cross_business_models:
            # If cross-business models exist, verify they reference both businesses
            for model_name in cross_business_models:
                model = service.get_model_by_name(model_name)
                assert model is not None
                
                # Check dependencies include models from both businesses
                deps = service.get_model_dependencies(model_name)
                all_deps = deps['upstream'] + deps['downstream']
                
                has_jaffle_ref = any('jaffle' in dep for dep in all_deps)
                has_flower_ref = any('flower' in dep for dep in all_deps)
                
                # Cross-business models should reference both or be referenced by both
                assert has_jaffle_ref or has_flower_ref, f"Cross-business model {model_name} should reference both businesses"
    
    def test_model_search_with_real_data(self):
        """Test model search functionality with real project data"""
        config = Config()
        service = ModelMetadataService(config)
        
        # Search for jaffle-related models
        jaffle_results = service.search_models("jaffle")
        assert len(jaffle_results) > 0, "No jaffle models found in search"
        
        # All results should contain 'jaffle' in name, description, or path
        for model in jaffle_results:
            has_jaffle = (
                'jaffle' in model.name.lower() or
                (model.description and 'jaffle' in model.description.lower()) or
                (model.path and 'jaffle' in model.path.lower())
            )
            assert has_jaffle, f"Model {model.name} doesn't contain 'jaffle' reference"
        
        # Search for flower-related models
        flower_results = service.search_models("flower")
        assert len(flower_results) > 0, "No flower models found in search"
        
        # All results should contain 'flower' in name, description, or path
        for model in flower_results:
            has_flower = (
                'flower' in model.name.lower() or
                (model.description and 'flower' in model.description.lower()) or
                (model.path and 'flower' in model.path.lower())
            )
            assert has_flower, f"Model {model.name} doesn't contain 'flower' reference"
    
    def test_layer_filtering_with_real_data(self):
        """Test layer-based filtering with real project structure"""
        config = Config()
        service = ModelMetadataService(config)
        
        # Test staging layer filtering
        staging_models = service.search_models("", {"layer": "staging"})
        assert len(staging_models) > 0, "No staging models found"
        
        for model in staging_models:
            assert model.path and 'staging' in model.path.lower(), f"Model {model.name} not in staging layer"
        
        # Test marts layer filtering
        marts_models = service.search_models("", {"layer": "marts"})
        assert len(marts_models) > 0, "No marts models found"
        
        for model in marts_models:
            assert model.path and 'marts' in model.path.lower(), f"Model {model.name} not in marts layer"
        
        # Test intermediate layer filtering
        intermediate_models = service.search_models("", {"layer": "intermediate"})
        assert len(intermediate_models) > 0, "No intermediate models found"
        
        for model in intermediate_models:
            assert model.path and 'intermediate' in model.path.lower(), f"Model {model.name} not in intermediate layer"
    
    def test_model_dependencies_with_real_data(self):
        """Test dependency tracking with real project models"""
        config = Config()
        service = ModelMetadataService(config)
        
        models = service.get_all_models()
        
        # Find a mart model to test dependencies
        mart_models = [m for m in models if m.path and 'marts' in m.path.lower()]
        assert len(mart_models) > 0, "No mart models found for dependency testing"
        
        # Test dependencies for first mart model
        mart_model = mart_models[0]
        deps = service.get_model_dependencies(mart_model.name)
        
        # Mart models should typically have upstream dependencies
        assert len(deps['upstream']) > 0, f"Mart model {mart_model.name} should have upstream dependencies"
        
        # Verify upstream models exist
        all_model_names = [m.name for m in models]
        for upstream in deps['upstream']:
            assert upstream in all_model_names, f"Upstream dependency {upstream} not found in project"
    
    def test_column_metadata_extraction(self):
        """Test that column metadata is properly extracted from real models"""
        config = Config()
        service = ModelMetadataService(config)
        
        models = service.get_all_models()
        
        # Find models with column definitions
        models_with_columns = [m for m in models if len(m.columns) > 0]
        
        if models_with_columns:
            # Test first model with columns
            model = models_with_columns[0]
            
            for column in model.columns:
                # Column should have at least a name
                assert column.name, f"Column in model {model.name} missing name"
                assert isinstance(column.name, str), f"Column name should be string in model {model.name}"
                
                # Data type should be present (even if 'unknown')
                assert column.data_type is not None, f"Column {column.name} missing data type"
                
                # Tests should be a list
                assert isinstance(column.tests, list), f"Column {column.name} tests should be a list"
    
    def test_materialization_types_in_real_project(self):
        """Test that different materialization types are properly detected"""
        config = Config()
        service = ModelMetadataService(config)
        
        models = service.get_all_models()
        
        # Collect all materialization types
        materializations = set(model.materialization for model in models)
        
        # Should have at least view and table materializations
        assert len(materializations) > 0, "No materialization types found"
        
        # Common dbt materializations
        expected_materializations = {'view', 'table', 'incremental', 'ephemeral'}
        found_materializations = materializations.intersection(expected_materializations)
        
        assert len(found_materializations) > 0, f"No standard materializations found. Found: {materializations}"
    
    def test_model_tags_in_real_project(self):
        """Test that model tags are properly extracted"""
        config = Config()
        service = ModelMetadataService(config)
        
        models = service.get_all_models()
        
        # Find models with tags
        models_with_tags = [m for m in models if len(m.tags) > 0]
        
        if models_with_tags:
            # Verify tag structure
            for model in models_with_tags:
                assert isinstance(model.tags, list), f"Model {model.name} tags should be a list"
                for tag in model.tags:
                    assert isinstance(tag, str), f"Tag in model {model.name} should be string"
                    assert len(tag) > 0, f"Empty tag found in model {model.name}"


class TestModelGenerationContext:
    """Test that model generation can reference existing tables and models"""
    
    def test_available_source_tables(self):
        """Test that source tables are available for model generation context"""
        config = Config()
        service = ModelMetadataService(config)
        
        # Check if we can identify source tables from the manifest
        if service.manifest:
            sources = service.manifest.get('sources', {})
            
            # Should have jaffle and flower shop sources
            source_names = []
            for source_id, source in sources.items():
                if source.get('resource_type') == 'source':
                    source_names.append(source.get('name', ''))
            
            # Look for expected source tables
            expected_tables = ['raw_customers', 'raw_orders', 'raw_flowers', 'raw_flower_orders']
            
            # At least some expected tables should be available
            # (This test verifies the data is accessible for model generation)
            assert len(source_names) > 0 or len(service.get_all_models()) > 0, \
                "No sources or models available for model generation context"
    
    def test_model_references_for_generation(self):
        """Test that existing models can be referenced in new model generation"""
        config = Config()
        service = ModelMetadataService(config)
        
        models = service.get_all_models()
        
        # Should have staging models that can be referenced
        staging_models = [m for m in models if 'stg_' in m.name]
        assert len(staging_models) > 0, "No staging models available for referencing"
        
        # Should have models from both businesses for cross-business joins
        jaffle_models = [m for m in models if 'jaffle' in m.name.lower()]
        flower_models = [m for m in models if 'flower' in m.name.lower()]
        
        assert len(jaffle_models) > 0, "No jaffle models available for cross-business references"
        assert len(flower_models) > 0, "No flower models available for cross-business references"
        
        # This confirms that model generation can reference both business domains
        print(f"Available for cross-business model generation:")
        print(f"  Jaffle models: {len(jaffle_models)}")
        print(f"  Flower models: {len(flower_models)}")
        print(f"  Total staging models: {len(staging_models)}")