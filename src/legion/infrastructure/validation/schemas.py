"""Pydantic Validation Schemas for API Endpoints"""

from typing import Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator

from .sanitizer import InputSanitizer


class ValidationSchemas:
    """Collection of validation schemas for Legion API"""
    pass


# Task Management Schemas

class TaskCreateSchema(BaseModel):
    """Schema for creating new tasks"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=5000)
    task_type: Literal["code_analysis", "code_review", "deployment", "monitoring", "custom"]
    priority: int = Field(default=3, ge=1, le=5)
    metadata: dict = Field(default_factory=dict)
    
    @validator('title', 'description')
    def sanitize_text(cls, v):
        """Remove HTML and dangerous characters"""
        return InputSanitizer.sanitize_html(v)
    
    @validator('metadata')
    def sanitize_metadata(cls, v):
        """Sanitize metadata dictionary"""
        return InputSanitizer.sanitize_dict(v)
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Analyze repository",
                "description": "Perform code quality analysis",
                "task_type": "code_analysis",
                "priority": 4,
                "metadata": {"repo": "user/repo"}
            }
        }


class TaskExecuteSchema(BaseModel):
    """Schema for task execution requests"""
    task_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]{1,64}$')
    command: Literal["start", "stop", "pause", "resume", "status"]
    parameters: dict = Field(default_factory=dict)
    
    @validator('task_id')
    def validate_task_id(cls, v):
        """Ensure task_id is safe"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("task_id must be alphanumeric")
        return v
    
    @validator('parameters')
    def sanitize_parameters(cls, v):
        """Remove dangerous patterns from parameters"""
        return InputSanitizer.sanitize_dict(v)


class TaskUpdateSchema(BaseModel):
    """Schema for updating tasks"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[Literal["pending", "running", "completed", "failed", "cancelled"]] = None
    
    @validator('title', 'description')
    def sanitize_text(cls, v):
        if v is not None:
            return InputSanitizer.sanitize_html(v)
        return v


# Agent Management Schemas

class AgentCreateSchema(BaseModel):
    """Schema for creating agents"""
    name: str = Field(..., min_length=3, max_length=100, regex=r'^[a-zA-Z0-9_-]+$')
    agent_type: str = Field(..., min_length=3, max_length=50)
    config: dict = Field(default_factory=dict)
    
    @validator('config')
    def sanitize_config(cls, v):
        return InputSanitizer.sanitize_dict(v)


class AgentExecuteSchema(BaseModel):
    """Schema for agent execution"""
    agent_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]{1,64}$')
    action: str = Field(..., min_length=1, max_length=100)
    payload: dict = Field(default_factory=dict)
    
    @validator('action')
    def validate_action(cls, v):
        """Whitelist allowed actions"""
        allowed_actions = ["execute", "status", "stop", "restart", "configure"]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v
    
    @validator('payload')
    def sanitize_payload(cls, v):
        return InputSanitizer.sanitize_dict(v)


# File Operation Schemas

class FileAccessSchema(BaseModel):
    """Schema for file access requests"""
    path: str = Field(..., min_length=1, max_length=500)
    operation: Literal["read", "write", "delete", "list"]
    
    @validator('path')
    def validate_path(cls, v):
        """Prevent path traversal"""
        return InputSanitizer.sanitize_path(v)


# Search/Query Schemas

class SearchSchema(BaseModel):
    """Schema for search queries"""
    query: str = Field(..., min_length=1, max_length=500)
    filters: dict = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize search query"""
        return InputSanitizer.sanitize_sql(v)
    
    @validator('filters')
    def sanitize_filters(cls, v):
        return InputSanitizer.sanitize_dict(v)
