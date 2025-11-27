"""Agent Identity - Entra-style authentication and authorization.

Предоставляет систему идентификации и авторизации агентов:
- JWT-токены для аутентификации
- Role-Based Access Control (RBAC)
- Permission management
- Token refresh & revocation
- Entra-inspired design (Microsoft's identity platform)
- Уникальные идентификаторы агентов
- Управление ролями и правами доступа
"""

import jwt
import logging
import secrets
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Agent permissions."""
    READ = 'read'
    WRITE = 'write'
    EXECUTE = 'execute'
    ADMIN = 'admin'
    MCP_INVOKE = 'mcp:invoke'
    BROWSER_CONTROL = 'browser:control'
    FILE_SYSTEM = 'filesystem:access'
    NETWORK = 'network:access'


class Role(str, Enum):
    """Predefined roles with permission sets."""
    GUEST = 'guest'
    WORKER = 'worker'
    SUPERVISOR = 'supervisor'
    ADMIN = 'admin'


ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.GUEST: {Permission.READ},
    Role.WORKER: {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.MCP_INVOKE},
    Role.SUPERVISOR: {
        Permission.READ, Permission.WRITE, Permission.EXECUTE,
        Permission.MCP_INVOKE, Permission.BROWSER_CONTROL, Permission.FILE_SYSTEM
    },
    Role.ADMIN: set(Permission),  # All permissions
}


@dataclass
class AgentIdentity:
    """Agent identity with authentication and authorization.
    
    Entra-style identity system:
    - Уникальный ID агента
    - Роли и разрешения (RBAC)
    - JWT-токены для аутентификации
    - Token refresh & expiry
    
    Attributes:
        agent_id: Уникальный идентификатор
        roles: Набор ролей
        custom_permissions: Дополнительные разрешения
        metadata: Метаданные агента
    """
    agent_id: str
    roles: Set[Role] = field(default_factory=lambda: {Role.WORKER})
    custom_permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Internal state
    _secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32), repr=False)
    _access_token: Optional[str] = field(default=None, repr=False)
    _refresh_token: Optional[str] = field(default=None, repr=False)
    _token_expires_at: Optional[datetime] = field(default=None, repr=False)
    _is_revoked: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        """Initialize identity."""
        self.metadata.setdefault('created_at', datetime.now().isoformat())
        self.metadata.setdefault('name', self.agent_id)
        logger.info(f"✅ Identity created for agent '{self.agent_id}' with roles {self.roles}")
    
    def get_all_permissions(self) -> Set[Permission]:
        """Получить все разрешения (из ролей + custom).
        
        Returns:
            Set[Permission]: Полный набор разрешений
        """
        permissions = set(self.custom_permissions)
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        return permissions
    
    def has_permission(self, permission: Permission) -> bool:
        """Проверить наличие разрешения.
        
        Args:
            permission: Разрешение для проверки
        
        Returns:
            bool: True если разрешение есть
        """
        if self._is_revoked:
            return False
        return permission in self.get_all_permissions()
    
    def has_role(self, role: Role) -> bool:
        """Проверить наличие роли.
        
        Args:
            role: Роль для проверки
        
        Returns:
            bool: True если роль есть
        """
        return role in self.roles
    
    def grant_role(self, role: Role):
        """Выдать роль.
        
        Args:
            role: Роль для выдачи
        """
        self.roles.add(role)
        logger.info(f"🔑 Role '{role}' granted to '{self.agent_id}'")
    
    def revoke_role(self, role: Role):
        """Отозвать роль.
        
        Args:
            role: Роль для отзыва
        """
        self.roles.discard(role)
        logger.info(f"❌ Role '{role}' revoked from '{self.agent_id}'")
    
    def grant_permission(self, permission: Permission):
        """Выдать дополнительное разрешение.
        
        Args:
            permission: Разрешение для выдачи
        """
        self.custom_permissions.add(permission)
        logger.info(f"🔑 Permission '{permission}' granted to '{self.agent_id}'")
    
    def revoke_permission(self, permission: Permission):
        """Отозвать дополнительное разрешение.
        
        Args:
            permission: Разрешение для отзыва
        """
        self.custom_permissions.discard(permission)
        logger.info(f"❌ Permission '{permission}' revoked from '{self.agent_id}'")
    
    def generate_access_token(self, expires_in_hours: int = 1) -> str:
        """Сгенерировать JWT access token.
        
        Args:
            expires_in_hours: Срок действия в часах
        
        Returns:
            str: JWT токен
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expires_in_hours)
        
        payload = {
            'agent_id': self.agent_id,
            'roles': [r.value for r in self.roles],
            'permissions': [p.value for p in self.get_all_permissions()],
            'iat': now,
            'exp': expires_at,
            'metadata': self.metadata
        }
        
        token = jwt.encode(payload, self._secret_key, algorithm='HS256')
        self._access_token = token
        self._token_expires_at = expires_at
        
        logger.info(f"🎫 Access token generated for '{self.agent_id}' (expires: {expires_at})")
        return token
    
    def generate_refresh_token(self) -> str:
        """Сгенерировать refresh token.
        
        Returns:
            str: Refresh токен
        """
        self._refresh_token = secrets.token_urlsafe(64)
        logger.info(f"🔄 Refresh token generated for '{self.agent_id}'")
        return self._refresh_token
    
    def verify_token(self, token: str) -> bool:
        """Проверить JWT токен.
        
        Args:
            token: JWT токен для проверки
        
        Returns:
            bool: True если токен валиден
        """
        if self._is_revoked:
            return False
        
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=['HS256'])
            return payload.get('agent_id') == self.agent_id
        except jwt.ExpiredSignatureError:
            logger.warning(f"⏰ Token expired for '{self.agent_id}'")
            return False
        except jwt.InvalidTokenError:
            logger.error(f"❌ Invalid token for '{self.agent_id}'")
            return False
    
    def revoke(self):
        """Отозвать все токены и разрешения."""
        self._is_revoked = True
        self._access_token = None
        self._refresh_token = None
        logger.warning(f"⚠️ Identity revoked for '{self.agent_id}'")
    
    def is_active(self) -> bool:
        """Проверить активность identity.
        
        Returns:
            bool: True если не отозван и токен валиден
        """
        if self._is_revoked:
            return False
        if self._token_expires_at and datetime.utcnow() > self._token_expires_at:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь (без секретных данных).
        
        Returns:
            Dict: Публичная информация о identity
        """
        return {
            'agent_id': self.agent_id,
            'roles': [r.value for r in self.roles],
            'permissions': [p.value for p in self.get_all_permissions()],
            'is_active': self.is_active(),
            'token_expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
            'metadata': self.metadata
        }
