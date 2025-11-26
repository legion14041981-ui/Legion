"""
Специализированные агенты для Legion framework.

Этот модуль содержит готовые реализации агентов для различных задач:
- EmailAgent - отправка email через SMTP
- GoogleSheetsAgent - интеграция с Google Sheets
- DataAgent - обработка и анализ данных
- CIHealerAgent - автономное исправление CI/CD ошибок
"""

from .email_agent import EmailAgent
from .sheets_agent import GoogleSheetsAgent
from .data_agent import DataAgent
from .ci_healer_agent import CIHealerAgent, HealingResult
from ..base_agent import LegionAgent

__all__ = [
    "EmailAgent",
    "GoogleSheetsAgent",
    "DataAgent",
    "CIHealerAgent",
    "HealingResult",
    "LegionAgent",
]

__version__ = "2.0.0"
