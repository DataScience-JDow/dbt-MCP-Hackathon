"""
Prompt processing and intent recognition service for dbt MCP Hackathon Project
"""
import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from ..shared.models import ModelMetadata
from .model_service import ModelMetadataService

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Types of user intents for model generation"""
    CREATE_MODEL = "create_model"
    JOIN_TABLES = "join_tables"
    AGGREGATE_DATA = "aggregate_data"
    FILTER_DATA = "filter_data"
    TRANSFORM_DATA = "transform_data"
    EXPLORE_DATA = "explore_data"
    UNKNOWN = "unknown"

@dataclass
class TableReference:
    """Reference to a table or model in the prompt"""
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None
    is_model: bool = False
    confidence: float = 0.0

@dataclass
class JoinRequirement:
    """Join requirement extracted from prompt"""
    left_table: str
    right_table: str
    join_type: str = "inner"  # inner, left, right, full
    join_condition: Optional[str] = None
    confidence: float = 0.0

@dataclass
class PromptAnalysis:
    """Analysis result of a user prompt"""
    intent: IntentType
    confidence: float
    table_references: List[TableReference]
    join_requirements: List[JoinRequirement]
    filters: List[str]
    aggregations: List[str]
    transformations: List[str]
    context_models: List[ModelMetadata]
    output_name: Optional[str] = None
    materialization: str = "view"
    description: Optional[str] = None

class PromptProcessor:
    """Service for processing natural language prompts and extracting intent"""
    
    def __init__(self, model_service: ModelMetadataService):
        self.model_service = model_service
        self._load_patterns()
    
    def _load_patterns(self):
        """Load regex patterns for intent recognition"""
        # Intent patterns
        self.intent_patterns = {
            IntentType.CREATE_MODEL: [
                r"create\s+(?:a\s+)?(?:new\s+)?model",
                r"build\s+(?:a\s+)?(?:new\s+)?model",
                r"generate\s+(?:a\s+)?(?:new\s+)?model",
                r"make\s+(?:a\s+)?(?:new\s+)?model",
                r"i\s+(?:want|need)\s+(?:a\s+)?(?:new\s+)?model"
            ],
            IntentType.JOIN_TABLES: [
                r"join\s+\w+\s+(?:with|and|to)\s+\w+",
                r"combine\s+\w+\s+(?:with|and)\s+\w+",
                r"merge\s+\w+\s+(?:with|and)\s+\w+",
                r"(?:inner|left|right|full)\s+join",
                r"connect\s+\w+\s+(?:with|and|to)\s+\w+"
            ],
            IntentType.AGGREGATE_DATA: [
                r"(?:sum|count|avg|average|min|max|group\s+by)",
                r"aggregate\s+",
                r"total\s+",
                r"calculate\s+(?:the\s+)?(?:sum|count|average|total)",
                r"group\s+.*\s+by"
            ],
            IntentType.FILTER_DATA: [
                r"filter\s+",
                r"where\s+",
                r"only\s+(?:show|include|get)",
                r"exclude\s+",
                r"(?:greater|less)\s+than",
                r"between\s+.*\s+and"
            ],
            IntentType.TRANSFORM_DATA: [
                r"transform\s+",
                r"convert\s+",
                r"calculate\s+",
                r"derive\s+",
                r"add\s+(?:a\s+)?(?:new\s+)?column",
                r"create\s+(?:a\s+)?(?:new\s+)?field"
            ]
        }
        
        # Table reference patterns
        self.table_patterns = [
            r"(?:from|join|with|and|table|model)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:table|model)",
            r"`([a-zA-Z_][a-zA-Z0-9_]*)`",
            r"'([a-zA-Z_][a-zA-Z0-9_]*)'",
            r'"([a-zA-Z_][a-zA-Z0-9_]*)"'
        ]
        
        # Join type patterns
        self.join_patterns = {
            "inner": [r"inner\s+join", r"join\s+(?!.*(?:left|right|full))"],
            "left": [r"left\s+(?:outer\s+)?join"],
            "right": [r"right\s+(?:outer\s+)?join"],
            "full": [r"full\s+(?:outer\s+)?join", r"full\s+join"]
        }
        
        # Output name patterns
        self.output_patterns = [
            r"(?:call|name)\s+(?:it|this|the\s+model)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"(?:as|called)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"create\s+(?:a\s+)?model\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"model\s+(?:named|called)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        ]
        
        # Materialization patterns
        self.materialization_patterns = {
            "table": [r"(?:as\s+)?(?:a\s+)?table", r"materialize\s+(?:as\s+)?table"],
            "view": [r"(?:as\s+)?(?:a\s+)?view", r"materialize\s+(?:as\s+)?view"],
            "incremental": [r"incremental", r"incrementally"]
        }
    
    def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """Analyze a user prompt and extract intent and requirements"""
        prompt_lower = prompt.lower()
        
        # Detect intent
        intent, intent_confidence = self._detect_intent(prompt_lower)
        
        # Extract table references
        table_references = self._extract_table_references(prompt)
        
        # Extract join requirements
        join_requirements = self._extract_join_requirements(prompt_lower, table_references)
        
        # Extract output name
        output_name = self._extract_output_name(prompt_lower)
        
        # Extract materialization
        materialization = self._extract_materialization(prompt_lower)
        
        # Extract filters, aggregations, transformations
        filters = self._extract_filters(prompt_lower)
        aggregations = self._extract_aggregations(prompt_lower)
        transformations = self._extract_transformations(prompt_lower)
        
        # Build context from existing models
        context_models = self._build_context(table_references)
        
        # Generate description
        description = self._generate_description(prompt, intent, table_references)
        
        return PromptAnalysis(
            intent=intent,
            confidence=intent_confidence,
            table_references=table_references,
            join_requirements=join_requirements,
            output_name=output_name,
            materialization=materialization,
            description=description,
            filters=filters,
            aggregations=aggregations,
            transformations=transformations,
            context_models=context_models
        )
    
    def _detect_intent(self, prompt: str) -> Tuple[IntentType, float]:
        """Detect the primary intent of the prompt"""
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    matches += 1
                    score += 1.0
            
            if matches > 0:
                # Normalize score by number of patterns
                intent_scores[intent_type] = score / len(patterns)
        
        if not intent_scores:
            return IntentType.UNKNOWN, 0.0
        
        # Return intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]
    
    def _extract_table_references(self, prompt: str) -> List[TableReference]:
        """Extract table/model references from the prompt"""
        references = []
        found_names = set()
        
        # Extract using patterns
        for pattern in self.table_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                table_name = match.group(1)
                if table_name and table_name.lower() not in found_names:
                    found_names.add(table_name.lower())
                    
                    # Check if it's an existing model
                    is_model = self._is_existing_model(table_name)
                    confidence = 0.8 if is_model else 0.6
                    
                    references.append(TableReference(
                        name=table_name,
                        is_model=is_model,
                        confidence=confidence
                    ))
        
        # Also check for known model names in the prompt
        all_models = self.model_service.get_all_models()
        for model in all_models:
            if (model.name.lower() in prompt.lower() and 
                model.name.lower() not in found_names):
                found_names.add(model.name.lower())
                references.append(TableReference(
                    name=model.name,
                    is_model=True,
                    confidence=0.9
                ))
        
        return references
    
    def _extract_join_requirements(self, prompt: str, 
                                 table_refs: List[TableReference]) -> List[JoinRequirement]:
        """Extract join requirements from the prompt"""
        join_requirements = []
        
        if len(table_refs) < 2:
            return join_requirements
        
        # Detect join type
        join_type = "inner"  # default
        for jtype, patterns in self.join_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    join_type = jtype
                    break
        
        # For now, create a simple join between first two tables
        # In a more sophisticated implementation, we would parse the specific join conditions
        if len(table_refs) >= 2:
            join_requirements.append(JoinRequirement(
                left_table=table_refs[0].name,
                right_table=table_refs[1].name,
                join_type=join_type,
                confidence=0.7
            ))
        
        return join_requirements
    
    def _extract_output_name(self, prompt: str) -> Optional[str]:
        """Extract the desired output model name from the prompt"""
        for pattern in self.output_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_materialization(self, prompt: str) -> str:
        """Extract the desired materialization type from the prompt"""
        for mat_type, patterns in self.materialization_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    return mat_type
        return "view"  # default
    
    def _extract_filters(self, prompt: str) -> List[str]:
        """Extract filter conditions from the prompt"""
        filters = []
        
        # Look for WHERE-like conditions
        where_patterns = [
            r"where\s+([^,\n]+)",
            r"filter\s+(?:by\s+)?([^,\n]+)",
            r"only\s+(?:show|include|get)\s+([^,\n]+)"
        ]
        
        for pattern in where_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                condition = match.group(1).strip()
                if condition:
                    filters.append(condition)
        
        return filters
    
    def _extract_aggregations(self, prompt: str) -> List[str]:
        """Extract aggregation functions from the prompt"""
        aggregations = []
        
        agg_patterns = [
            r"(sum\s+(?:of\s+)?\w+)",
            r"(count\s+(?:of\s+)?\w+)",
            r"(avg|average\s+(?:of\s+)?\w+)",
            r"(min\s+(?:of\s+)?\w+)",
            r"(max\s+(?:of\s+)?\w+)",
            r"(group\s+by\s+\w+)"
        ]
        
        for pattern in agg_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                agg = match.group(1).strip()
                if agg:
                    aggregations.append(agg)
        
        return aggregations
    
    def _extract_transformations(self, prompt: str) -> List[str]:
        """Extract transformation requirements from the prompt"""
        transformations = []
        
        transform_patterns = [
            r"(calculate\s+[^,\n]+)",
            r"(convert\s+[^,\n]+)",
            r"(add\s+(?:a\s+)?(?:new\s+)?column\s+[^,\n]+)",
            r"(create\s+(?:a\s+)?(?:new\s+)?field\s+[^,\n]+)"
        ]
        
        for pattern in transform_patterns:
            matches = re.finditer(pattern, prompt, re.IGNORECASE)
            for match in matches:
                transform = match.group(1).strip()
                if transform:
                    transformations.append(transform)
        
        return transformations
    
    def _is_existing_model(self, table_name: str) -> bool:
        """Check if a table name refers to an existing dbt model"""
        model = self.model_service.get_model_by_name(table_name)
        return model is not None
    
    def _build_context(self, table_refs: List[TableReference]) -> List[ModelMetadata]:
        """Build context from referenced models"""
        context_models = []
        
        for table_ref in table_refs:
            if table_ref.is_model:
                model = self.model_service.get_model_by_name(table_ref.name)
                if model:
                    context_models.append(model)
        
        return context_models
    
    def _generate_description(self, prompt: str, intent: IntentType, 
                            table_refs: List[TableReference]) -> Optional[str]:
        """Generate a description for the model based on the prompt"""
        if intent == IntentType.CREATE_MODEL:
            table_names = [ref.name for ref in table_refs]
            if table_names:
                return f"Model generated from prompt: {prompt[:100]}... using tables: {', '.join(table_names)}"
            else:
                return f"Model generated from prompt: {prompt[:100]}..."
        
        return None
    
    def extract_context_for_generation(self, analysis: PromptAnalysis) -> Dict[str, Any]:
        """Extract context information for AI model generation"""
        context = {
            "intent": analysis.intent.value,
            "tables": [],
            "joins": [],
            "schema_info": {},
            "existing_models": []
        }
        
        # Add table information
        for table_ref in analysis.table_references:
            table_info = {
                "name": table_ref.name,
                "is_model": table_ref.is_model,
                "alias": table_ref.alias
            }
            context["tables"].append(table_info)
        
        # Add join information
        for join_req in analysis.join_requirements:
            join_info = {
                "left_table": join_req.left_table,
                "right_table": join_req.right_table,
                "join_type": join_req.join_type,
                "condition": join_req.join_condition
            }
            context["joins"].append(join_info)
        
        # Add schema information from context models
        for model in analysis.context_models:
            schema_info = {
                "name": model.name,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "description": col.description
                    } for col in model.columns
                ],
                "materialization": model.materialization,
                "description": model.description
            }
            context["schema_info"][model.name] = schema_info
            context["existing_models"].append(model.name)
        
        return context