"""
dbt compilation and execution service for dbt MCP Hackathon Project
"""
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..config import Config

logger = logging.getLogger(__name__)

@dataclass
class CompilationResult:
    """Result of dbt compilation"""
    success: bool
    model_name: str
    compiled_sql: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    compilation_time: Optional[float] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

@dataclass
class ExecutionResult:
    """Result of dbt model execution"""
    success: bool
    model_name: str
    rows_affected: Optional[int] = None
    execution_time: Optional[float] = None
    errors: List[str] = None
    warnings: List[str] = None
    output_path: Optional[str] = None
    preview_data: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

@dataclass
class ValidationResult:
    """Result of SQL validation"""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []

class DBTCompilationService:
    """Service for dbt compilation and execution operations"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.dbt_project_path = self.config.DBT_PROJECT_PATH
        
    def compile_model(self, model_name: str) -> CompilationResult:
        """Compile a specific dbt model"""
        start_time = datetime.now()
        
        try:
            # Run dbt compile for specific model
            cmd = [
                "dbt", "compile",
                "--select", model_name,
                "--project-dir", str(self.dbt_project_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.dbt_project_path
            )
            
            compilation_time = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                # Compilation successful - get compiled SQL
                compiled_sql = self._get_compiled_sql(model_name)
                
                return CompilationResult(
                    success=True,
                    model_name=model_name,
                    compiled_sql=compiled_sql,
                    compilation_time=compilation_time,
                    warnings=self._extract_warnings_from_output(result.stdout)
                )
            else:
                # Compilation failed - parse errors
                errors, suggestions = self._parse_compilation_errors(result.stderr)
                
                return CompilationResult(
                    success=False,
                    model_name=model_name,
                    errors=errors,
                    suggestions=suggestions,
                    compilation_time=compilation_time
                )
                
        except Exception as e:
            logger.error(f"Failed to compile model {model_name}: {e}")
            return CompilationResult(
                success=False,
                model_name=model_name,
                errors=[f"Compilation failed: {str(e)}"],
                suggestions=["Check that dbt is installed and the model exists"]
            )
    
    def compile_all_models(self) -> Dict[str, CompilationResult]:
        """Compile all models in the project"""
        try:
            cmd = [
                "dbt", "compile",
                "--project-dir", str(self.dbt_project_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.dbt_project_path
            )
            
            if result.returncode == 0:
                # Parse successful compilation results
                return self._parse_compilation_results(result.stdout)
            else:
                # Parse failed compilation results
                return self._parse_failed_compilation_results(result.stderr)
                
        except Exception as e:
            logger.error(f"Failed to compile all models: {e}")
            return {}
    
    def validate_sql_syntax(self, sql: str, model_name: str = "temp_model") -> ValidationResult:
        """Validate SQL syntax by attempting compilation"""
        try:
            # Create temporary model file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sql',
                dir=self.dbt_project_path / "models",
                delete=False
            ) as temp_file:
                temp_file.write(sql)
                temp_path = Path(temp_file.name)
            
            try:
                # Try to compile the temporary model
                temp_model_name = temp_path.stem
                compilation_result = self.compile_model(temp_model_name)
                
                if compilation_result.success:
                    return ValidationResult(
                        is_valid=True,
                        warnings=compilation_result.warnings
                    )
                else:
                    return ValidationResult(
                        is_valid=False,
                        errors=compilation_result.errors,
                        suggestions=compilation_result.suggestions
                    )
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
                    
        except Exception as e:
            logger.error(f"Failed to validate SQL: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"],
                suggestions=["Check SQL syntax and dbt configuration"]
            )
    
    def _get_compiled_sql(self, model_name: str) -> Optional[str]:
        """Get compiled SQL for a model from target directory"""
        try:
            # Look for compiled SQL in target/compiled directory
            compiled_path = self.dbt_project_path / "target" / "compiled" / "dbt_mcp_hackathon_project" / "models"
            
            # Search for the model file (could be in subdirectories)
            for sql_file in compiled_path.rglob(f"{model_name}.sql"):
                with open(sql_file, 'r') as f:
                    return f.read()
            
            logger.warning(f"Compiled SQL not found for model: {model_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get compiled SQL for {model_name}: {e}")
            return None
    
    def _parse_compilation_errors(self, stderr: str) -> Tuple[List[str], List[str]]:
        """Parse compilation errors and extract suggestions"""
        errors = []
        suggestions = []
        
        lines = stderr.split('\n')
        current_error = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_error:
                    error_text = ' '.join(current_error)
                    errors.append(error_text)
                    
                    # Generate suggestions based on error patterns
                    suggestion = self._generate_error_suggestion(error_text)
                    if suggestion:
                        suggestions.append(suggestion)
                    
                    current_error = []
                continue
            
            # Skip dbt log prefixes
            if line.startswith('[') or line.startswith('Running with dbt'):
                continue
                
            current_error.append(line)
        
        # Handle last error if exists
        if current_error:
            error_text = ' '.join(current_error)
            errors.append(error_text)
            suggestion = self._generate_error_suggestion(error_text)
            if suggestion:
                suggestions.append(suggestion)
        
        return errors, suggestions
    
    def _generate_error_suggestion(self, error_text: str) -> Optional[str]:
        """Generate helpful suggestions based on error patterns"""
        error_lower = error_text.lower()
        
        if "relation" in error_lower and "does not exist" in error_lower:
            return "Check that referenced tables/models exist and are spelled correctly"
        elif "column" in error_lower and "does not exist" in error_lower:
            return "Verify column names in your SELECT statement"
        elif "syntax error" in error_lower:
            return "Check SQL syntax - missing commas, parentheses, or keywords"
        elif "circular dependency" in error_lower:
            return "Remove circular references between models"
        elif "compilation error" in error_lower and "macro" in error_lower:
            return "Check macro usage and ensure required macros are available"
        elif "jinja" in error_lower:
            return "Check Jinja template syntax in your model"
        else:
            return None
    
    def _extract_warnings_from_output(self, stdout: str) -> List[str]:
        """Extract warnings from dbt output"""
        warnings = []
        lines = stdout.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'WARN' in line or 'WARNING' in line:
                # Clean up the warning message
                warning = line.replace('[WARNING]', '').replace('WARN', '').strip()
                if warning:
                    warnings.append(warning)
        
        return warnings
    
    def _parse_compilation_results(self, stdout: str) -> Dict[str, CompilationResult]:
        """Parse successful compilation results"""
        results = {}
        
        # For now, return empty dict - would need to parse dbt output format
        # This could be enhanced to extract individual model compilation info
        
        return results
    
    def _parse_failed_compilation_results(self, stderr: str) -> Dict[str, CompilationResult]:
        """Parse failed compilation results"""
        results = {}
        
        # For now, return empty dict - would need to parse dbt error format
        # This could be enhanced to extract per-model error information
        
        return results


class DBTExecutionService:
    """Service for dbt model execution operations"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.dbt_project_path = self.config.DBT_PROJECT_PATH
        
    def run_model(self, model_name: str) -> ExecutionResult:
        """Execute a specific dbt model"""
        start_time = datetime.now()
        
        try:
            # Run dbt run for specific model
            cmd = [
                "dbt", "run",
                "--select", model_name,
                "--project-dir", str(self.dbt_project_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.dbt_project_path
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                # Execution successful
                rows_affected = self._extract_rows_affected(result.stdout)
                preview_data = self._get_model_preview_data(model_name)
                
                return ExecutionResult(
                    success=True,
                    model_name=model_name,
                    rows_affected=rows_affected,
                    execution_time=execution_time,
                    preview_data=preview_data,
                    warnings=self._extract_warnings_from_output(result.stdout)
                )
            else:
                # Execution failed
                errors, suggestions = self._parse_execution_errors(result.stderr)
                
                return ExecutionResult(
                    success=False,
                    model_name=model_name,
                    errors=errors,
                    execution_time=execution_time
                )
                
        except Exception as e:
            logger.error(f"Failed to run model {model_name}: {e}")
            return ExecutionResult(
                success=False,
                model_name=model_name,
                errors=[f"Execution failed: {str(e)}"],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def run_model_with_dependencies(self, model_name: str) -> ExecutionResult:
        """Execute a model and all its upstream dependencies"""
        start_time = datetime.now()
        
        try:
            # Run dbt run with upstream dependencies
            cmd = [
                "dbt", "run",
                "--select", f"+{model_name}",
                "--project-dir", str(self.dbt_project_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.dbt_project_path
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                # Get preview data for the target model
                preview_data = self._get_model_preview_data(model_name)
                
                return ExecutionResult(
                    success=True,
                    model_name=model_name,
                    execution_time=execution_time,
                    preview_data=preview_data,
                    warnings=self._extract_warnings_from_output(result.stdout)
                )
            else:
                errors, _ = self._parse_execution_errors(result.stderr)
                
                return ExecutionResult(
                    success=False,
                    model_name=model_name,
                    errors=errors,
                    execution_time=execution_time
                )
                
        except Exception as e:
            logger.error(f"Failed to run model with dependencies {model_name}: {e}")
            return ExecutionResult(
                success=False,
                model_name=model_name,
                errors=[f"Execution failed: {str(e)}"],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def get_model_results(self, model_name: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get results from a model that has been executed"""
        try:
            return self._get_model_preview_data(model_name, limit)
        except Exception as e:
            logger.error(f"Failed to get results for model {model_name}: {e}")
            return None
    
    def _extract_rows_affected(self, stdout: str) -> Optional[int]:
        """Extract number of rows affected from dbt output"""
        try:
            lines = stdout.split('\n')
            for line in lines:
                if 'OK created' in line or 'OK inserted' in line:
                    # Look for patterns like "OK created view [1 row, ...]"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i + 1 < len(parts) and 'row' in parts[i + 1]:
                            return int(part)
            return None
        except Exception:
            return None
    
    def _get_model_preview_data(self, model_name: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get preview data from executed model using DuckDB"""
        try:
            import duckdb
            
            # Connect to the database
            conn = duckdb.connect(str(self.config.DUCKDB_PATH))
            
            # Query the model table (assuming it's materialized)
            query = f"SELECT * FROM {model_name} LIMIT {limit}"
            
            result = conn.execute(query).fetchall()
            columns = [desc[0] for desc in conn.description]
            
            # Convert to list of dictionaries
            preview_data = []
            for row in result:
                row_dict = dict(zip(columns, row))
                # Convert any non-serializable types to strings
                for key, value in row_dict.items():
                    if not isinstance(value, (str, int, float, bool, type(None))):
                        row_dict[key] = str(value)
                preview_data.append(row_dict)
            
            conn.close()
            return preview_data
            
        except Exception as e:
            logger.error(f"Failed to get preview data for {model_name}: {e}")
            return None
    
    def _parse_execution_errors(self, stderr: str) -> Tuple[List[str], List[str]]:
        """Parse execution errors and extract suggestions"""
        errors = []
        suggestions = []
        
        lines = stderr.split('\n')
        current_error = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_error:
                    error_text = ' '.join(current_error)
                    errors.append(error_text)
                    
                    # Generate suggestions based on error patterns
                    suggestion = self._generate_execution_suggestion(error_text)
                    if suggestion:
                        suggestions.append(suggestion)
                    
                    current_error = []
                continue
            
            # Skip dbt log prefixes
            if line.startswith('[') or line.startswith('Running with dbt'):
                continue
                
            current_error.append(line)
        
        # Handle last error if exists
        if current_error:
            error_text = ' '.join(current_error)
            errors.append(error_text)
            suggestion = self._generate_execution_suggestion(error_text)
            if suggestion:
                suggestions.append(suggestion)
        
        return errors, suggestions
    
    def _generate_execution_suggestion(self, error_text: str) -> Optional[str]:
        """Generate helpful suggestions based on execution error patterns"""
        error_lower = error_text.lower()
        
        if "permission denied" in error_lower:
            return "Check database permissions for the target schema"
        elif "table already exists" in error_lower:
            return "Consider using incremental materialization or dropping the existing table"
        elif "out of memory" in error_lower:
            return "Try processing smaller batches or optimizing the query"
        elif "timeout" in error_lower:
            return "Query may be too complex - consider breaking it into smaller steps"
        elif "connection" in error_lower and "failed" in error_lower:
            return "Check database connection settings and network connectivity"
        else:
            return None
    
    def _extract_warnings_from_output(self, stdout: str) -> List[str]:
        """Extract warnings from dbt output"""
        warnings = []
        lines = stdout.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'WARN' in line or 'WARNING' in line:
                # Clean up the warning message
                warning = line.replace('[WARNING]', '').replace('WARN', '').strip()
                if warning:
                    warnings.append(warning)
        
        return warnings


class DBTCompilationExecutionService:
    """Combined service for dbt compilation and execution operations"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.compilation_service = DBTCompilationService(config)
        self.execution_service = DBTExecutionService(config)
    
    def compile_and_run_model(self, model_name: str) -> Tuple[CompilationResult, Optional[ExecutionResult]]:
        """Compile and then run a model if compilation succeeds"""
        # First compile the model
        compilation_result = self.compilation_service.compile_model(model_name)
        
        if not compilation_result.success:
            return compilation_result, None
        
        # If compilation succeeds, run the model
        execution_result = self.execution_service.run_model(model_name)
        
        return compilation_result, execution_result
    
    def validate_and_run_model(self, model_name: str, sql: Optional[str] = None) -> Tuple[ValidationResult, Optional[ExecutionResult]]:
        """Validate SQL (if provided) and run model if valid"""
        if sql:
            # Validate the provided SQL first
            validation_result = self.compilation_service.validate_sql_syntax(sql, model_name)
            
            if not validation_result.is_valid:
                return validation_result, None
        else:
            # Just validate that the model compiles
            compilation_result = self.compilation_service.compile_model(model_name)
            validation_result = ValidationResult(
                is_valid=compilation_result.success,
                errors=compilation_result.errors,
                warnings=compilation_result.warnings,
                suggestions=compilation_result.suggestions
            )
            
            if not validation_result.is_valid:
                return validation_result, None
        
        # If validation passes, run the model
        execution_result = self.execution_service.run_model(model_name)
        
        return validation_result, execution_result