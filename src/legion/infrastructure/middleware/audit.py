"""Audit Middleware for Request/Response Logging"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..audit import AuditLogger


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all API requests for audit trail"""
    
    def __init__(self, app):
        super().__init__(app)
        self.audit = AuditLogger()
    
    async def dispatch(self, request: Request, call_next):
        # Extract user info if available
        user_id = getattr(request.state, 'user_id', 'anonymous')
        
        # Log request
        self.audit.logger.info(
            "api.request",
            method=request.method,
            path=request.url.path,
            user_id=user_id,
            ip=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        self.audit.logger.info(
            "api.response",
            status_code=response.status_code,
            user_id=user_id
        )
        
        return response
