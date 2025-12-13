"""Input Sanitization for Security"""

import re
from html import escape
from typing import Any
import bleach


class InputSanitizer:
    """Centralized input sanitization to prevent injection attacks"""
    
    # SQL injection patterns
    SQL_DANGEROUS = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'UNION', 'SELECT']
    
    # Command injection characters
    CMD_DANGEROUS = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    
    # Path traversal patterns
    PATH_DANGEROUS = ['..', '~/', '/etc/', '/var/', '/root/', 'C:\\', '\\\\', '%00']
    
    @staticmethod
    def sanitize_sql(value: str) -> str:
        """Remove SQL injection vectors"""
        if not isinstance(value, str):
            return value
        
        sanitized = value
        for pattern in InputSanitizer.SQL_DANGEROUS:
            sanitized = sanitized.replace(pattern, '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_command(value: str) -> str:
        """Remove command injection vectors"""
        if not isinstance(value, str):
            return value
        
        sanitized = value
        for char in InputSanitizer.CMD_DANGEROUS:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_path(value: str) -> str:
        """Prevent path traversal attacks"""
        if not isinstance(value, str):
            return value
        
        # Check for dangerous patterns
        for pattern in InputSanitizer.PATH_DANGEROUS:
            if pattern.lower() in value.lower():
                raise ValueError(f"Dangerous path pattern detected: {pattern}")
        
        # Normalize path
        import os.path
        normalized = os.path.normpath(value)
        
        # Ensure it doesn't escape base directory
        if normalized.startswith('..'):
            raise ValueError("Path traversal not allowed")
        
        return normalized
    
    @staticmethod
    def sanitize_html(value: str, allowed_tags: list = None) -> str:
        """Remove XSS vectors from HTML"""
        if not isinstance(value, str):
            return value
        
        # Default: strip all HTML
        if allowed_tags is None:
            allowed_tags = []
        
        # Remove dangerous tags and attributes
        return bleach.clean(
            value,
            tags=allowed_tags,
            strip=True,
            attributes={}
        )
    
    @staticmethod
    def escape_output(value: str) -> str:
        """Escape HTML for safe output rendering"""
        if not isinstance(value, str):
            return value
        
        return escape(value)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format"""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid_str.lower()))
    
    @staticmethod
    def sanitize_dict(data: dict) -> dict:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Apply multiple sanitization layers
                value = InputSanitizer.sanitize_html(value)
                value = InputSanitizer.sanitize_command(value)
            elif isinstance(value, dict):
                value = InputSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                value = [InputSanitizer.sanitize_dict(v) if isinstance(v, dict) else v for v in value]
            
            sanitized[key] = value
        
        return sanitized
