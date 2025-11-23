"""
Специализированные агенты для Legion framework.

Этот модуль содержит готовые реализации агентов для различных задач:
- EmailAgent - отправка email через SMTP
- GoogleSheetsAgent - интеграция с Google Sheets
- DataAgent - обработка и анализ данных"""

from .email_agent import EmailAgent
from .sheets_agent import GoogleSheetsAgent
from .data_agent import DataAgent
from ..agents import LegionAgent

__all__ = [
    "EmailAgent",
    "GoogleSheetsAgent",
    "DataAgent"    "LegionAgent",
]
]

__version__ = "0.2.0"
