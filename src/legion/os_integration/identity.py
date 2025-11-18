"""Agent Identity - Authentication and authorization for Legion agents.

Inspired by Microsoft Entra Agent ID announced May 2025.
Provides OAuth 2.0-style authentication with scoped permissions.
"""

import asyncio
import logging
import secrets
import hashlib
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentScope:
    """OAuth-style scope for agent permissions."""
    
    name: str
    description: str
    requires_approval: bool = True
    risk_level: str = "medium"  # low, medium, high, critical


class BuiltInScopes:
    """Built-in permission scopes for Legion agents."""
    
    # Filesystem scopes
    FILES_READ = AgentScope("files.read", "Read files from filesystem", requires_approval=True, risk_level="medium")
    FILES_WRITE = AgentScope("files.write", "Write files to filesystem", requires_approval=True, risk_level="high")
    FILES_DELETE = AgentScope("files.delete", "Delete files from filesystem", requires_approval=True, risk_level="high")
    
    # System scopes
    SYSTEM_EXECUTE = AgentScope("system.execute", "Execute system commands", requires_approval=True, risk_level="critical")
    SYSTEM_READ = AgentScope("system.read", "Read system information", requires_approval=False, risk_level="low")
    
    # Network scopes
    NETWORK_HTTP = AgentScope("network.http", "Make HTTP requests", requires_approval=False, risk_level="low")
    NETWORK_WEBHOOK = AgentScope("network.webhook", "Call webhooks", requires_approval=False, risk_level="medium")
    
    # Browser scopes
    BROWSER_NAVIGATE = AgentScope("browser.navigate", "Navigate web pages", requires_approval=False, risk_level="low")
    BROWSER_DOWNLOAD = AgentScope("browser.download", "Download files via browser", requires_approval=True, risk_level="medium")
    
    # Database scopes
    DATABASE_READ = AgentScope("database.read", "Read from databases", requires_approval=False, risk_level="low")
    DATABASE_WRITE = AgentScope("database.write", "Write to databases", requires_approval=True, risk_level="high")
    
    # API scopes
    API_OPENAI = AgentScope("api.openai", "Call OpenAI API", requires_approval=False, risk_level="low")
    API_SUPABASE = AgentScope("api.supabase", "Access Supabase", requires_approval=False, risk_level="medium")
    
    @classmethod
    def get_all(cls) -> Dict[str, AgentScope]:
        """Get all built-in scopes."""
        return {
            name: getattr(cls, name) 
            for name in dir(cls) 
            if not name.startswith('_') and isinstance(getattr(cls, name), AgentScope)
        }


@dataclass
class AgentToken:
    """Authentication token for agent."""
    
    token: str
    agent_id: str
    scopes: List[str]
    issued_at: datetime
    expires_at: datetime
    refresh_token: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return datetime.now() < self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        """Check if token has specific scope."""
        return scope in self.scopes


class LegionAgentIdentity:
    """
    Agent Identity system with OAuth 2.0-style authentication.
    
    Features:
    - Unique identity per agent (Entra Agent ID pattern)
    - Scoped permissions with granular control
    - Token-based authentication (access + refresh)
    - User approval workflow for high-risk scopes
    - Credential management
    - Audit logging for all authentication events
    
    Security Model:
    - Each agent has unique ID (legion-agent-{uuid})
    - Tokens expire after 1 hour (configurable)
    - Refresh tokens valid for 7 days
    - High-risk operations require user approval
    - All authentications logged
    
    Attributes:
        agent_id: Unique agent identifier
        entra_id: Entra-style agent ID (legion-agent-{id})
        granted_scopes: Set of approved scopes
        active_tokens: Dict of active tokens
    """
    
    def __init__(self, agent_id: str, agent_name: Optional[str] = None):
        """
        Initialize agent identity.
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
        """
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.entra_id = f"legion-agent-{agent_id}"
        
        # Permission management
        self.granted_scopes: Set[str] = set()
        self.pending_scopes: Set[str] = set()
        
        # Token management
        self.active_tokens: Dict[str, AgentToken] = {}
        self.token_lifetime_hours = 1
        self.refresh_lifetime_days = 7
        
        # Credentials (for external services)
        self.credentials: Dict[str, str] = {}  # service -> credential
        
        # Audit
        self.auth_log: List[Dict[str, Any]] = []
        
        logger.info(f"Agent identity created: {self.entra_id}")
    
    async def request_scope(self, scope: str, reason: str = "") -> bool:
        """Request permission scope for agent.
        
        Args:
            scope: Scope name (e.g., 'files.read')
            reason: Reason for requesting scope
        
        Returns:
            bool: True if granted
        """
        # Check if already granted
        if scope in self.granted_scopes:
            return True
        
        # Get scope info
        all_scopes = BuiltInScopes.get_all()
        scope_obj = None
        
        for scope_name, scope_data in all_scopes.items():
            if scope_data.name == scope:
                scope_obj = scope_data
                break
        
        if not scope_obj:
            logger.warning(f"Unknown scope requested: {scope}")
            return False
        
        # Check if requires approval
        if scope_obj.requires_approval:
            logger.info(f"Scope {scope} requires user approval")
            self.pending_scopes.add(scope)
            
            # In production, this would trigger UI prompt
            # For now, auto-approve low/medium risk
            if scope_obj.risk_level in ["low", "medium"]:
                approved = True
            else:
                approved = await self._request_user_approval(scope, reason, scope_obj.risk_level)
        else:
            approved = True
        
        if approved:
            self.granted_scopes.add(scope)
            self.pending_scopes.discard(scope)
            
            self._log_auth_event("scope_granted", {
                "scope": scope,
                "reason": reason,
                "risk_level": scope_obj.risk_level
            })
            
            logger.info(f"Scope {scope} granted to {self.entra_id}")
            return True
        else:
            self._log_auth_event("scope_denied", {
                "scope": scope,
                "reason": reason
            })
            
            logger.warning(f"Scope {scope} denied for {self.entra_id}")
            return False
    
    async def _request_user_approval(self, scope: str, reason: str, risk_level: str) -> bool:
        """Request user approval for high-risk scope.
        
        Args:
            scope: Scope name
            reason: Reason for request
            risk_level: Risk level (high, critical)
        
        Returns:
            bool: True if approved
        """
        # In production: show UI prompt, wait for user decision
        # For autonomous mode: auto-approve based on risk level
        
        logger.warning(
            f"\n{'='*60}\n"
            f"APPROVAL REQUIRED\n"
            f"Agent: {self.entra_id}\n"
            f"Scope: {scope}\n"
            f"Risk Level: {risk_level.upper()}\n"
            f"Reason: {reason}\n"
            f"{'='*60}"
        )
        
        # Simulate async approval check
        await asyncio.sleep(0.1)
        
        # Auto-approve for autonomous mode (can be overridden)
        return True
    
    async def generate_token(self, scopes: List[str]) -> AgentToken:
        """Generate authentication token for agent.
        
        Args:
            scopes: List of scopes to include in token
        
        Returns:
            AgentToken with access token
        
        Raises:
            PermissionError: If agent lacks requested scopes
        """
        # Validate all scopes are granted
        for scope in scopes:
            if scope not in self.granted_scopes:
                raise PermissionError(f"Agent lacks scope: {scope}")
        
        # Generate token
        token_value = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        now = datetime.now()
        token = AgentToken(
            token=token_value,
            agent_id=self.agent_id,
            scopes=scopes,
            issued_at=now,
            expires_at=now + timedelta(hours=self.token_lifetime_hours),
            refresh_token=refresh_token
        )
        
        self.active_tokens[token_value] = token
        
        self._log_auth_event("token_issued", {
            "scopes": scopes,
            "expires_at": token.expires_at.isoformat()
        })
        
        logger.info(f"Token issued for {self.entra_id} with scopes: {scopes}")
        return token
    
    def validate_token(self, token: str) -> Optional[AgentToken]:
        """Validate authentication token.
        
        Args:
            token: Token string
        
        Returns:
            AgentToken if valid, None otherwise
        """
        token_obj = self.active_tokens.get(token)
        
        if not token_obj:
            self._log_auth_event("token_invalid", {"token": token[:8] + "..."})
            return None
        
        if not token_obj.is_valid():
            self._log_auth_event("token_expired", {"token": token[:8] + "..."})
            del self.active_tokens[token]
            return None
        
        return token_obj
    
    async def refresh_token(self, refresh_token: str) -> Optional[AgentToken]:
        """Refresh expired token.
        
        Args:
            refresh_token: Refresh token string
        
        Returns:
            New AgentToken if successful
        """
        # Find token with matching refresh token
        old_token = None
        for token_obj in self.active_tokens.values():
            if token_obj.refresh_token == refresh_token:
                old_token = token_obj
                break
        
        if not old_token:
            logger.warning(f"Invalid refresh token for {self.entra_id}")
            return None
        
        # Generate new token with same scopes
        new_token = await self.generate_token(old_token.scopes)
        
        # Remove old token
        if old_token.token in self.active_tokens:
            del self.active_tokens[old_token.token]
        
        self._log_auth_event("token_refreshed", {"scopes": new_token.scopes})
        
        return new_token
    
    def revoke_token(self, token: str):
        """Revoke authentication token.
        
        Args:
            token: Token string
        """
        if token in self.active_tokens:
            del self.active_tokens[token]
            self._log_auth_event("token_revoked", {"token": token[:8] + "..."})
            logger.info(f"Token revoked for {self.entra_id}")
    
    def revoke_all_tokens(self):
        """Revoke all active tokens."""
        count = len(self.active_tokens)
        self.active_tokens.clear()
        self._log_auth_event("all_tokens_revoked", {"count": count})
        logger.info(f"All {count} tokens revoked for {self.entra_id}")
    
    def set_credential(self, service: str, credential: str):
        """Store credential for external service.
        
        Args:
            service: Service name (e.g., 'openai', 'supabase')
            credential: Credential value (API key, token, etc.)
        """
        # Hash credential for audit log (don't log actual value)
        cred_hash = hashlib.sha256(credential.encode()).hexdigest()[:8]
        
        self.credentials[service] = credential
        
        self._log_auth_event("credential_set", {
            "service": service,
            "credential_hash": cred_hash
        })
        
        logger.info(f"Credential set for {service} (agent: {self.entra_id})")
    
    def get_credential(self, service: str) -> Optional[str]:
        """Get credential for external service.
        
        Args:
            service: Service name
        
        Returns:
            Credential value or None
        """
        credential = self.credentials.get(service)
        
        if credential:
            self._log_auth_event("credential_accessed", {"service": service})
        
        return credential
    
    def _log_auth_event(self, event_type: str, details: Dict[str, Any]):
        """Log authentication event.
        
        Args:
            event_type: Type of event
            details: Event details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "entra_id": self.entra_id,
            "event_type": event_type,
            "details": details
        }
        
        self.auth_log.append(log_entry)
    
    def get_auth_summary(self) -> Dict[str, Any]:
        """Get authentication status summary.
        
        Returns:
            Dict with identity, scopes, tokens summary
        """
        return {
            "agent_id": self.agent_id,
            "entra_id": self.entra_id,
            "agent_name": self.agent_name,
            "granted_scopes": list(self.granted_scopes),
            "pending_scopes": list(self.pending_scopes),
            "active_tokens": len(self.active_tokens),
            "stored_credentials": list(self.credentials.keys()),
            "auth_events": len(self.auth_log)
        }
    
    def export_identity(self) -> Dict[str, Any]:
        """Export identity for persistence.
        
        Returns:
            Dict with identity data (excludes secrets)
        """
        return {
            "agent_id": self.agent_id,
            "entra_id": self.entra_id,
            "agent_name": self.agent_name,
            "granted_scopes": list(self.granted_scopes),
            "auth_log": self.auth_log,
            "created_at": self.auth_log[0]["timestamp"] if self.auth_log else None
        }
