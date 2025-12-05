"""Authentication Models"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class Role(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    READONLY = "readonly"


class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: Optional[str] = None
    roles: list[Role] = [Role.USER]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: str
    session_id: str
    roles: list[str] = []
    exp: datetime


class LoginRequest(BaseModel):
    """Login request payload"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
