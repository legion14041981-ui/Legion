"""OS Integration Layer for Legion AI System v2.2.

Предоставляет OS-уровневые возможности для агентов:
- Workspace: изолированные файловые окружения
- Identity: Entra-style аутентификация
- Audit Trail: tamper-evident логирование
- Self-Improvement: долгосрочная память и обучение
- Interface: унифицированный интерфейс для OS API
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
