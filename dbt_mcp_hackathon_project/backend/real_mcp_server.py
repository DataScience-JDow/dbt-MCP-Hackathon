"""
Real MCP Server implementation with ChatGPT integration
"""
import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Sequence
from pathlib import Path

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource
)

# OpenAI imports
import openai
from openai import AsyncOpenAI

# Our existing services
try:
    from ..config import Config
    from ..shared.models import ModelMetadata, ModelGenerationRequest
    from .model_service import ModelMetadataService
    from .compilation_service import DBTCompilationExecutionService
    from .model_generator import ModelFileManager
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from config import Config
    from shared.models import ModelMetadata, ModelGenerationRequest
    from backend.model_service import ModelMetadataService
    from backend.compilation_service import DBTCompilationExecutionService
    from backend.model_generator import ModelFileManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealMCPServer:
    """
    Real MCP Server implementation with ChatGPT integration
    
    This replaces our custom FastAPI server with a proper MCP implementation
    that can be used by AI agents like Claude, ChatGPT, etc.
    """
    
    def __init__(self):
        self.config = Config()
        
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize our existing services
        self.model_service = ModelMetadataService(self.config)
        self.compilation_service = DBTCompilationExecutionService(self.config)
        self.model_generator = ModelFileManager(self.config)
        
        # MCP server will be initialized in setup_mcp_server()
        self.mcp_server = None
    
    async def setup_mcp_server(self):
        """Setup the MCP server with tools and resources"""
        
        # Initialize MCP server
        self.mcp_server = Server("dbt-mcp-hackathon")
        
        # Register tools
        await self.mcp_server.register_tool(
            Tool(
                name="list_models",
                description="List all dbt models in the project with optional filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": "Search query for model name, description, or tags"
                        },
                        "materialization": {
                            "type": "string",
                            "description": "Filter by materialization type (table, view, incremental)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of models to return",
                            "default": 50
                        }
                    },
                    "required": []
                }
            ),
            self.list_models_handler
        )
        
        await self.mcp_server.register_tool(
            Tool(
                name="get_model_details",
                description="Get detailed information about a specific dbt model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "Name of the model to get details for"
                        }
                    },
                    "required": ["model_name"]
                }
            ),
            self.get_model_details_handler
        )
        
        await self.mcp_server.register_tool(
            Tool(
                name="generate_model",
                description="Generate a new dbt model using ChatGPT from natural language prompt",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Natural language description of the model to generate"
                        },
                        "model_name": {
                            "type": "string",
                            "description": "Optional name for the generated model"
                        },
                        "materialization": {
                            "type": "string",
                            "description": "Materialization type (view, table, incremental)",
                            "default": "view"
                        },
                        "business_context": {
                            "type": "string",
                            "description": "Additional business context for better generation"
                        },
                        "save_model": {
                            "type": "boolean",
                            "description": "Whether to save the generated model to filesystem",
                            "default": false
                        }
                    },
                    "required": ["prompt"]
                }
            ),
            self.generate_model_handler
        )
        
        await self.mcp_server.register_tool(
            Tool(
                name="compile_model",
                description="Compile a dbt model to check for syntax errors",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "Name of the model to compile"
                        }
                    },
                    "required": ["model_name"]
                }
            ),
            self.compile_model_handler
        )
        
        await self.mcp_server.register_tool(
            Tool(
                name="run_model",
                description="Execute a dbt model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "Name of the model to run"
                        },
                        "with_dependencies": {
                            "type": "boolean",
                            "description": "Whether to run upstream dependencies first",
                            "default": false
                        }
                    },
                    "required": ["model_name"]
                }
            ),
            self.run_model_handler
        )
        
        await self.mcp_server.register_tool(
            Tool(
                name="get_model_lineage",
                description="Get dependency information (upstream and downstream) for a model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "Name of the model to get lineage for"
                        }
                    },
                    "required": ["model_name"]
                }
            ),
            self.get_model_lineage_handler
        )
        
        # Register resources
        await self.mcp_server.register_resource(
            Resource(
                uri="dbt://manifest",
                name="dbt Manifest",
                description="Current dbt project manifest with all models and metadata",
                mimeType="application/json"
            ),
            self.get_manifest_resource
        )
        
        logger.info("MCP Server setup complete")
    
    async def list_models_handler(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP tool handler for listing models"""
        try:
            search = arguments.get("search", "")
            materialization = arguments.get("materialization")
            limit = arguments.get("limit", 50)
            
            # Build filters
            filters = {}
            if materialization:
                filters["materialization"] = materialization
            
            # Get filtered models
            if search or filters:
                models = self.model_service.search_models(search, filters if filters else None)
            else:
                models = self.model_service.get_all_models()
            
            # Apply limit
            if limit:
                models = models[:limit]
            
            # Format models for MCP response
            models_data = []
            for model in models:
                models_data.append({
                    "name": model.name,
                    "description": model.description,
                    "materialization": model.materialization,
                    "path": model.path,
                    "tags": model.tags,
                    "column_count": len(model.columns),
                    "dependencies": len(model.depends_on),
                    "dependents": len(model.referenced_by)
                })
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "models": models_data,
                    "count": len(models_data),
                    "search_query": search,
                    "filters_applied": filters
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return [TextContent(
                type="text", 
                text=f"Error listing models: {str(e)}"
            )]
    
    async def get_model_details_handler(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP tool handler for getting model details"""
        try:
            model_name = arguments.get("model_name", "")
            
            if not model_name:
                return [TextContent(
                    type="text",
                    text="Error: No model name provided"
                )]
            
            model = self.model_service.get_model_by_name(model_name)
            
            if not model:
                return [TextContent(
                    type="text",
                    text=f"Error: Model '{model_name}' not found"
                )]
            
            model_details = {
                "name": model.name,
                "path": model.path,
                "description": model.description,
                "materialization": model.materialization,
                "tags": model.tags,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "description": col.description,
                        "tests": col.tests
                    } for col in model.columns
                ],
                "depends_on": model.depends_on,
                "referenced_by": model.referenced_by
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(model_details, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error getting model details: {e}")
            return [TextContent(
                type="text",
                text=f"Error getting model details: {str(e)}"
            )]
    
    async def get_model_lineage_handler(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP tool handler for getting model lineage"""
        try:
            model_name = arguments.get("model_name", "")
            
            if not model_name:
                return [TextContent(
                    type="text",
                    text="Error: No model name provided"
                )]
            
            # Check if model exists
            model = self.model_service.get_model_by_name(model_name)
            if not model:
                return [TextContent(
                    type="text",
                    text=f"Error: Model '{model_name}' not found"
                )]
            
            dependencies = self.model_service.get_model_dependencies(model_name)
            
            lineage_info = {
                "model": model_name,
                "upstream_dependencies": dependencies["upstream"],
                "downstream_dependents": dependencies["downstream"],
                "total_upstream": len(dependencies["upstream"]),
                "total_downstream": len(dependencies["downstream"])
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(lineage_info, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error getting model lineage: {e}")
            return [TextContent(
                type="text",
                text=f"Error getting model lineage: {str(e)}"
            )]
    
    async def generate_model_with_chatgpt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a dbt model using ChatGPT instead of our pattern-based system
        """
        try:
            # Build comprehensive prompt for ChatGPT
            system_prompt = self._build_chatgpt_system_prompt()
            user_prompt = self._build_chatgpt_user_prompt(prompt, context)
            
            # Call ChatGPT
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",  # or gpt-3.5-turbo for faster/cheaper
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=2000
            )
            
            # Parse ChatGPT response
            generated_sql = response.choices[0].message.content.strip()
            
            # Extract model name and other metadata from the response
            model_name = self._extract_model_name_from_sql(generated_sql)
            
            return {
                "success": True,
                "sql": generated_sql,
                "model_name": model_name,
                "description": f"Generated from: {prompt}",
                "materialization": "view",  # Default, could be extracted from SQL
                "confidence": 0.95,  # High confidence with real AI
                "reasoning": "Generated using ChatGPT with dbt context"
            }
            
        except Exception as e:
            logger.error(f"ChatGPT generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql": "",
                "model_name": "failed_generation"
            }
    
    def _build_chatgpt_system_prompt(self) -> str:
        """Build comprehensive system prompt for ChatGPT"""
        
        # Get available models for context
        models = self.model_service.get_all_models()
        model_context = "\n".join([
            f"- {model.name}: {model.description or 'No description'}"
            for model in models[:10]  # Limit to avoid token limits
        ])
        
        return f"""You are an expert dbt developer. Generate SQL for dbt models following these guidelines:

AVAILABLE MODELS IN PROJECT:
{model_context}

DBT BEST PRACTICES:
1. Use {{{{ ref('model_name') }}}} for model references
2. Use {{{{ source('schema', 'table') }}}} for source tables
3. Use CTEs (Common Table Expressions) for readability
4. Use lowercase SQL keywords
5. Use snake_case for column names
6. Include trailing commas in SELECT statements
7. Add meaningful comments

RESPONSE FORMAT:
- Return ONLY the SQL code
- No markdown formatting or explanations
- Include model configuration if needed: {{{{ config(materialized='table') }}}}
- Ensure all referenced models exist in the available models list

EXAMPLE OUTPUT:
{{{{
  config(materialized='view')
}}}}

with source_data as (
  select * from {{{{ ref('customers') }}}}
),

final as (
  select
    customer_id,
    first_name,
    last_name,
    email,
    created_at
  from source_data
)

select * from final
"""
    
    def _build_chatgpt_user_prompt(self, user_prompt: str, context: Dict[str, Any]) -> str:
        """Build user prompt with context"""
        
        prompt_parts = [
            f"USER REQUEST: {user_prompt}",
            "",
            "CONTEXT:"
        ]
        
        if context.get("business_area"):
            prompt_parts.append(f"- Business area: {context['business_area']}")
        
        if context.get("materialization"):
            prompt_parts.append(f"- Preferred materialization: {context['materialization']}")
        
        if context.get("existing_models"):
            prompt_parts.append("- Focus on these existing models:")
            for model in context["existing_models"][:5]:
                prompt_parts.append(f"  - {model}")
        
        prompt_parts.extend([
            "",
            "Generate a complete dbt model SQL file that fulfills this request."
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_model_name_from_sql(self, sql: str) -> str:
        """Extract model name from generated SQL or create one"""
        # Simple extraction - could be enhanced
        lines = sql.split('\n')
        for line in lines:
            if 'from final' in line.lower():
                return "generated_model"
        
        return "chatgpt_generated_model"
    
    async def generate_model_handler(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP tool handler for model generation using ChatGPT"""
        try:
            prompt = arguments.get("prompt", "")
            materialization = arguments.get("materialization", "view")
            business_context = arguments.get("business_context", "")
            
            if not prompt:
                return [TextContent(
                    type="text",
                    text="Error: No prompt provided"
                )]
            
            # Build context for ChatGPT
            context = {
                "materialization": materialization,
                "business_area": business_context,
                "existing_models": [model.name for model in self.model_service.get_all_models()]
            }
            
            # Generate with ChatGPT
            result = await self.generate_model_with_chatgpt(prompt, context)
            
            if result["success"]:
                # Optionally save the generated model
                if arguments.get("save_model", False):
                    model_path = await self._save_generated_model(
                        result["model_name"],
                        result["sql"],
                        result["description"]
                    )
                    result["model_path"] = str(model_path)
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Generation failed: {result['error']}"
                )]
                
        except Exception as e:
            logger.error(f"Error in generate_model_handler: {e}")
            return [TextContent(
                type="text",
                text=f"Error generating model: {str(e)}"
            )]
    
    async def _save_generated_model(self, model_name: str, sql: str, description: str) -> Path:
        """Save generated model to filesystem"""
        return self.model_generator.create_model_file(
            model_name=model_name,
            sql_content=sql,
            description=description,
            materialization="view"  # Default
        )
    
    async def compile_model_handler(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP tool handler for compiling models"""
        try:
            model_name = arguments.get("model_name", "")
            
            if not model_name:
                return [TextContent(
                    type="text",
                    text="Error: No model name provided"
                )]
            
            # Use our existing compilation service
            result = self.compilation_service.compilation_service.compile_model(model_name)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": result.success,
                    "model_name": model_name,
                    "compiled_sql": result.compiled_sql,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "compilation_time": result.compilation_time
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error compiling model: {e}")
            return [TextContent(
                type="text",
                text=f"Error compiling model: {str(e)}"
            )]
    
    async def run_model_handler(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """MCP tool handler for running models"""
        try:
            model_name = arguments.get("model_name", "")
            with_dependencies = arguments.get("with_dependencies", False)
            
            if not model_name:
                return [TextContent(
                    type="text",
                    text="Error: No model name provided"
                )]
            
            # Use our existing execution service
            if with_dependencies:
                result = self.compilation_service.execution_service.run_model_with_dependencies(model_name)
            else:
                result = self.compilation_service.execution_service.run_model(model_name)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": result.success,
                    "model_name": model_name,
                    "rows_affected": result.rows_affected,
                    "execution_time": result.execution_time,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "with_dependencies": with_dependencies
                }, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error running model: {e}")
            return [TextContent(
                type="text",
                text=f"Error running model: {str(e)}"
            )]
    
    async def get_manifest_resource(self, uri: str) -> str:
        """MCP resource handler for dbt manifest"""
        try:
            manifest_info = self.model_service.get_manifest_info()
            return json.dumps(manifest_info, indent=2)
        except Exception as e:
            logger.error(f"Error getting manifest resource: {e}")
            return json.dumps({"error": str(e)})
    
    async def run_server(self):
        """Run the MCP server"""
        try:
            await self.setup_mcp_server()
            
            # Start MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.mcp_server.run(
                    read_stream,
                    write_stream,
                    self.mcp_server.create_initialization_options()
                )
            
            logger.info("MCP Server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

# Entry point for running the real MCP server
async def main():
    """Main entry point for the real MCP server"""
    server = RealMCPServer()
    await server.run_server()

if __name__ == "__main__":
    asyncio.run(main())