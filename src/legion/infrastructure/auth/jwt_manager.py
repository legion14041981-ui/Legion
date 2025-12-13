"""JWT Token Management with Redis Session Store"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
import json

from jose import jwt, JWTError
import redis.asyncio as aioredis
from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: str
    session_id: str
    roles: list[str] = []
    exp: datetime


class JWTManager:
    """Secure JWT token management with Redis session store"""
    
    def __init__(
        self,
        secret_key: str,
        redis_url: str = "redis://localhost:6379",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
    
    async def create_session(
        self,
        user_id: str,
        roles: list[str],
        metadata: Optional[dict] = None
    ) -> dict:
        """Create new session with access + refresh tokens"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        
        # Access token (short-lived)
        access_token = jwt.encode(
            {
                "sub": user_id,
                "session_id": session_id,
                "roles": roles,
                "type": "access",
                "exp": now + self.access_token_expire
            },
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Refresh token (long-lived)
        refresh_token = jwt.encode(
            {
                "sub": user_id,
                "session_id": session_id,
                "type": "refresh",
                "exp": now + self.refresh_token_expire
            },
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Store session in Redis
        session_data = {
            "user_id": user_id,
            "roles": roles,
            "created_at": now.isoformat(),
            "metadata": metadata or {}
        }
        
        await self.redis.setex(
            f"session:{session_id}",
            int(self.refresh_token_expire.total_seconds()),
            json.dumps(session_data)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(self.access_token_expire.total_seconds())
        }
    
    async def validate_token(self, token: str) -> Optional[TokenData]:
        """Validate JWT token and check session existence"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            session_id = payload.get("session_id")
            
            # Verify session exists in Redis
            session_data = await self.redis.get(f"session:{session_id}")
            if not session_data:
                return None
            
            session = json.loads(session_data)
            
            return TokenData(
                user_id=payload["sub"],
                session_id=session_id,
                roles=session["roles"],
                exp=datetime.fromisoformat(payload["exp"])
            )
        except (JWTError, KeyError, ValueError):
            return None
    
    async def refresh_session(self, refresh_token: str) -> Optional[dict]:
        """Refresh access token using refresh token"""
        token_data = await self.validate_token(refresh_token)
        if not token_data:
            return None
        
        # Create new access token
        return await self.create_session(
            user_id=token_data.user_id,
            roles=token_data.roles
        )
    
    async def revoke_session(self, session_id: str):
        """Revoke session (logout)"""
        await self.redis.delete(f"session:{session_id}")
