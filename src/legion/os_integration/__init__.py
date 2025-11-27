"""OS Integration Layer для Legion v2.2 - Autonomous System Improvements.

Обеспечивает OS-уровневые возможности для агентов:
- Workspace: изолированные файловые окружения с квотами
- Identity: Entra-style аутентификация и RBAC
- Audit Trail: tamper-evident логирование действий
- Self-Improvement: долгосрочная память и обучение
- Interface: унифицированный API для всех компонентов
"""

from .workspace import AgentWorkspace
from .identity import AgentIdentity
from .audit import AuditTrail
from .self_improvement import SelfImprovementEngine
from .interface import OSInterface

__all__ = [
    'AgentWorkspace',
    'AgentIdentity',
    'AuditTrail',
    'SelfImprovementEngine',
    'OSInterface',
]

__version__ = '2.2.0'

