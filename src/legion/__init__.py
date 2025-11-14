"""
Legion Framework - многоагентная система координации.

Этот пакет содержит основное ядро фреймворка Legion, включая:
- Координатор (LegionCore) - управление агентами и их жизненным циклом
- Базовый класс агента (LegionAgent) - интерфейс для создания агентов
"""

from .core import LegionCore
from .agents import LegionAgent
from .database import LegionDatabase

__version__ = "0.1.0"
__all__ = ["LegionCore", "LegionAgent, "LegionDatabase"]]
