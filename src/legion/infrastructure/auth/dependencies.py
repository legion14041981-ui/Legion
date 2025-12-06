"""FastAPI Dependencies for Authentication"""

from typing import Optional
from functools import wraps

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_manager import JWTManager, TokenData
from .models import User, Role


security = HTTPBearer()
jwt_manager = None  # Initialize in app startup


def init_auth(manager: JWTManager):
    """Initialize global JWT manager"""
    global jwt_manager
    jwt_manager = manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Dependency to get current authenticated user"""
    if not jwt_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized"
        )
    
    token_data = await jwt_manager.validate_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


def require_role(required_role: str):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: TokenData = Depends(get_current_user), **kwargs):
            if required_role not in user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator
