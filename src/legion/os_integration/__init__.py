"""OS Integration Layer для Legion v2.2.

Обеспечивает:
- Безопасную изоляцию агентов (Workspace)
- Управление идентификацией (Identity)
- Интерфейс взаимодействия с ОС (Interface)
- Аудит и логирование операций (Audit)
- Самообучение и оптимизацию (SelfImprovement)
"""

from .workspace import Workspace
from .identity import IdentityManager
from .interface import OSInterface
from .audit import AuditLogger
from .self_improvement import SelfImprovementEngine

__all__ = [
    'Workspace',
    'IdentityManager',
    'OSInterface',
    'AuditLogger',
    'SelfImprovementEngine'
]

__version__ = '2.2.0'
