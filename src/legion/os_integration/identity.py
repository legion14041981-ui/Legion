"""Identity Manager - управление идентификацией агентов.

Обеспечивает:
- Уникальные идентификаторы агентов
- Аутентификацию и авторизацию
- Управление ролями и правами доступа
"""

import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Role(Enum):
    """Роли агентов."""
    ADMIN = "admin"
    PLANNER = "planner"
    EXECUTOR = "executor"
    MONITOR = "monitor"
    BROWSER = "browser"
    READ_ONLY = "read_only"


class Permission(Enum):
    """Права доступа."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class Identity:
    """Идентификация агента."""
    
    def __init__(self, agent_id: str, role: Role, permissions: Set[Permission]):
        self.agent_id = agent_id
        self.role = role
        self.permissions = permissions
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.token = self._generate_token()
    
    def _generate_token(self) -> str:
        """Генерировать уникальный токен."""
        data = f"{self.agent_id}:{self.role.value}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def has_permission(self, permission: Permission) -> bool:
        """Проверить наличие права доступа."""
        return permission in self.permissions or Permission.ADMIN in self.permissions
    
    def update_activity(self):
        """Обновить время последней активности."""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь."""
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'permissions': [p.value for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'token': self.token
        }


class IdentityManager:
    """Управление идентификацией агентов."""
    
    def __init__(self):
        self.identities: Dict[str, Identity] = {}
        self.role_permissions: Dict[Role, Set[Permission]] = {
            Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE, Permission.ADMIN},
            Role.PLANNER: {Permission.READ, Permission.WRITE},
            Role.EXECUTOR: {Permission.READ, Permission.EXECUTE},
            Role.MONITOR: {Permission.READ},
            Role.BROWSER: {Permission.READ, Permission.EXECUTE},
            Role.READ_ONLY: {Permission.READ}
        }
        logger.info("IdentityManager initialized")
    
    def create_identity(self, agent_id: Optional[str] = None, role: Role = Role.EXECUTOR) -> Identity:
        """
        Создать новую идентификацию агента.
        
        Args:
            agent_id: Идентификатор агента (если None, генерируется UUID)
            role: Роль агента
        
        Returns:
            Identity: Созданная идентификация
        """
        if not agent_id:
            agent_id = str(uuid.uuid4())
        
        if agent_id in self.identities:
            raise ValueError(f"Agent ID already exists: {agent_id}")
        
        permissions = self.role_permissions[role]
        identity = Identity(agent_id, role, permissions)
        self.identities[agent_id] = identity
        
        logger.info(f"Created identity for agent '{agent_id}' with role '{role.value}'")
        return identity
    
    def get_identity(self, agent_id: str) -> Optional[Identity]:
        """
        Получить идентификацию агента.
        
        Args:
            agent_id: Идентификатор агента
        
        Returns:
            Optional[Identity]: Идентификация или None
        """
        return self.identities.get(agent_id)
    
    def verify_token(self, agent_id: str, token: str) -> bool:
        """
        Проверить токен агента.
        
        Args:
            agent_id: Идентификатор агента
            token: Токен для проверки
        
        Returns:
            bool: True если токен валиден
        """
        identity = self.identities.get(agent_id)
        if not identity:
            return False
        
        return identity.token == token
    
    def check_permission(self, agent_id: str, permission: Permission) -> bool:
        """
        Проверить право доступа агента.
        
        Args:
            agent_id: Идентификатор агента
            permission: Право для проверки
        
        Returns:
            bool: True если право есть
        """
        identity = self.identities.get(agent_id)
        if not identity:
            return False
        
        identity.update_activity()
        return identity.has_permission(permission)
    
    def revoke_identity(self, agent_id: str):
        """
        Отозвать идентификацию агента.
        
        Args:
            agent_id: Идентификатор агента
        """
        if agent_id in self.identities:
            del self.identities[agent_id]
            logger.info(f"Revoked identity for agent '{agent_id}'")
    
    def get_all_identities(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить все идентификации.
        
        Returns:
            Dict: Словарь всех идентификаций
        """
        return {agent_id: identity.to_dict() for agent_id, identity in self.identities.items()}
