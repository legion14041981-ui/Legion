"""Security Middleware - Headers, Rate Limiting"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException, status
import redis.asyncio as aioredis
from datetime import datetime, timedelta
import hashlib


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        
        # HTTPS enforcement
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # MIME sniffing prevention
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiting middleware"""
    
    def __init__(self, app, redis_url: str = "redis://localhost:6379", requests_per_minute: int = 60):
        super().__init__(app)
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use combination of IP + User-Agent for fingerprinting
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Hash for privacy
        fingerprint = f"{client_ip}:{user_agent}"
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
    
    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)
        key = f"ratelimit:{client_id}"
        
        try:
            # Get current request count
            current = await self.redis.get(key)
            
            if current is None:
                # First request in window
                await self.redis.setex(key, self.window_seconds, 1)
            else:
                current_count = int(current)
                
                if current_count >= self.requests_per_minute:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "retry_after": self.window_seconds
                        },
                        headers={"Retry-After": str(self.window_seconds)}
                    )
                
                # Increment counter
                await self.redis.incr(key)
            
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = self.requests_per_minute - int(await self.redis.get(key) or 0)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            response.headers["X-RateLimit-Reset"] = str(self.window_seconds)
            
            return response
        
        except Exception as e:
            # If Redis fails, allow request (fail open)
            return await call_next(request)
