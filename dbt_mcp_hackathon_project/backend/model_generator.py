"""
Model file creation and management service for dbt MCP Hackathon Project
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..config import Config
from ..shared.models import ModelGenerationRequest
from .ai_service import SQLGenerationResult

logger = logging.getLogger(__name__)

@dataclass
class ModelFileResult:
    """Result of model file creation"""
    model_path: Path
    schema_path: Optional[Path]
    success: bool
    message: str
    conflicts: List[str] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []

@dataclass
class ModelValidationResult:
    """Result of model validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

class ModelFileManager:
    """Service for creating and managing dbt model files"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.models_dir = self.config.DBT_PROJECT_PATH / "models"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.models_dir,
            self.models_dir / "staging",
            self.models_dir / "intermediate", 
            self.models_dir / "marts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def create_model_from_sql_result(self, sql_result: SQLGenerationResult) -> ModelFileResult:
        """Create a dbt model file from SQL generation result"""
        try:
            # Determine model path
            model_path = self._determine_model_path(sql_result.model_name)
            
            # Check for conflicts
            conflicts = self._check_conflicts(model_path)
            
            if conflicts and not self._should_overwrite(conflicts):
                return ModelFileResult(
                    model_path=model_path,
                    schema_path=None,
                    success=False,
                    message=f"Model file conflicts detected: {', '.join(conflicts)}",
                    conflicts=conflicts
                )
            
            # Create model file
            self._write_model_file(model_path, sql_result)
            
            # Create or update schema.yml
            schema_path = None
            if sql_result.description or self._should_create_schema(sql_result):
                schema_path = self._create_or_update_schema(sql_result)
            
            return ModelFileResult(
                model_path=model_path,
                schema_path=schema_path,
                success=True,
                message=f"Successfully created model: {sql_result.model_name}",
                conflicts=conflicts
            )
            
        except Exception as e:
            logger.error(f"Failed to create model file: {e}")
            return ModelFileResult(
                model_path=Path(""),
                schema_path=None,
                success=False,
                message=f"Failed to create model: {str(e)}"
            )
    
    def _determine_model_path(self, model_name: str) -> Path:
        """Determine the appropriate path for a model based on naming conventions"""
        # Determine layer based on model name prefix
        if model_name.startswith(('stg_', 'staging_')):
            layer_dir = self.models_dir / "staging"
        elif model_name.startswith(('int_', 'intermediate_')):
            layer_dir = self.models_dir / "intermediate"
        elif model_name.startswith(('dim_', 'fct_', 'mart_')):
            layer_dir = self.models_dir / "marts"
        else:
            # Default to intermediate for generated models
            layer_dir = self.models_dir / "intermediate"
        
        return layer_dir / f"{model_name}.sql"
    
    def _check_conflicts(self, model_path: Path) -> List[str]:
        """Check for potential conflicts with existing files"""
        conflicts = []
        
        if model_path.exists():
            conflicts.append(f"Model file already exists: {model_path}")
        
        # Check for similar named files
        model_dir = model_path.parent
        model_stem = model_path.stem
        
        for existing_file in model_dir.glob("*.sql"):
            if existing_file.stem.lower() == model_stem.lower() and existing_file != model_path:
                conflicts.append(f"Similar model name exists: {existing_file}")
        
        return conflicts
    
    def _should_overwrite(self, conflicts: List[str]) -> bool:
        """Determine if conflicts should be overwritten (for now, always False)"""
        # In a real implementation, this might prompt the user or check configuration
        return False
    
    def _write_model_file(self, model_path: Path, sql_result: SQLGenerationResult):
        """Write the SQL model file"""
        # Ensure directory exists
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare file content
        content_parts = []
        
        # Add file header comment
        content_parts.extend([
            f"-- Model: {sql_result.model_name}",
            f"-- Generated by dbt MCP Hackathon Project"
        ])
        
        if sql_result.description:
            content_parts.append(f"-- Description: {sql_result.description}")
        
        if sql_result.reasoning:
            content_parts.append(f"-- Reasoning: {sql_result.reasoning}")
        
        content_parts.extend([
            "",
            sql_result.sql
        ])
        
        # Write file
        with open(model_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_parts))
        
        logger.info(f"Created model file: {model_path}")
    
    def _should_create_schema(self, sql_result: SQLGenerationResult) -> bool:
        """Determine if a schema.yml entry should be created"""
        # Create schema if we have description or non-default materialization
        return (sql_result.description is not None or 
                sql_result.materialization != "view")
    
    def _create_or_update_schema(self, sql_result: SQLGenerationResult) -> Optional[Path]:
        """Create or update schema.yml file for the model"""
        try:
            model_dir = self._determine_model_path(sql_result.model_name).parent
            schema_path = model_dir / "schema.yml"
            
            # Load existing schema or create new
            schema_data = self._load_or_create_schema(schema_path)
            
            # Add or update model entry
            self._add_model_to_schema(schema_data, sql_result)
            
            # Write schema file
            with open(schema_path, 'w', encoding='utf-8') as f:
                yaml.dump(schema_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Updated schema file: {schema_path}")
            return schema_path
            
        except Exception as e:
            logger.error(f"Failed to create/update schema: {e}")
            return None
    
    def _load_or_create_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load existing schema.yml or create new structure"""
        if schema_path.exists():
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load existing schema, creating new: {e}")
        
        return {
            "version": 2,
            "models": []
        }
    
    def _add_model_to_schema(self, schema_data: Dict[str, Any], sql_result: SQLGenerationResult):
        """Add model entry to schema data"""
        # Ensure models list exists
        if "models" not in schema_data:
            schema_data["models"] = []
        
        # Check if model already exists
        existing_model = None
        for model in schema_data["models"]:
            if model.get("name") == sql_result.model_name:
                existing_model = model
                break
        
        # Create model entry
        model_entry = {
            "name": sql_result.model_name
        }
        
        if sql_result.description:
            model_entry["description"] = sql_result.description
        
        # Add materialization config if not default
        if sql_result.materialization != "view":
            model_entry["config"] = {
                "materialized": sql_result.materialization
            }
        
        # Add or update model in schema
        if existing_model:
            # Update existing entry
            existing_model.update(model_entry)
        else:
            # Add new entry
            schema_data["models"].append(model_entry)
    
    def validate_model_file(self, model_path: Path) -> ModelValidationResult:
        """Validate a model file for common issues"""
        result = ModelValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        
        try:
            if not model_path.exists():
                result.errors.append(f"Model file does not exist: {model_path}")
                result.is_valid = False
                return result
            
            # Read file content
            with open(model_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic SQL validation
            self._validate_sql_content(content, result)
            
            # dbt-specific validation
            self._validate_dbt_syntax(content, result)
            
            # File naming validation
            self._validate_file_naming(model_path, result)
            
        except Exception as e:
            result.errors.append(f"Failed to validate model: {str(e)}")
            result.is_valid = False
        
        return result
    
    def _validate_sql_content(self, content: str, result: ModelValidationResult):
        """Validate basic SQL content"""
        content_lower = content.lower()
        
        # Check for SELECT statement
        if "select" not in content_lower:
            result.errors.append("Model must contain a SELECT statement")
            result.is_valid = False
        
        # Check for common SQL issues
        if content.count('(') != content.count(')'):
            result.errors.append("Unmatched parentheses in SQL")
            result.is_valid = False
        
        # Check for trailing commas
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.endswith(','):
                # Check if next non-empty line starts with FROM, WHERE, etc.
                for j in range(i, len(lines)):
                    next_line = lines[j].strip().lower()
                    if next_line:
                        if next_line.startswith(('from', 'where', 'group', 'order', 'having', ')')):
                            result.warnings.append(f"Trailing comma on line {i} may cause issues")
                        break
    
    def _validate_dbt_syntax(self, content: str, result: ModelValidationResult):
        """Validate dbt-specific syntax"""
        # Check for proper ref usage
        if " from " in content.lower() and "{{ ref(" not in content and "{{ source(" not in content:
            result.suggestions.append("Consider using {{ ref('model_name') }} for model references")
        
        # Check for config block
        if "materialized" in content and "{{ config(" not in content:
            result.suggestions.append("Use {{ config() }} block for model configuration")
        
        # Check for proper Jinja syntax
        jinja_patterns = [r'\{\{[^}]*\}\}', r'\{%[^%]*%\}']
        for pattern in jinja_patterns:
            import re
            matches = re.findall(pattern, content)
            for match in matches:
                if match.count('{') != match.count('}'):
                    result.errors.append(f"Invalid Jinja syntax: {match}")
                    result.is_valid = False
    
    def _validate_file_naming(self, model_path: Path, result: ModelValidationResult):
        """Validate file naming conventions"""
        model_name = model_path.stem
        
        # Check for valid characters
        if not model_name.replace('_', '').replace('-', '').isalnum():
            result.warnings.append("Model name should only contain letters, numbers, and underscores")
        
        # Check for naming conventions
        if model_name.startswith('stg_') and 'staging' not in str(model_path):
            result.suggestions.append("Staging models (stg_*) should be in staging directory")
        elif model_name.startswith('int_') and 'intermediate' not in str(model_path):
            result.suggestions.append("Intermediate models (int_*) should be in intermediate directory")
        elif (model_name.startswith(('dim_', 'fct_', 'mart_')) and 
              'marts' not in str(model_path)):
            result.suggestions.append("Mart models should be in marts directory")
    
    def delete_model(self, model_name: str) -> bool:
        """Delete a model and its schema entry"""
        try:
            # Find model file
            model_path = self._find_model_file(model_name)
            if not model_path:
                logger.warning(f"Model file not found: {model_name}")
                return False
            
            # Delete model file
            model_path.unlink()
            logger.info(f"Deleted model file: {model_path}")
            
            # Remove from schema.yml
            self._remove_from_schema(model_name, model_path.parent)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return False
    
    def _find_model_file(self, model_name: str) -> Optional[Path]:
        """Find model file by name"""
        # Search in all model directories
        search_dirs = [
            self.models_dir,
            self.models_dir / "staging",
            self.models_dir / "intermediate",
            self.models_dir / "marts"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                model_path = search_dir / f"{model_name}.sql"
                if model_path.exists():
                    return model_path
        
        return None
    
    def _remove_from_schema(self, model_name: str, model_dir: Path):
        """Remove model entry from schema.yml"""
        try:
            schema_path = model_dir / "schema.yml"
            if not schema_path.exists():
                return
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = yaml.safe_load(f) or {}
            
            if "models" in schema_data:
                schema_data["models"] = [
                    model for model in schema_data["models"]
                    if model.get("name") != model_name
                ]
                
                # Write back if there are still models, otherwise delete empty schema
                if schema_data["models"]:
                    with open(schema_path, 'w', encoding='utf-8') as f:
                        yaml.dump(schema_data, f, default_flow_style=False, sort_keys=False)
                else:
                    schema_path.unlink()
                    logger.info(f"Removed empty schema file: {schema_path}")
            
        except Exception as e:
            logger.error(f"Failed to remove model from schema: {e}")
    
    def list_generated_models(self) -> List[Dict[str, Any]]:
        """List all models that appear to be generated by dbt MCP Hackathon Project"""
        generated_models = []
        
        # Search in all model directories
        search_dirs = [
            self.models_dir / "staging",
            self.models_dir / "intermediate",
            self.models_dir / "marts"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for model_file in search_dir.glob("*.sql"):
                    try:
                        with open(model_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check if file was generated by dbt MCP Hackathon Project
                        if "Generated by dbt MCP Hackathon Project" in content:
                            model_info = {
                                "name": model_file.stem,
                                "path": str(model_file),
                                "layer": search_dir.name,
                                "size": model_file.stat().st_size,
                                "modified": model_file.stat().st_mtime
                            }
                            generated_models.append(model_info)
                    
                    except Exception as e:
                        logger.warning(f"Failed to read model file {model_file}: {e}")
        
        return generated_models