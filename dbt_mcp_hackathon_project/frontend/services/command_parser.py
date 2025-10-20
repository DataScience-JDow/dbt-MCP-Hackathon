"""
Command parser for recognizing and routing user requests
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class CommandType(Enum):
    """Types of commands the system can handle"""
    MODEL_GENERATION = "model_generation"
    MODEL_EXPLORATION = "model_exploration"
    MODEL_COMPILATION = "model_compilation"
    MODEL_EXECUTION = "model_execution"
    HELP = "help"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"

@dataclass
class ParsedCommand:
    """Parsed command with extracted information"""
    command_type: CommandType
    intent: str
    entities: Dict[str, Any]
    confidence: float
    raw_input: str
    suggested_action: Optional[str] = None

class CommandParser:
    """Parser for natural language commands in dbt MCP Hackathon Project"""
    
    def __init__(self):
        self.generation_patterns = [
            # Model creation patterns
            (r'\b(create|generate|build|make)\b.*\b(model|table|view)\b', 0.9),
            (r'\b(create|generate|build|make)\b.*\b(join|aggregate|sum|count|group)\b', 0.8),
            (r'\b(create|generate|build|make)\b.*\b(mart|staging|intermediate)\b', 0.9),
            (r'\b(new|fresh)\b.*\b(model|table|view)\b', 0.8),
            (r'\b(write|code|sql)\b.*\b(model|query)\b', 0.7),
        ]
        
        self.exploration_patterns = [
            # Model exploration patterns
            (r'\b(show|list|find|explore|browse|display)\b.*\b(model|table|view)s?\b', 0.9),
            (r'\b(what|which|how many)\b.*\b(model|table|view)s?\b', 0.8),
            (r'\b(dependencies|depends|lineage|upstream|downstream)\b', 0.9),
            (r'\b(schema|structure|columns|fields)\b.*\b(model|table)\b', 0.8),
            (r'\b(search|filter|look for)\b.*\b(model|table|view)s?\b', 0.8),
        ]
        
        self.compilation_patterns = [
            # Compilation patterns
            (r'\b(compile|check|validate|syntax)\b', 0.9),
            (r'\b(test|verify)\b.*\b(sql|model|code)\b', 0.8),
            (r'\b(parse|lint)\b', 0.7),
        ]
        
        self.execution_patterns = [
            # Execution patterns
            (r'\b(run|execute|build)\b.*\b(model|table|view)\b', 0.9),
            (r'\b(materialize|create table|create view)\b', 0.8),
            (r'\b(refresh|update|rebuild)\b.*\b(model|data)\b', 0.8),
        ]
        
        self.help_patterns = [
            # Help patterns
            (r'\b(help|how|what|guide|tutorial|explain)\b', 0.8),
            (r'\b(can you|could you|please)\b.*\b(help|show|explain)\b', 0.7),
            (r'^\?|^help$', 0.9),
        ]
        
        # Entity extraction patterns
        self.model_name_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        self.table_reference_pattern = r'\b(raw_|stg_|int_|fct_|dim_|mart_)?([a-zA-Z_][a-zA-Z0-9_]*)\b'
        self.join_pattern = r'\b(join|inner join|left join|right join|full join)\b'
        self.aggregation_pattern = r'\b(sum|count|avg|max|min|group by|having)\b'
    
    def parse_command(self, user_input: str) -> ParsedCommand:
        """Parse user input and return structured command information"""
        
        user_input_lower = user_input.lower().strip()
        
        # Try to match against different command types
        generation_match = self._match_patterns(user_input_lower, self.generation_patterns)
        exploration_match = self._match_patterns(user_input_lower, self.exploration_patterns)
        compilation_match = self._match_patterns(user_input_lower, self.compilation_patterns)
        execution_match = self._match_patterns(user_input_lower, self.execution_patterns)
        help_match = self._match_patterns(user_input_lower, self.help_patterns)
        
        # Find the best match
        matches = [
            (CommandType.MODEL_GENERATION, generation_match),
            (CommandType.MODEL_EXPLORATION, exploration_match),
            (CommandType.MODEL_COMPILATION, compilation_match),
            (CommandType.MODEL_EXECUTION, execution_match),
            (CommandType.HELP, help_match),
        ]
        
        # Sort by confidence and get the best match
        best_match = max(matches, key=lambda x: x[1])
        command_type, confidence = best_match
        
        # If confidence is too low, classify as general query or unknown
        if confidence < 0.5:
            if any(word in user_input_lower for word in ['dbt', 'model', 'sql', 'data', 'table']):
                command_type = CommandType.GENERAL_QUERY
                confidence = 0.6
            else:
                command_type = CommandType.UNKNOWN
                confidence = 0.3
        
        # Extract entities based on command type
        entities = self._extract_entities(user_input, command_type)
        
        # Generate intent description
        intent = self._generate_intent(command_type, entities, user_input)
        
        # Suggest action
        suggested_action = self._suggest_action(command_type, entities)
        
        return ParsedCommand(
            command_type=command_type,
            intent=intent,
            entities=entities,
            confidence=confidence,
            raw_input=user_input,
            suggested_action=suggested_action
        )
    
    def _match_patterns(self, text: str, patterns: List[Tuple[str, float]]) -> float:
        """Match text against a list of patterns and return highest confidence"""
        
        max_confidence = 0.0
        
        for pattern, base_confidence in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                max_confidence = max(max_confidence, base_confidence)
        
        return max_confidence
    
    def _extract_entities(self, text: str, command_type: CommandType) -> Dict[str, Any]:
        """Extract relevant entities from text based on command type"""
        
        entities = {}
        
        # Extract model/table names
        model_names = re.findall(self.model_name_pattern, text)
        if model_names:
            # Filter out common words
            common_words = {'the', 'and', 'or', 'with', 'from', 'to', 'in', 'on', 'at', 'by', 'for', 'of', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
            entities['model_names'] = [name for name in model_names if name.lower() not in common_words]
        
        # Extract table references (with prefixes)
        table_refs = re.findall(self.table_reference_pattern, text)
        if table_refs:
            entities['table_references'] = [f"{prefix}{name}" if prefix else name for prefix, name in table_refs]
        
        # Extract join information
        if re.search(self.join_pattern, text, re.IGNORECASE):
            entities['has_joins'] = True
            join_matches = re.findall(self.join_pattern, text, re.IGNORECASE)
            entities['join_types'] = join_matches
        
        # Extract aggregation information
        if re.search(self.aggregation_pattern, text, re.IGNORECASE):
            entities['has_aggregation'] = True
            agg_matches = re.findall(self.aggregation_pattern, text, re.IGNORECASE)
            entities['aggregation_functions'] = agg_matches
        
        # Extract materialization hints
        materialization_patterns = {
            'table': r'\b(table|persist|store)\b',
            'view': r'\b(view|virtual)\b',
            'incremental': r'\b(incremental|append|update)\b',
            'ephemeral': r'\b(ephemeral|temporary|temp)\b'
        }
        
        for mat_type, pattern in materialization_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                entities['materialization'] = mat_type
                break
        
        # Extract layer hints
        layer_patterns = {
            'staging': r'\b(staging|stg|raw|source)\b',
            'intermediate': r'\b(intermediate|int|transform)\b',
            'mart': r'\b(mart|final|output|report)\b'
        }
        
        for layer, pattern in layer_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                entities['layer'] = layer
                break
        
        # Extract business concepts
        business_concepts = [
            'customer', 'order', 'product', 'revenue', 'sales', 'profit',
            'lifetime value', 'churn', 'retention', 'conversion',
            'inventory', 'supply', 'demand', 'forecast'
        ]
        
        found_concepts = []
        for concept in business_concepts:
            if concept in text.lower():
                found_concepts.append(concept)
        
        if found_concepts:
            entities['business_concepts'] = found_concepts
        
        return entities
    
    def _generate_intent(self, command_type: CommandType, entities: Dict[str, Any], raw_input: str) -> str:
        """Generate a human-readable intent description"""
        
        if command_type == CommandType.MODEL_GENERATION:
            if entities.get('business_concepts'):
                concepts = ', '.join(entities['business_concepts'])
                return f"Generate a model related to: {concepts}"
            elif entities.get('table_references'):
                tables = ', '.join(entities['table_references'][:3])  # Limit to first 3
                return f"Generate a model using tables: {tables}"
            else:
                return "Generate a new dbt model"
        
        elif command_type == CommandType.MODEL_EXPLORATION:
            if entities.get('model_names'):
                models = ', '.join(entities['model_names'][:3])
                return f"Explore models: {models}"
            elif entities.get('layer'):
                return f"Explore {entities['layer']} layer models"
            else:
                return "Explore existing dbt models"
        
        elif command_type == CommandType.MODEL_COMPILATION:
            if entities.get('model_names'):
                models = ', '.join(entities['model_names'][:3])
                return f"Compile models: {models}"
            else:
                return "Compile and validate models"
        
        elif command_type == CommandType.MODEL_EXECUTION:
            if entities.get('model_names'):
                models = ', '.join(entities['model_names'][:3])
                return f"Execute models: {models}"
            else:
                return "Execute dbt models"
        
        elif command_type == CommandType.HELP:
            return "Get help and guidance"
        
        elif command_type == CommandType.GENERAL_QUERY:
            return "General dbt-related question"
        
        else:
            return "Unknown request"
    
    def _suggest_action(self, command_type: CommandType, entities: Dict[str, Any]) -> Optional[str]:
        """Suggest the next action based on parsed command"""
        
        if command_type == CommandType.MODEL_GENERATION:
            return "generate_model"
        elif command_type == CommandType.MODEL_EXPLORATION:
            if entities.get('model_names'):
                return "show_model_details"
            else:
                return "list_models"
        elif command_type == CommandType.MODEL_COMPILATION:
            return "compile_model"
        elif command_type == CommandType.MODEL_EXECUTION:
            return "run_model"
        elif command_type == CommandType.HELP:
            return "show_help"
        else:
            return None

# Global parser instance
_command_parser = None

def get_command_parser() -> CommandParser:
    """Get or create command parser instance"""
    global _command_parser
    
    if _command_parser is None:
        _command_parser = CommandParser()
    
    return _command_parser