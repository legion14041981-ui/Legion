"""OS Interface - unified API for OS-level capabilities and system interaction.

Объединяет:
- OS Integration компоненты (Workspace, Identity, Audit, Self-Improvement)
- Безопасный доступ к файловой системе
- Выполнение системных команд
- Управление процессами
"""

import os
import subprocess
import logging
import shlex
from pathlib import Path
from typing import Optional, Dict, Any, List

from .workspace import AgentWorkspace
from .identity import AgentIdentity, Role, Permission
from .audit import AuditTrail, AuditEventType, SeverityLevel
from .self_improvement import SelfImprovementEngine

logger = logging.getLogger(__name__)


class OSInterface:
    """Унифицированный интерфейс для OS-возможностей и системного взаимодействия.
    
    Предоставляет единую точку доступа ко всем компонентам:
    - Workspace: изолированное файловое окружение
    - Identity: аутентификация и авторизация
    - Audit: tamper-evident логирование
    - Self-improvement: обучение и улучшение
    - System: безопасное выполнение системных операций
    
    Attributes:
        agent_id: ID агента
        workspace: AgentWorkspace экземпляр
        identity: AgentIdentity экземпляр
        audit: AuditTrail экземпляр
        improvement: SelfImprovementEngine экземпляр
    """
    
    def __init__(
        self,
        agent_id: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """Инициализировать OS Interface.
        
        Args:
            agent_id: Уникальный идентификатор агента
            config: Конфигурация
        """
        self.agent_id = agent_id
        self.config = config or {}
        
        # Инициализировать компоненты
        self.workspace = self._init_workspace()
        self.identity = self._init_identity()
        self.audit = self._init_audit()
        self.improvement = self._init_improvement()
        
        # Залогировать создание агента
        self.audit.log_event(
            AuditEventType.AGENT_CREATED,
            SeverityLevel.INFO,
            {'agent_id': agent_id, 'config': self.config}
        )
        
        logger.info(f"="*60)
        logger.info(f"📦 OS Interface initialized for agent '{agent_id}'")
        logger.info(f"  📁 Workspace: {self.workspace.workspace_path}")
        logger.info(f"  🔑 Identity: {len(self.identity.get_all_permissions())} permissions")
        logger.info(f"  📋 Audit: {len(self.audit.events)} events")
        logger.info(f"  🧠 Memory: {self.improvement.knowledge['metadata']['total_experiences']} experiences")
        logger.info(f"="*60)
    
    def _init_workspace(self) -> AgentWorkspace:
        """Инициализировать workspace."""
        return AgentWorkspace(
            agent_id=self.agent_id,
            quota_mb=self.config.get('workspace_quota_mb', 100),
            auto_cleanup=self.config.get('workspace_auto_cleanup', False)
        )
    
    def _init_identity(self) -> AgentIdentity:
        """Инициализировать identity."""
        roles = set()
        role_str = self.config.get('role', 'worker')
        if role_str in Role.__members__.values():
            roles.add(Role(role_str))
        else:
            roles.add(Role.WORKER)
        
        return AgentIdentity(
            agent_id=self.agent_id,
            roles=roles,
            metadata=self.config.get('identity_metadata', {})
        )
    
    def _init_audit(self) -> AuditTrail:
        """Инициализировать audit trail."""
        return AuditTrail(agent_id=self.agent_id)
    
    def _init_improvement(self) -> SelfImprovementEngine:
        """Инициализировать self-improvement engine."""
        return SelfImprovementEngine(agent_id=self.agent_id)
    
    def check_permission(self, permission: Permission) -> bool:
        """Проверить разрешение и залогировать.
        
        Args:
            permission: Разрешение для проверки
        
        Returns:
            bool: True если разрешение есть
        """
        has_perm = self.identity.has_permission(permission)
        
        if not has_perm:
            self.audit.log_event(
                AuditEventType.SECURITY_VIOLATION,
                SeverityLevel.WARNING,
                {'permission': permission.value, 'denied': True}
            )
        
        return has_perm
    
    # === System Operations ===
    
    def execute_command(
        self,
        command: str,
        shell: bool = False,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Безопасное выполнение системной команды.
        
        Args:
            command: Команда для выполнения
            shell: Использовать shell
            timeout: Таймаут в секундах
        
        Returns:
            Dict с результатом выполнения
        """
        if not self.check_permission(Permission.EXECUTE):
            raise PermissionError("Agent does not have EXECUTE permission")
        
        self.audit.log_event(
            AuditEventType.MCP_INVOKE,
            SeverityLevel.INFO,
            {'command': command, 'shell': shell}
        )
        
        try:
            if not shell:
                command = shlex.split(command)
            
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'status': 'success',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def read_file(self, path: Path) -> str:
        """Безопасное чтение файла.
        
        Args:
            path: Путь к файлу
        
        Returns:
            str: Содержимое файла
        """
        if not self.check_permission(Permission.FILE_SYSTEM):
            raise PermissionError("Agent does not have FILE_SYSTEM permission")
        
        self.audit.log_event(
            AuditEventType.FILE_READ,
            SeverityLevel.INFO,
            {'path': str(path)}
        )
        
        return path.read_text(encoding='utf-8')
    
    def write_file(self, path: Path, content: str):
        """Безопасная запись файла.
        
        Args:
            path: Путь к файлу
            content: Содержимое
        """
        if not self.check_permission(Permission.FILE_SYSTEM):
            raise PermissionError("Agent does not have FILE_SYSTEM permission")
        
        self.audit.log_event(
            AuditEventType.FILE_WRITE,
            SeverityLevel.INFO,
            {'path': str(path), 'size': len(content)}
        )
        
        path.write_text(content, encoding='utf-8')
    
    # === Core Methods ===
    
    def cleanup(self):
        """Очистить все ресурсы."""
        self.audit.log_event(
            AuditEventType.AGENT_STOPPED,
            SeverityLevel.INFO,
            {'reason': 'cleanup'}
        )
        
        if self.workspace.auto_cleanup:
            self.workspace.cleanup()
        
        logger.info(f"🧹 OS Interface cleaned up for '{self.agent_id}'")
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус всех компонентов.
        
        Returns:
            Dict: Полный статус
        """
        return {
            'agent_id': self.agent_id,
            'workspace': self.workspace.get_usage_stats(),
            'identity': self.identity.to_dict(),
            'audit': {
                'event_count': len(self.audit.events),
                'integrity_verified': self.audit.verify_integrity()
            },
            'improvement': self.improvement.get_stats()
        }
    
    def __enter__(self):
        """Context manager вход."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager выход."""
        self.cleanup()
