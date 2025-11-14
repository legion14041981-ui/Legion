"""
Legion Framework - многоагентная система координации.

Этот пакет содержит основное ядро фреймворка Legion, включает:

- Координатор (LegionCore) - управление агентами и их жизненным циклом
- Базовый класс агента (LegionAgent) - интерфейс для создания агентов
- Специализированные агенты (EmailAgent, GoogleSheetsAgent, DataAgent)"""

from .core import LegionCore
from .agents import LegionAgent
from .agents import EmailAgent, GoogleSheetsAgent, DataAgentfrom .database import LegionDat
from .database import LegionDatabase
from .queue import TaskQueue
from .logging_config import LegionLogger, setup_logging

__version__ = "0.2.0"
__all__ = [
    "LegionCore",
    "LegionAgent",
    "EmailAgent",
    "GoogleSheetsAgent",
    "DataAgent",
    "LegionDatabase",
    "TaskQueue",
    "LegionLogger",
    "setup_logging"
]
