"""
AI service for SQL generation using Kiro AI
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..shared.models import ModelGenerationRequest
from .prompt_processor import PromptAnalysis, IntentType

logger = logging.getLogger(__name__)

@dataclass
class SQLGenerationResult:
    """Result of SQL generation"""
    sql: str
    model_name: str
    description: Optional[str]
    materialization: str
    confidence: float
    reasoning: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class KiroAIService:
    """Service for integrating with Kiro AI for SQL code generation"""
    
    def __init__(self):
        self.dbt_context = self._build_dbt_context()
    
    def _build_dbt_context(self) -> str:
        """Build dbt-specific context for AI prompts"""
        return """
You are an expert dbt developer. When generating SQL for dbt models:

1. Use dbt best practices:
   - Use {{ ref('model_name') }} for model references
   - Use {{ source('schema', 'table') }} for source table references
   - Include proper CTEs (Common Table Expressions) for readability
   - Use meaningful column aliases
   - Add appropriate comments

2. SQL Style Guidelines:
   - Use lowercase for SQL keywords
   - Use snake_case for column names
   - Indent nested queries properly
   - Use trailing commas in SELECT statements
   - Group related columns together

3. dbt Materialization Types:
   - view: For lightweight transformations (default)
   - table: For heavy transformations or frequently queried models
   - incremental: For large datasets that can be processed incrementally

4. Common dbt Patterns:
   - Staging models: Clean and standardize raw data
   - Intermediate models: Business logic transformations
   - Mart models: Final business-ready datasets

5. Always validate that:
   - Referenced models exist in the context provided
   - Column names are consistent with source schemas
   - Join conditions are properly specified
   - Aggregations are appropriate for the use case
"""
    
    def generate_sql_from_analysis(self, analysis: PromptAnalysis, 
                                 original_prompt: str) -> SQLGenerationResult:
        """Generate SQL code from prompt analysis"""
        try:
            # Build the AI prompt
            ai_prompt = self._build_ai_prompt(analysis, original_prompt)
            
            # For now, we'll create a mock implementation
            # In a real implementation, this would call Kiro AI API
            sql_result = self._mock_kiro_ai_generation(analysis, ai_prompt)
            
            return sql_result
            
        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            raise
    
    def _build_ai_prompt(self, analysis: PromptAnalysis, original_prompt: str) -> str:
        """Build a comprehensive prompt for Kiro AI"""
        prompt_parts = [
            self.dbt_context,
            "\n## User Request:",
            f"Original prompt: {original_prompt}",
            f"Intent: {analysis.intent.value}",
            f"Requested materialization: {analysis.materialization}",
        ]
        
        if analysis.output_name:
            prompt_parts.append(f"Requested model name: {analysis.output_name}")
        
        # Add table context
        if analysis.table_references:
            prompt_parts.append("\n## Available Tables/Models:")
            for table_ref in analysis.table_references:
                ref_type = "dbt model" if table_ref.is_model else "source table"
                prompt_parts.append(f"- {table_ref.name} ({ref_type})")
        
        # Add schema information
        if analysis.context_models:
            prompt_parts.append("\n## Schema Information:")
            for model in analysis.context_models:
                prompt_parts.append(f"\n### {model.name} (materialized as {model.materialization})")
                if model.description:
                    prompt_parts.append(f"Description: {model.description}")
                prompt_parts.append("Columns:")
                for col in model.columns:
                    col_desc = f" - {col.description}" if col.description else ""
                    prompt_parts.append(f"  - {col.name} ({col.data_type}){col_desc}")
        
        # Add join requirements
        if analysis.join_requirements:
            prompt_parts.append("\n## Join Requirements:")
            for join_req in analysis.join_requirements:
                prompt_parts.append(
                    f"- {join_req.join_type.upper()} JOIN {join_req.left_table} "
                    f"with {join_req.right_table}"
                )
                if join_req.join_condition:
                    prompt_parts.append(f"  Condition: {join_req.join_condition}")
        
        # Add filters
        if analysis.filters:
            prompt_parts.append("\n## Filters:")
            for filter_cond in analysis.filters:
                prompt_parts.append(f"- {filter_cond}")
        
        # Add aggregations
        if analysis.aggregations:
            prompt_parts.append("\n## Aggregations:")
            for agg in analysis.aggregations:
                prompt_parts.append(f"- {agg}")
        
        # Add transformations
        if analysis.transformations:
            prompt_parts.append("\n## Transformations:")
            for transform in analysis.transformations:
                prompt_parts.append(f"- {transform}")
        
        # Add generation instructions
        prompt_parts.extend([
            "\n## Instructions:",
            "Generate a complete dbt model SQL file that:",
            "1. Follows dbt best practices and the style guidelines above",
            "2. Uses appropriate {{ ref() }} and {{ source() }} functions",
            "3. Includes meaningful CTEs and column aliases",
            "4. Handles the requested transformations, joins, and filters",
            "5. Is ready to be saved as a .sql file in the models directory",
            "",
            "Return only the SQL code without any markdown formatting or explanations."
        ])
        
        return "\n".join(prompt_parts)
    
    def _mock_kiro_ai_generation(self, analysis: PromptAnalysis, 
                               ai_prompt: str) -> SQLGenerationResult:
        """Mock implementation of Kiro AI generation"""
        # This is a simplified mock implementation
        # In reality, this would call the actual Kiro AI API
        
        model_name = analysis.output_name or self._generate_model_name(analysis)
        
        # Generate basic SQL based on analysis
        sql_parts = []
        
        # Add model configuration
        config_lines = []
        if analysis.materialization != "view":
            config_lines.append(f"materialized='{analysis.materialization}'")
        
        if config_lines:
            sql_parts.append("{{")
            sql_parts.append("  config(")
            sql_parts.append(f"    {', '.join(config_lines)}")
            sql_parts.append("  )")
            sql_parts.append("}}")
            sql_parts.append("")
        
        # Generate SQL based on intent
        if analysis.intent == IntentType.JOIN_TABLES and len(analysis.table_references) >= 2:
            sql_parts.extend(self._generate_join_sql(analysis))
        elif analysis.intent == IntentType.AGGREGATE_DATA:
            sql_parts.extend(self._generate_aggregate_sql(analysis))
        elif analysis.intent == IntentType.FILTER_DATA:
            sql_parts.extend(self._generate_filter_sql(analysis))
        elif analysis.intent == IntentType.TRANSFORM_DATA:
            sql_parts.extend(self._generate_transform_sql(analysis))
        else:
            # Default: simple select from first table
            sql_parts.extend(self._generate_simple_select_sql(analysis))
        
        sql = "\n".join(sql_parts)
        
        return SQLGenerationResult(
            sql=sql,
            model_name=model_name,
            description=analysis.description,
            materialization=analysis.materialization,
            confidence=0.8,  # Mock confidence
            reasoning="Generated using pattern-based mock implementation"
        )
    
    def _generate_model_name(self, analysis: PromptAnalysis) -> str:
        """Generate a model name based on analysis"""
        if analysis.table_references:
            # Use first table as base
            base_name = analysis.table_references[0].name
            
            if analysis.intent == IntentType.JOIN_TABLES:
                return f"joined_{base_name}"
            elif analysis.intent == IntentType.AGGREGATE_DATA:
                return f"agg_{base_name}"
            elif analysis.intent == IntentType.FILTER_DATA:
                return f"filtered_{base_name}"
            elif analysis.intent == IntentType.TRANSFORM_DATA:
                return f"transformed_{base_name}"
            else:
                return f"new_{base_name}"
        
        return "generated_model"
    
    def _generate_join_sql(self, analysis: PromptAnalysis) -> List[str]:
        """Generate SQL for join operations"""
        sql_parts = []
        
        if len(analysis.table_references) < 2:
            return self._generate_simple_select_sql(analysis)
        
        left_table = analysis.table_references[0]
        right_table = analysis.table_references[1]
        
        # Determine reference function
        left_ref = f"{{{{ ref('{left_table.name}') }}}}" if left_table.is_model else left_table.name
        right_ref = f"{{{{ ref('{right_table.name}') }}}}" if right_table.is_model else right_table.name
        
        join_type = "inner"
        if analysis.join_requirements:
            join_type = analysis.join_requirements[0].join_type
        
        sql_parts.extend([
            "with",
            "",
            f"left_table as (",
            f"  select * from {left_ref}",
            "),",
            "",
            f"right_table as (",
            f"  select * from {right_ref}",
            "),",
            "",
            "final as (",
            "  select",
            "    left_table.*,",
            "    right_table.*",
            "  from left_table",
            f"  {join_type} join right_table",
            "    on left_table.id = right_table.id  -- Adjust join condition as needed",
        ])
        
        # Add filters if any
        if analysis.filters:
            sql_parts.append("  where")
            for i, filter_cond in enumerate(analysis.filters):
                prefix = "    " if i == 0 else "    and "
                sql_parts.append(f"{prefix}{filter_cond}")
        
        sql_parts.extend([
            ")",
            "",
            "select * from final"
        ])
        
        return sql_parts
    
    def _generate_aggregate_sql(self, analysis: PromptAnalysis) -> List[str]:
        """Generate SQL for aggregation operations"""
        sql_parts = []
        
        if not analysis.table_references:
            return ["select 1 as placeholder"]
        
        table_ref = analysis.table_references[0]
        ref_func = f"{{{{ ref('{table_ref.name}') }}}}" if table_ref.is_model else table_ref.name
        
        sql_parts.extend([
            "with",
            "",
            "source_data as (",
            f"  select * from {ref_func}",
            "),",
            "",
            "aggregated as (",
            "  select",
        ])
        
        # Add aggregations if specified
        if analysis.aggregations:
            for agg in analysis.aggregations:
                sql_parts.append(f"    {agg},")
        else:
            sql_parts.extend([
                "    count(*) as row_count,",
                "    count(distinct id) as unique_ids  -- Adjust columns as needed",
            ])
        
        # Remove trailing comma from last line
        if sql_parts[-1].endswith(","):
            sql_parts[-1] = sql_parts[-1][:-1]
        
        sql_parts.extend([
            "  from source_data",
        ])
        
        # Add group by if needed
        if any("group by" in agg.lower() for agg in analysis.aggregations):
            sql_parts.append("  group by 1  -- Adjust grouping columns as needed")
        
        sql_parts.extend([
            ")",
            "",
            "select * from aggregated"
        ])
        
        return sql_parts
    
    def _generate_filter_sql(self, analysis: PromptAnalysis) -> List[str]:
        """Generate SQL for filter operations"""
        sql_parts = []
        
        if not analysis.table_references:
            return ["select 1 as placeholder"]
        
        table_ref = analysis.table_references[0]
        ref_func = f"{{{{ ref('{table_ref.name}') }}}}" if table_ref.is_model else table_ref.name
        
        sql_parts.extend([
            "with",
            "",
            "source_data as (",
            f"  select * from {ref_func}",
            "),",
            "",
            "filtered as (",
            "  select *",
            "  from source_data",
        ])
        
        # Add filters
        if analysis.filters:
            sql_parts.append("  where")
            for i, filter_cond in enumerate(analysis.filters):
                prefix = "    " if i == 0 else "    and "
                sql_parts.append(f"{prefix}{filter_cond}")
        
        sql_parts.extend([
            ")",
            "",
            "select * from filtered"
        ])
        
        return sql_parts
    
    def _generate_transform_sql(self, analysis: PromptAnalysis) -> List[str]:
        """Generate SQL for transformation operations"""
        sql_parts = []
        
        if not analysis.table_references:
            return ["select 1 as placeholder"]
        
        table_ref = analysis.table_references[0]
        ref_func = f"{{{{ ref('{table_ref.name}') }}}}" if table_ref.is_model else table_ref.name
        
        sql_parts.extend([
            "with",
            "",
            "source_data as (",
            f"  select * from {ref_func}",
            "),",
            "",
            "transformed as (",
            "  select",
            "    *,",
        ])
        
        # Add transformations
        if analysis.transformations:
            for transform in analysis.transformations:
                # Simple transformation mapping
                if "calculate" in transform.lower():
                    sql_parts.append("    -- Add calculated fields here")
                elif "convert" in transform.lower():
                    sql_parts.append("    -- Add conversion logic here")
                elif "column" in transform.lower() or "field" in transform.lower():
                    sql_parts.append("    -- Add new column here")
        else:
            sql_parts.append("    current_timestamp as processed_at")
        
        # Remove trailing comma from last line
        if sql_parts[-1].endswith(","):
            sql_parts[-1] = sql_parts[-1][:-1]
        
        sql_parts.extend([
            "  from source_data",
            ")",
            "",
            "select * from transformed"
        ])
        
        return sql_parts
    
    def _generate_simple_select_sql(self, analysis: PromptAnalysis) -> List[str]:
        """Generate simple select SQL"""
        if not analysis.table_references:
            return [
                "-- No table references found in prompt",
                "-- Please specify which tables or models to use",
                "select 1 as placeholder"
            ]
        
        table_ref = analysis.table_references[0]
        ref_func = f"{{{{ ref('{table_ref.name}') }}}}" if table_ref.is_model else table_ref.name
        
        return [
            f"select * from {ref_func}"
        ]
    
    def validate_generated_sql(self, sql: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated SQL for common issues"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        # Check for dbt ref functions
        if "from " in sql.lower() and "{{ ref(" not in sql and "{{ source(" not in sql:
            validation_result["warnings"].append(
                "Consider using {{ ref('model_name') }} for dbt model references"
            )
        
        # Check for basic SQL structure
        if "select" not in sql.lower():
            validation_result["errors"].append("SQL must contain a SELECT statement")
            validation_result["is_valid"] = False
        
        # Check for trailing commas in SELECT
        lines = sql.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.endswith(',') and 
                i < len(lines) - 1 and 
                ('from' in lines[i + 1].lower() or 
                 ')' in lines[i + 1].strip())):
                validation_result["warnings"].append(
                    f"Trailing comma on line {i + 1} may cause issues"
                )
        
        return validation_result
    
    async def call_kiro_ai_api(self, prompt: str) -> str:
        """
        Call the actual Kiro AI API for SQL generation
        This is a placeholder for the real implementation
        """
        # TODO: Implement actual Kiro AI API integration
        # This would involve:
        # 1. Setting up HTTP client
        # 2. Authenticating with Kiro AI
        # 3. Sending the prompt
        # 4. Parsing the response
        # 5. Error handling
        
        raise NotImplementedError(
            "Kiro AI API integration not yet implemented. "
            "Using mock generation for now."
        )