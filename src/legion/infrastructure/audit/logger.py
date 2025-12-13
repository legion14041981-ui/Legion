"""Structured Audit Logging for Security Events"""

import structlog
from datetime import datetime
from typing import Optional, Any
import json


class AuditLogger:
    """Structured audit logger for compliance and security monitoring"""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def _log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Internal method to log structured event"""
        self.logger.info(
            event_type,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            ip_address=ip_address,
            metadata=metadata or {}
        )
    
    def log_auth_attempt(
        self,
        user_id: str,
        ip_address: str,
        success: bool,
        method: str = "password",
        reason: Optional[str] = None
    ):
        """Log authentication attempt"""
        self._log_event(
            event_type="auth.login.attempt" if not success else "auth.login.success",
            user_id=user_id,
            ip_address=ip_address,
            action="login",
            result="success" if success else "failure",
            metadata={"method": method, "reason": reason}
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        granted: bool,
        ip_address: Optional[str] = None
    ):
        """Log data access attempt"""
        self._log_event(
            event_type="data.access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result="granted" if granted else "denied",
            ip_address=ip_address
        )
    
    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None
    ):
        """Log configuration change"""
        self._log_event(
            event_type="config.change",
            user_id=user_id,
            action="update",
            result="success",
            ip_address=ip_address,
            metadata={
                "config_key": config_key,
                "old_value": str(old_value),
                "new_value": str(new_value)
            }
        )
    
    def log_admin_action(
        self,
        admin_id: str,
        action: str,
        target_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Log administrative action"""
        self._log_event(
            event_type="admin.action",
            user_id=admin_id,
            action=action,
            resource_id=target_id,
            result="executed",
            ip_address=ip_address,
            metadata=metadata
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Log security-related event"""
        self._log_event(
            event_type=f"security.{event_type}",
            user_id=user_id,
            ip_address=ip_address,
            result=severity,
            metadata={"description": description, **(metadata or {})}
        )
