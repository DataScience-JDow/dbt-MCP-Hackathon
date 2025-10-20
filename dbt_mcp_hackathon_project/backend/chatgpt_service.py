"""
ChatGPT integration service for SQL generation
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
import json

from openai import AsyncOpenAI
from ..config import Config
from ..shared.models import ModelMetadata
from .model_service import ModelMetadataService

logger = logging.getLogger(__name__)

class ChatGPTService:
    """
    Service for integrating with ChatGPT for SQL generation
    
    This replaces our pattern-based AI with real ChatGPT integration
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. ChatGPT integration will not work.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
        
        # Initialize model service for context
        self.model_service = ModelMetadataService(config)
        
        # Configuration
        self.model_name = "gpt-4"  # or "gpt-3.5-turbo" for faster/cheaper
        self.temperature = 0.1  # Low temperature for consistent SQL
        self.max_tokens = 2000
    
    def is_available(self) -> bool:
        """Check if ChatGPT service is available"""
        return self.client is not None
    
    async def generate_sql(self, 
                          prompt: str, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate SQL using ChatGPT
        
        Args:
            prompt: User's natural language request
            context: Additional context (materialization, business area, etc.)
            
        Returns:
            Dict with success, sql, model_name, description, etc.
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "ChatGPT service not available. Please set OPENAI_API_KEY.",
                "sql": "",
                "model_name": "failed_generation"
            }
        
        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(prompt, context or {})
            
            logger.info(f"Generating SQL with ChatGPT for prompt: {prompt[:100]}...")
            
            # Call ChatGPT
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract generated SQL
            generated_sql = response.choices[0].message.content.strip()
            
            # Parse the response
            result = self._parse_generated_sql(generated_sql, prompt, context)
            
            logger.info(f"Successfully generated SQL for model: {result['model_name']}")
            
            return result
            
        except Exception as e:
            logger.error(f"ChatGPT generation failed: {e}")
            return {
                "success": False,
                "error": f"ChatGPT API error: {str(e)}",
                "sql": "",
                "model_name": "failed_generation"
            }
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for ChatGPT"""
        
        # Get available models for context
        try:
            models = self.model_service.get_all_models()
            model_context = self._format_models_for_context(models)
        except Exception as e:
            logger.warning(f"Could not load models for context: {e}")
            model_context = "No models available in context"
        
        return f"""You are an expert dbt developer. Generate SQL for dbt models following these strict guidelines:

AVAILABLE MODELS IN PROJECT:
{model_context}

DBT BEST PRACTICES:
1. ALWAYS use {{{{ ref('model_name') }}}} for dbt model references
2. Use {{{{ source('schema', 'table') }}}} for raw source tables
3. Structure with CTEs (Common Table Expressions) for readability
4. Use lowercase SQL keywords (select, from, where, etc.)
5. Use snake_case for all column names and aliases
6. Include trailing commas in SELECT statements for maintainability
7. Add meaningful comments explaining business logic
8. Use proper indentation (2 spaces)

MATERIALIZATION GUIDELINES:
- view: For lightweight transformations, fast queries
- table: For heavy transformations, frequently queried data
- incremental: For large datasets that grow over time

SQL STRUCTURE TEMPLATE:
{{{{
  config(materialized='view')
}}}}

-- Description of what this model does
with source_data as (
  select * from {{{{ ref('source_model') }}}}
),

transformed as (
  select
    column_1,
    column_2,
    -- Add calculated fields
    column_1 + column_2 as calculated_field,
    current_timestamp as processed_at
  from source_data
  where condition = 'value'
),

final as (
  select * from transformed
)

select * from final

RESPONSE REQUIREMENTS:
- Return ONLY the SQL code, no explanations or markdown
- Ensure all referenced models exist in the available models list
- If a model doesn't exist, use a similar one or create a reasonable assumption
- Include appropriate model configuration at the top
- Add comments explaining complex logic

COLUMN NAMING:
- Use descriptive names: customer_lifetime_value not clv
- Use standard suffixes: _at for timestamps, _id for identifiers
- Group related columns together in SELECT statements
"""
    
    def _format_models_for_context(self, models: List[ModelMetadata]) -> str:
        """Format models for inclusion in ChatGPT context"""
        if not models:
            return "No models available"
        
        # Limit to avoid token limits, prioritize by importance
        important_models = []
        other_models = []
        
        for model in models:
            if any(keyword in model.name.lower() for keyword in ['customer', 'order', 'product', 'revenue']):
                important_models.append(model)
            else:
                other_models.append(model)
        
        # Take top 15 models to stay within token limits
        selected_models = (important_models + other_models)[:15]
        
        context_lines = []
        for model in selected_models:
            description = model.description or "No description"
            columns = ", ".join([col.name for col in model.columns[:5]])  # First 5 columns
            if len(model.columns) > 5:
                columns += f" (and {len(model.columns) - 5} more)"
            
            context_lines.append(
                f"- {model.name} ({model.materialization}): {description}\n"
                f"  Columns: {columns}"
            )
        
        return "\n".join(context_lines)
    
    def _build_user_prompt(self, user_prompt: str, context: Dict[str, Any]) -> str:
        """Build user prompt with context"""
        
        prompt_parts = [
            f"USER REQUEST: {user_prompt}",
            ""
        ]
        
        # Add context if provided
        if context:
            prompt_parts.append("ADDITIONAL CONTEXT:")
            
            if context.get("materialization"):
                prompt_parts.append(f"- Preferred materialization: {context['materialization']}")
            
            if context.get("business_area"):
                prompt_parts.append(f"- Business area: {context['business_area']}")
            
            if context.get("focus_models"):
                prompt_parts.append("- Focus on these models:")
                for model in context["focus_models"][:5]:
                    prompt_parts.append(f"  - {model}")
            
            if context.get("requirements"):
                prompt_parts.append(f"- Special requirements: {context['requirements']}")
            
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Generate a complete dbt model SQL file that fulfills this request.",
            "Remember to use {{ ref() }} for model references and follow all dbt best practices."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_generated_sql(self, 
                           generated_sql: str, 
                           original_prompt: str, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate generated SQL"""
        
        # Extract model name from SQL or generate one
        model_name = self._extract_model_name(generated_sql, original_prompt)
        
        # Extract materialization from config
        materialization = self._extract_materialization(generated_sql)
        
        # Basic validation
        validation_result = self._validate_sql(generated_sql)
        
        return {
            "success": True,
            "sql": generated_sql,
            "model_name": model_name,
            "description": f"Generated from: {original_prompt}",
            "materialization": materialization,
            "confidence": 0.95,  # High confidence with real AI
            "reasoning": "Generated using ChatGPT with dbt context and best practices",
            "warnings": validation_result.get("warnings", []),
            "suggestions": validation_result.get("suggestions", [])
        }
    
    def _extract_model_name(self, sql: str, prompt: str) -> str:
        """Extract or generate appropriate model name"""
        
        # Try to extract from prompt keywords
        prompt_lower = prompt.lower()
        
        # Common patterns
        if "revenue" in prompt_lower:
            if "daily" in prompt_lower:
                return "daily_revenue_analysis"
            elif "monthly" in prompt_lower:
                return "monthly_revenue_analysis"
            else:
                return "revenue_analysis"
        
        if "customer" in prompt_lower:
            if "lifetime" in prompt_lower or "ltv" in prompt_lower:
                return "customer_lifetime_value"
            elif "segment" in prompt_lower:
                return "customer_segmentation"
            else:
                return "customer_analysis"
        
        if "order" in prompt_lower:
            if "funnel" in prompt_lower:
                return "order_funnel_analysis"
            else:
                return "order_analysis"
        
        if "product" in prompt_lower:
            return "product_analysis"
        
        # Default fallback
        return "chatgpt_generated_model"
    
    def _extract_materialization(self, sql: str) -> str:
        """Extract materialization from SQL config"""
        
        # Look for config block
        if "materialized=" in sql:
            for line in sql.split('\n'):
                if "materialized=" in line:
                    if "'table'" in line or '"table"' in line:
                        return "table"
                    elif "'incremental'" in line or '"incremental"' in line:
                        return "incremental"
                    else:
                        return "view"
        
        return "view"  # Default
    
    def _validate_sql(self, sql: str) -> Dict[str, List[str]]:
        """Basic validation of generated SQL"""
        
        warnings = []
        suggestions = []
        
        # Check for dbt ref functions
        if "from " in sql.lower() and "{{ ref(" not in sql and "{{ source(" not in sql:
            warnings.append("SQL contains table references without {{ ref() }} or {{ source() }} functions")
        
        # Check for basic SQL structure
        if "select" not in sql.lower():
            warnings.append("SQL does not contain a SELECT statement")
        
        # Check for CTE usage (best practice)
        if "with " not in sql.lower() and len(sql.split('\n')) > 10:
            suggestions.append("Consider using CTEs for better readability in complex queries")
        
        # Check for comments
        if "--" not in sql and "/*" not in sql:
            suggestions.append("Consider adding comments to explain business logic")
        
        return {
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test ChatGPT API connection"""
        if not self.is_available():
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }
        
        try:
            # Simple test call
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for testing
                messages=[
                    {"role": "user", "content": "Say 'Connection successful' if you can read this."}
                ],
                max_tokens=10
            )
            
            return {
                "success": True,
                "message": "ChatGPT API connection successful",
                "model": self.model_name,
                "response": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"ChatGPT API connection failed: {str(e)}"
            }

# Utility function for easy testing
async def test_chatgpt_service():
    """Test the ChatGPT service"""
    config = Config()
    service = ChatGPTService(config)
    
    # Test connection
    connection_result = await service.test_connection()
    print("Connection test:", connection_result)
    
    if connection_result["success"]:
        # Test SQL generation
        result = await service.generate_sql(
            "Create a model that shows daily revenue by combining order and product data",
            {"materialization": "view", "business_area": "analytics"}
        )
        
        print("\nSQL Generation test:")
        print(f"Success: {result['success']}")
        if result["success"]:
            print(f"Model name: {result['model_name']}")
            print(f"SQL preview: {result['sql'][:200]}...")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_chatgpt_service())