"""
MCP Server implementation for dbt MCP Hackathon Project
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import duckdb

from ..config import Config
from ..shared.models import ModelMetadata, ErrorResponse, ModelGenerationRequest
from .model_service import ModelMetadataService
from .prompt_processor import PromptProcessor
from .ai_service import KiroAIService
from .chatgpt_service import ChatGPTService
from .model_generator import ModelFileManager
from .compilation_service import DBTCompilationExecutionService, CompilationResult, ExecutionResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    dbt_project_path: str
    database_connected: bool
    models_count: int

class ModelGenerationResponse(BaseModel):
    """Response for model generation"""
    success: bool
    model_name: str
    model_path: Optional[str] = None
    schema_path: Optional[str] = None
    message: str
    sql_preview: Optional[str] = None
    conflicts: List[str] = []
    warnings: List[str] = []

class SQLGenerationResponse(BaseModel):
    """Response for SQL generation only"""
    success: bool
    sql: str
    model_name: str
    description: Optional[str] = None
    materialization: str
    confidence: float
    reasoning: Optional[str] = None
    warnings: List[str] = []

class ValidationResponse(BaseModel):
    """Response for SQL validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []

class CompilationResponse(BaseModel):
    """Response for model compilation"""
    success: bool
    model_name: str
    compiled_sql: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    compilation_time: Optional[float] = None

class ExecutionResponse(BaseModel):
    """Response for model execution"""
    success: bool
    model_name: str
    rows_affected: Optional[int] = None
    execution_time: Optional[float] = None
    errors: List[str] = []
    warnings: List[str] = []
    preview_data: Optional[List[Dict[str, Any]]] = None

class ModelResultsResponse(BaseModel):
    """Response for model results"""
    model_name: str
    data: List[Dict[str, Any]]
    row_count: int
    columns: List[str]

class MCPServer:
    """MCP Server for dbt MCP Hackathon Project functionality"""
    
    def __init__(self):
        self.app = FastAPI(title="dbt MCP Hackathon Project MCP Server", version="0.1.0")
        self.config = Config()
        self.db_connection: Optional[duckdb.DuckDBPyConnection] = None
        self.dbt_manifest: Optional[Dict[str, Any]] = None
        self.model_service: Optional[ModelMetadataService] = None
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Initialize connections
        self._initialize_connections()
        
        # Initialize services
        self.model_service = ModelMetadataService(self.config)
        self.prompt_processor: Optional[PromptProcessor] = None
        self.ai_service: Optional[KiroAIService] = None
        self.model_generator: Optional[ModelFileManager] = None
        self.compilation_service: Optional[DBTCompilationExecutionService] = None
        
        # Initialize AI services after model service is ready
        self._initialize_ai_services()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            try:
                models_count = 0
                if self.model_service and self.model_service.manifest:
                    models = self.model_service.get_all_models()
                    models_count = len(models)
                
                return HealthResponse(
                    status="healthy",
                    dbt_project_path=str(self.config.DBT_PROJECT_PATH),
                    database_connected=self.db_connection is not None,
                    models_count=models_count
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/ai-status")
        async def get_ai_status():
            """Get status of AI services"""
            try:
                chatgpt_available = hasattr(self, 'chatgpt_service') and self.chatgpt_service.is_available()
                pattern_ai_available = hasattr(self, 'ai_service') and self.ai_service is not None
                
                status = {
                    "chatgpt": {
                        "available": chatgpt_available,
                        "model": "gpt-4" if chatgpt_available else None,
                        "status": "ready" if chatgpt_available else "not configured"
                    },
                    "pattern_ai": {
                        "available": pattern_ai_available,
                        "status": "ready" if pattern_ai_available else "not initialized"
                    },
                    "recommended": "chatgpt" if chatgpt_available else "pattern_ai",
                    "default_endpoint": "/generate"
                }
                
                return status
                
            except Exception as e:
                logger.error(f"AI status check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/manifest-info")
        async def get_manifest_info():
            """Get information about the dbt manifest"""
            try:
                if not self.model_service:
                    raise HTTPException(status_code=500, detail="Model service not initialized")
                
                return self.model_service.get_manifest_info()
            except Exception as e:
                logger.error(f"Failed to get manifest info: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models")
        async def list_models(
            search: Optional[str] = Query(None, description="Search query for model name, description, or tags"),
            materialization: Optional[str] = Query(None, description="Filter by materialization type"),
            layer: Optional[str] = Query(None, description="Filter by model layer (staging, intermediate, marts)"),
            tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
            limit: Optional[int] = Query(None, description="Limit number of results"),
            offset: Optional[int] = Query(0, description="Offset for pagination")
        ):
            """List all dbt models with metadata, search, and filtering"""
            try:
                if not self.model_service:
                    raise HTTPException(status_code=500, detail="Model service not initialized")
                
                # Build filters
                filters = {}
                if materialization:
                    filters["materialization"] = materialization
                if layer:
                    filters["layer"] = layer
                if tags:
                    filters["tags"] = [tag.strip() for tag in tags.split(",")]
                
                # Get filtered models
                models = self.model_service.search_models(search or "", filters if filters else None)
                
                # Apply pagination
                total_count = len(models)
                if offset:
                    models = models[offset:]
                if limit:
                    models = models[:limit]
                
                # Convert to dict format for JSON response
                models_data = []
                for model in models:
                    model_dict = {
                        "name": model.name,
                        "path": model.path,
                        "description": model.description,
                        "materialization": model.materialization,
                        "tags": model.tags,
                        "depends_on": model.depends_on,
                        "referenced_by": model.referenced_by,
                        "columns": [
                            {
                                "name": col.name,
                                "data_type": col.data_type,
                                "description": col.description,
                                "tests": col.tests
                            } for col in model.columns
                        ]
                    }
                    models_data.append(model_dict)
                
                return {
                    "models": models_data,
                    "total_count": total_count,
                    "offset": offset,
                    "limit": limit
                }
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models/{model_name}")
        async def get_model_details(model_name: str):
            """Get detailed information about a specific model"""
            try:
                if not self.model_service:
                    raise HTTPException(status_code=500, detail="Model service not initialized")
                
                model = self.model_service.get_model_by_name(model_name)
                
                if not model:
                    raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
                
                return {
                    "name": model.name,
                    "path": model.path,
                    "description": model.description,
                    "columns": [
                        {
                            "name": col.name,
                            "data_type": col.data_type,
                            "description": col.description,
                            "tests": col.tests
                        } for col in model.columns
                    ],
                    "depends_on": model.depends_on,
                    "referenced_by": model.referenced_by,
                    "materialization": model.materialization,
                    "tags": model.tags
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get model details: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/lineage/{model_name}")
        async def get_model_lineage(model_name: str):
            """Get dependency information for a specific model"""
            try:
                if not self.model_service:
                    raise HTTPException(status_code=500, detail="Model service not initialized")
                
                # Check if model exists
                model = self.model_service.get_model_by_name(model_name)
                if not model:
                    raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
                
                dependencies = self.model_service.get_model_dependencies(model_name)
                
                return {
                    "model": model_name,
                    "upstream": dependencies["upstream"],
                    "downstream": dependencies["downstream"]
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get model lineage: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/search/models")
        async def search_models(
            q: str = Query(..., description="Search query"),
            materialization: Optional[str] = Query(None, description="Filter by materialization type"),
            layer: Optional[str] = Query(None, description="Filter by model layer"),
            tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
            limit: int = Query(50, description="Maximum number of results"),
            offset: int = Query(0, description="Offset for pagination")
        ):
            """Advanced search for dbt models"""
            try:
                if not self.model_service:
                    raise HTTPException(status_code=500, detail="Model service not initialized")
                
                # Build filters
                filters = {}
                if materialization:
                    filters["materialization"] = materialization
                if layer:
                    filters["layer"] = layer
                if tags:
                    filters["tags"] = [tag.strip() for tag in tags.split(",")]
                
                # Perform search
                models = self.model_service.search_models(q, filters if filters else None)
                
                # Apply pagination
                total_count = len(models)
                paginated_models = models[offset:offset + limit] if limit else models[offset:]
                
                # Convert to simplified format for search results
                search_results = []
                for model in paginated_models:
                    result = {
                        "name": model.name,
                        "path": model.path,
                        "description": model.description,
                        "materialization": model.materialization,
                        "tags": model.tags,
                        "column_count": len(model.columns),
                        "dependency_count": len(model.depends_on) + len(model.referenced_by)
                    }
                    search_results.append(result)
                
                return {
                    "results": search_results,
                    "query": q,
                    "total_count": total_count,
                    "offset": offset,
                    "limit": limit,
                    "filters_applied": filters
                }
            except Exception as e:
                logger.error(f"Failed to search models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/refresh")
        async def refresh_manifest():
            """Refresh the dbt manifest from disk"""
            try:
                if not self.model_service:
                    raise HTTPException(status_code=500, detail="Model service not initialized")
                
                success = self.model_service.reload_manifest()
                if success:
                    # Also reload the server's manifest for health checks
                    self._load_dbt_manifest()
                    return {"status": "success", "message": "Manifest reloaded successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to reload manifest")
            except Exception as e:
                logger.error(f"Failed to refresh manifest: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models", response_model=ModelGenerationResponse)
        async def create_model(request: ModelGenerationRequest):
            """Create a new dbt model from natural language prompt"""
            try:
                if not all([self.prompt_processor, self.ai_service, self.model_generator]):
                    raise HTTPException(status_code=500, detail="AI services not initialized")
                
                # Analyze the prompt
                analysis = self.prompt_processor.analyze_prompt(request.prompt)
                
                # Override analysis with request parameters if provided
                if request.output_name:
                    analysis.output_name = request.output_name
                if request.materialization:
                    analysis.materialization = request.materialization
                if request.description:
                    analysis.description = request.description
                
                # Generate SQL using AI service
                sql_result = self.ai_service.generate_sql_from_analysis(analysis, request.prompt)
                
                # Create model file
                file_result = self.model_generator.create_model_from_sql_result(sql_result)
                
                return ModelGenerationResponse(
                    success=file_result.success,
                    model_name=sql_result.model_name,
                    model_path=str(file_result.model_path) if file_result.success else None,
                    schema_path=str(file_result.schema_path) if file_result.schema_path else None,
                    message=file_result.message,
                    sql_preview=sql_result.sql,
                    conflicts=file_result.conflicts,
                    warnings=sql_result.warnings
                )
                
            except Exception as e:
                logger.error(f"Failed to create model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/generate", response_model=SQLGenerationResponse)
        async def generate_sql(request: ModelGenerationRequest):
            """Generate SQL code from natural language prompt (uses ChatGPT if available)"""
            try:
                # Try ChatGPT first if available
                if hasattr(self, 'chatgpt_service') and self.chatgpt_service.is_available():
                    return await self._generate_with_chatgpt(request)
                
                # Fallback to pattern-based AI
                if not all([self.prompt_processor, self.ai_service]):
                    raise HTTPException(status_code=500, detail="AI services not initialized")
                
                return await self._generate_with_pattern_ai(request)
                
            except Exception as e:
                logger.error(f"Failed to generate SQL: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/generate-chatgpt", response_model=SQLGenerationResponse)
        async def generate_sql_chatgpt(request: ModelGenerationRequest):
            """Generate SQL code using ChatGPT specifically"""
            try:
                if not hasattr(self, 'chatgpt_service') or not self.chatgpt_service.is_available():
                    raise HTTPException(
                        status_code=503, 
                        detail="ChatGPT service not available. Please configure OPENAI_API_KEY."
                    )
                
                return await self._generate_with_chatgpt(request)
                
            except Exception as e:
                logger.error(f"Failed to generate SQL with ChatGPT: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/generate-pattern", response_model=SQLGenerationResponse)
        async def generate_sql_pattern(request: ModelGenerationRequest):
            """Generate SQL code using pattern-based AI specifically"""
            try:
                if not all([self.prompt_processor, self.ai_service]):
                    raise HTTPException(status_code=500, detail="Pattern-based AI services not initialized")
                
                return await self._generate_with_pattern_ai(request)
                
            except Exception as e:
                logger.error(f"Failed to generate SQL with pattern AI: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/validate", response_model=ValidationResponse)
        async def validate_sql(sql: str = None, model_name: str = None):
            """Validate generated SQL or existing model"""
            try:
                if not self.ai_service:
                    raise HTTPException(status_code=500, detail="AI service not initialized")
                
                if sql:
                    # Validate provided SQL
                    validation_result = self.ai_service.validate_generated_sql(sql, {})
                    return ValidationResponse(
                        is_valid=validation_result["is_valid"],
                        errors=validation_result["errors"],
                        warnings=validation_result["warnings"],
                        suggestions=validation_result["suggestions"]
                    )
                elif model_name and self.model_generator:
                    # Validate existing model file
                    model_path = self.model_generator._find_model_file(model_name)
                    if not model_path:
                        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
                    
                    validation_result = self.model_generator.validate_model_file(model_path)
                    return ValidationResponse(
                        is_valid=validation_result.is_valid,
                        errors=validation_result.errors,
                        warnings=validation_result.warnings,
                        suggestions=validation_result.suggestions
                    )
                else:
                    raise HTTPException(status_code=400, detail="Either 'sql' or 'model_name' must be provided")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to validate: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/models/{model_name}")
        async def delete_model(model_name: str):
            """Delete a generated model"""
            try:
                if not self.model_generator:
                    raise HTTPException(status_code=500, detail="Model generator not initialized")
                
                success = self.model_generator.delete_model(model_name)
                
                if success:
                    return {"success": True, "message": f"Model '{model_name}' deleted successfully"}
                else:
                    raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to delete model: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/generated-models")
        async def list_generated_models():
            """List all models generated by dbt MCP Hackathon Project"""
            try:
                if not self.model_generator:
                    raise HTTPException(status_code=500, detail="Model generator not initialized")
                
                generated_models = self.model_generator.list_generated_models()
                
                return {
                    "models": generated_models,
                    "count": len(generated_models)
                }
                
            except Exception as e:
                logger.error(f"Failed to list generated models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/compile", response_model=CompilationResponse)
        async def compile_model(model_name: str):
            """Compile a specific dbt model"""
            try:
                if not self.compilation_service:
                    raise HTTPException(status_code=500, detail="Compilation service not initialized")
                
                result = self.compilation_service.compilation_service.compile_model(model_name)
                
                return CompilationResponse(
                    success=result.success,
                    model_name=result.model_name,
                    compiled_sql=result.compiled_sql,
                    errors=result.errors,
                    warnings=result.warnings,
                    suggestions=result.suggestions,
                    compilation_time=result.compilation_time
                )
                
            except Exception as e:
                logger.error(f"Failed to compile model {model_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/run", response_model=ExecutionResponse)
        async def run_model(
            model_name: str,
            with_dependencies: bool = False
        ):
            """Execute a dbt model"""
            try:
                if not self.compilation_service:
                    raise HTTPException(status_code=500, detail="Compilation service not initialized")
                
                if with_dependencies:
                    result = self.compilation_service.execution_service.run_model_with_dependencies(model_name)
                else:
                    result = self.compilation_service.execution_service.run_model(model_name)
                
                return ExecutionResponse(
                    success=result.success,
                    model_name=result.model_name,
                    rows_affected=result.rows_affected,
                    execution_time=result.execution_time,
                    errors=result.errors,
                    warnings=result.warnings,
                    preview_data=result.preview_data
                )
                
            except Exception as e:
                logger.error(f"Failed to run model {model_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/results/{model_name}", response_model=ModelResultsResponse)
        async def get_model_results(
            model_name: str,
            limit: int = Query(100, description="Maximum number of rows to return")
        ):
            """Get execution results for a specific model"""
            try:
                if not self.compilation_service:
                    raise HTTPException(status_code=500, detail="Compilation service not initialized")
                
                data = self.compilation_service.execution_service.get_model_results(model_name, limit)
                
                if data is None:
                    raise HTTPException(status_code=404, detail=f"No results found for model '{model_name}'")
                
                columns = list(data[0].keys()) if data else []
                
                return ModelResultsResponse(
                    model_name=model_name,
                    data=data,
                    row_count=len(data),
                    columns=columns
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get results for model {model_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/compile-and-run", response_model=Dict[str, Any])
        async def compile_and_run_model(model_name: str):
            """Compile and run a model in one operation"""
            try:
                if not self.compilation_service:
                    raise HTTPException(status_code=500, detail="Compilation service not initialized")
                
                compilation_result, execution_result = self.compilation_service.compile_and_run_model(model_name)
                
                response = {
                    "compilation": {
                        "success": compilation_result.success,
                        "model_name": compilation_result.model_name,
                        "compiled_sql": compilation_result.compiled_sql,
                        "errors": compilation_result.errors,
                        "warnings": compilation_result.warnings,
                        "suggestions": compilation_result.suggestions,
                        "compilation_time": compilation_result.compilation_time
                    }
                }
                
                if execution_result:
                    response["execution"] = {
                        "success": execution_result.success,
                        "model_name": execution_result.model_name,
                        "rows_affected": execution_result.rows_affected,
                        "execution_time": execution_result.execution_time,
                        "errors": execution_result.errors,
                        "warnings": execution_result.warnings,
                        "preview_data": execution_result.preview_data
                    }
                
                return response
                
            except Exception as e:
                logger.error(f"Failed to compile and run model {model_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def _initialize_connections(self):
        """Initialize database and dbt connections"""
        try:
            # Validate configuration
            self.config.validate()
            
            # Connect to DuckDB
            self._connect_database()
            
            # Load dbt manifest
            self._load_dbt_manifest()
            
            logger.info("MCP Server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Server: {e}")
            raise
    
    def _connect_database(self):
        """Connect to DuckDB database"""
        try:
            self.db_connection = duckdb.connect(str(self.config.DUCKDB_PATH))
            logger.info(f"Connected to DuckDB: {self.config.DUCKDB_PATH}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise
    
    def _load_dbt_manifest(self):
        """Load dbt manifest.json file"""
        try:
            manifest_path = self.config.DBT_PROJECT_PATH / "target" / "manifest.json"
            
            if not manifest_path.exists():
                logger.warning(f"dbt manifest not found at {manifest_path}. Run 'dbt compile' first.")
                return
            
            with open(manifest_path, 'r') as f:
                self.dbt_manifest = json.load(f)
            
            logger.info(f"Loaded dbt manifest with {len(self.dbt_manifest.get('nodes', {}))} nodes")
        except Exception as e:
            logger.error(f"Failed to load dbt manifest: {e}")
            # Don't raise here - server can still function without manifest
    
    def _initialize_ai_services(self):
        """Initialize AI-related services"""
        try:
            if self.model_service and self.model_service.manifest:
                self.prompt_processor = PromptProcessor(self.model_service)
                
                # Initialize both AI services
                self.ai_service = KiroAIService()  # Pattern-based fallback
                self.chatgpt_service = ChatGPTService(self.config)  # Real AI
                
                self.model_generator = ModelFileManager(self.config)
                logger.info("AI services initialized successfully")
                
                # Log which AI service is available
                if self.chatgpt_service.is_available():
                    logger.info("ChatGPT service is available and will be used for generation")
                else:
                    logger.info("ChatGPT service not available, using pattern-based AI")
            else:
                logger.warning("AI services not initialized - dbt manifest not available")
            
            # Initialize compilation service (doesn't require manifest)
            self.compilation_service = DBTCompilationExecutionService(self.config)
            logger.info("Compilation service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
    
    async def _generate_with_chatgpt(self, request: ModelGenerationRequest) -> SQLGenerationResponse:
        """Generate SQL using ChatGPT service"""
        
        # Build context for ChatGPT
        context = {
            "materialization": request.materialization or "view",
            "business_area": getattr(request, 'business_context', ''),
            "requirements": request.description
        }
        
        # Call ChatGPT service
        result = await self.chatgpt_service.generate_sql(request.prompt, context)
        
        if result["success"]:
            return SQLGenerationResponse(
                success=True,
                sql=result["sql"],
                model_name=result["model_name"],
                description=result["description"],
                materialization=result["materialization"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                warnings=result.get("warnings", [])
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    async def _generate_with_pattern_ai(self, request: ModelGenerationRequest) -> SQLGenerationResponse:
        """Generate SQL using pattern-based AI service"""
        
        # Analyze the prompt
        analysis = self.prompt_processor.analyze_prompt(request.prompt)
        
        # Override analysis with request parameters if provided
        if request.output_name:
            analysis.output_name = request.output_name
        if request.materialization:
            analysis.materialization = request.materialization
        if request.description:
            analysis.description = request.description
        
        # Generate SQL using pattern-based AI service
        sql_result = self.ai_service.generate_sql_from_analysis(analysis, request.prompt)
        
        return SQLGenerationResponse(
            success=True,
            sql=sql_result.sql,
            model_name=sql_result.model_name,
            description=sql_result.description,
            materialization=sql_result.materialization,
            confidence=sql_result.confidence,
            reasoning=sql_result.reasoning,
            warnings=sql_result.warnings
        )
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app