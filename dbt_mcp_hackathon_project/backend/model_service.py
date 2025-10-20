"""
Model metadata extraction service for dbt MCP Hackathon Project
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..shared.models import ModelMetadata, ColumnInfo
from ..config import Config

logger = logging.getLogger(__name__)

class ModelMetadataService:
    """Service for extracting and managing dbt model metadata"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.manifest: Optional[Dict[str, Any]] = None
        self._load_manifest()
    
    def _load_manifest(self) -> None:
        """Load dbt manifest.json file"""
        try:
            manifest_path = self.config.DBT_PROJECT_PATH / "target" / "manifest.json"
            
            if not manifest_path.exists():
                logger.warning(f"dbt manifest not found at {manifest_path}. Run 'dbt compile' first.")
                return
            
            with open(manifest_path, 'r') as f:
                self.manifest = json.load(f)
            
            logger.info(f"Loaded dbt manifest with {len(self.manifest.get('nodes', {}))} nodes")
        except Exception as e:
            logger.error(f"Failed to load dbt manifest: {e}")
            self.manifest = None
    
    def reload_manifest(self) -> bool:
        """Reload the dbt manifest from disk"""
        try:
            self._load_manifest()
            return self.manifest is not None
        except Exception as e:
            logger.error(f"Failed to reload manifest: {e}")
            return False
    
    def get_manifest_info(self) -> Dict[str, Any]:
        """Get information about the current manifest"""
        if not self.manifest:
            return {
                "loaded": False,
                "message": "No manifest loaded. Run 'dbt compile' to generate manifest.json"
            }
        
        nodes = self.manifest.get("nodes", {})
        model_nodes = {k: v for k, v in nodes.items() if v.get("resource_type") == "model"}
        
        # Count models with and without column info
        models_with_columns = 0
        total_models = len(model_nodes)
        
        for node in model_nodes.values():
            if node.get("columns"):
                models_with_columns += 1
        
        return {
            "loaded": True,
            "total_models": total_models,
            "models_with_columns": models_with_columns,
            "models_without_columns": total_models - models_with_columns,
            "manifest_metadata": self.manifest.get("metadata", {}),
            "message": f"Manifest loaded with {total_models} models. {models_with_columns} have column definitions."
        }
    
    def get_all_models(self) -> List[ModelMetadata]:
        """Get metadata for all dbt models"""
        if not self.manifest:
            return []
        
        models = []
        nodes = self.manifest.get("nodes", {})
        
        for node_id, node in nodes.items():
            if node.get("resource_type") == "model":
                model_metadata = self._extract_model_metadata(node_id, node, nodes)
                models.append(model_metadata)
        
        return models
    
    def get_model_by_name(self, model_name: str) -> Optional[ModelMetadata]:
        """Get metadata for a specific model by name"""
        if not self.manifest:
            return None
        
        nodes = self.manifest.get("nodes", {})
        
        for node_id, node in nodes.items():
            if (node.get("resource_type") == "model" and 
                node.get("name") == model_name):
                return self._extract_model_metadata(node_id, node, nodes)
        
        return None
    
    def get_model_dependencies(self, model_name: str) -> Dict[str, List[str]]:
        """Get upstream and downstream dependencies for a model"""
        if not self.manifest:
            return {"upstream": [], "downstream": []}
        
        nodes = self.manifest.get("nodes", {})
        target_node_id = None
        
        # Find the target model's node ID
        for node_id, node in nodes.items():
            if (node.get("resource_type") == "model" and 
                node.get("name") == model_name):
                target_node_id = node_id
                break
        
        if not target_node_id:
            return {"upstream": [], "downstream": []}
        
        # Get upstream dependencies (what this model depends on)
        target_node = nodes[target_node_id]
        upstream = []
        for dep_node_id in target_node.get("depends_on", {}).get("nodes", []):
            if dep_node_id in nodes:
                dep_node = nodes[dep_node_id]
                if dep_node.get("resource_type") == "model":
                    upstream.append(dep_node.get("name"))
        
        # Get downstream dependencies (what depends on this model)
        downstream = []
        for node_id, node in nodes.items():
            if node.get("resource_type") == "model" and node_id != target_node_id:
                deps = node.get("depends_on", {}).get("nodes", [])
                if target_node_id in deps:
                    downstream.append(node.get("name"))
        
        return {"upstream": upstream, "downstream": downstream}
    
    def _infer_columns_from_compiled_sql(self, node: Dict[str, Any]) -> List[ColumnInfo]:
        """Try to infer column information from compiled SQL or database introspection"""
        columns = []
        
        try:
            # Try to get compiled SQL
            compiled_sql = node.get("compiled_sql") or node.get("raw_sql")
            
            if compiled_sql:
                # Basic SQL parsing to extract SELECT columns
                # This is a simple heuristic - not perfect but better than nothing
                columns = self._parse_select_columns(compiled_sql)
            
            # If we still don't have columns and the model exists in the database,
            # we could potentially introspect the database schema here
            # For now, we'll just return what we found from SQL parsing
            
        except Exception as e:
            logger.debug(f"Failed to infer columns from SQL: {e}")
        
        return columns
    
    def _parse_select_columns(self, sql: str) -> List[ColumnInfo]:
        """Basic parsing of SELECT statement to extract column names"""
        columns = []
        
        try:
            # This is a very basic parser - just looks for common patterns
            # In a production system, you'd want to use a proper SQL parser
            
            sql_upper = sql.upper()
            
            # Find SELECT clause
            select_start = sql_upper.find("SELECT")
            if select_start == -1:
                return columns
            
            # Find FROM clause
            from_start = sql_upper.find("FROM", select_start)
            if from_start == -1:
                return columns
            
            # Extract the SELECT clause
            select_clause = sql[select_start + 6:from_start].strip()
            
            # Split by comma and clean up
            column_parts = [part.strip() for part in select_clause.split(",")]
            
            for part in column_parts:
                if not part:
                    continue
                
                # Handle aliases (AS keyword or space-separated)
                if " AS " in part.upper():
                    column_name = part.upper().split(" AS ")[1].strip()
                elif " " in part and not any(func in part.upper() for func in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("]):
                    # Simple alias without AS
                    parts = part.split()
                    column_name = parts[-1].strip()
                else:
                    # No alias, use the expression as column name
                    column_name = part.strip()
                
                # Clean up column name
                column_name = column_name.replace('"', '').replace("'", "").replace("`", "")
                
                if column_name and column_name != "*":
                    columns.append(ColumnInfo(
                        name=column_name,
                        data_type="unknown",
                        description=f"Inferred from SQL (run dbt docs generate for accurate schema)"
                    ))
            
        except Exception as e:
            logger.debug(f"Failed to parse SELECT columns: {e}")
        
        return columns
    
    def _extract_model_metadata(self, node_id: str, node: Dict[str, Any], 
                               all_nodes: Dict[str, Any]) -> ModelMetadata:
        """Extract ModelMetadata from a dbt manifest node"""
        # Extract column information
        columns = []
        
        # Try to get columns from the manifest first
        manifest_columns = node.get("columns", {})
        
        if manifest_columns:
            # Use manifest column information (from schema.yml files)
            for col_name, col_info in manifest_columns.items():
                column = ColumnInfo(
                    name=col_name,
                    data_type=col_info.get("data_type", "unknown"),
                    description=col_info.get("description"),
                    tests=[test.get("test_metadata", {}).get("name", str(test)) 
                          if isinstance(test, dict) else str(test)
                          for test in col_info.get("tests", [])]
                )
                columns.append(column)
        else:
            # If no manifest columns, try to get from compiled SQL or database
            # This is a fallback for when schema.yml doesn't define columns
            columns = self._infer_columns_from_compiled_sql(node)
            
            # If still no columns, log a warning
            if not columns:
                logger.debug(f"No column information available for model {node.get('name')}. "
                           f"Consider adding column definitions to schema.yml or running dbt docs generate.")
        
        # Extract dependencies
        depends_on = []
        for dep_node_id in node.get("depends_on", {}).get("nodes", []):
            if dep_node_id in all_nodes:
                dep_node = all_nodes[dep_node_id]
                if dep_node.get("resource_type") == "model":
                    depends_on.append(dep_node.get("name"))
        
        # Find what references this model
        referenced_by = []
        for other_node_id, other_node in all_nodes.items():
            if (other_node.get("resource_type") == "model" and 
                other_node_id != node_id):
                deps = other_node.get("depends_on", {}).get("nodes", [])
                if node_id in deps:
                    referenced_by.append(other_node.get("name"))
        
        return ModelMetadata(
            name=node.get("name"),
            path=node.get("original_file_path"),
            description=node.get("description"),
            columns=columns,
            depends_on=depends_on,
            referenced_by=referenced_by,
            materialization=node.get("config", {}).get("materialized", "view"),
            tags=node.get("tags", [])
        )
    
    def search_models(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[ModelMetadata]:
        """Search models by name, description, or tags with optional filters"""
        all_models = self.get_all_models()
        
        if not query and not filters:
            return all_models
        
        filtered_models = []
        query_lower = query.lower() if query else ""
        
        for model in all_models:
            # Text search
            if query:
                matches_query = (
                    query_lower in model.name.lower() or
                    (model.description and query_lower in model.description.lower()) or
                    any(query_lower in tag.lower() for tag in model.tags)
                )
                if not matches_query:
                    continue
            
            # Apply filters
            if filters:
                # Filter by materialization
                if ("materialization" in filters and 
                    model.materialization != filters["materialization"]):
                    continue
                
                # Filter by tags
                if ("tags" in filters and filters["tags"]):
                    required_tags = filters["tags"]
                    if not any(tag in model.tags for tag in required_tags):
                        continue
                
                # Filter by layer (based on path)
                if ("layer" in filters and filters["layer"]):
                    layer = filters["layer"]
                    if not self._model_matches_layer(model, layer):
                        continue
            
            filtered_models.append(model)
        
        return filtered_models
    
    def _model_matches_layer(self, model: ModelMetadata, layer: str) -> bool:
        """Check if a model belongs to a specific layer based on its path"""
        if not model.path:
            return False
        
        path_lower = model.path.lower()
        layer_lower = layer.lower()
        
        # Common dbt layer patterns
        layer_patterns = {
            "staging": ["staging", "stg_"],
            "intermediate": ["intermediate", "int_"],
            "marts": ["marts", "mart_", "dim_", "fct_"],
            "raw": ["raw", "source"]
        }
        
        if layer_lower in layer_patterns:
            patterns = layer_patterns[layer_lower]
            return any(pattern in path_lower for pattern in patterns)
        
        # Direct layer name match
        return layer_lower in path_lower