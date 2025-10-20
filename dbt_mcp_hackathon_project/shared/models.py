"""
Shared data models for dbt MCP Hackathon Project
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

@dataclass
class ColumnInfo:
    """Information about a model column"""
    name: str
    data_type: str
    description: Optional[str] = None
    tests: List[str] = None
    
    def __post_init__(self):
        if self.tests is None:
            self.tests = []

@dataclass
class ModelMetadata:
    """Metadata for a dbt model"""
    name: str
    path: str
    description: Optional[str] = None
    columns: List[ColumnInfo] = None
    depends_on: List[str] = None
    referenced_by: List[str] = None
    materialization: str = "view"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.columns is None:
            self.columns = []
        if self.depends_on is None:
            self.depends_on = []
        if self.referenced_by is None:
            self.referenced_by = []
        if self.tags is None:
            self.tags = []

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_type: str = "text"  # 'text', 'code', 'data', 'error'
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ModelGenerationRequest(BaseModel):
    """Request for generating a new model"""
    prompt: str
    context: List[str] = []
    output_name: Optional[str] = None
    materialization: str = "view"
    description: Optional[str] = None

class ErrorResponse(BaseModel):
    """Structured error response"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    recoverable: bool = True