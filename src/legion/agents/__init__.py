"""
Специализированные агенты для Legion framework.

Этот модуль содержит готовые реализации агентов для различных задач:
- EmailAgent - отправка email через SMTP
- GoogleSheetsAgent - интеграция с Google Sheets
from .base_agent import LegionAgent
- DataAgent - обработка и анализ данных"""

from .email_agent import EmailAgent
from .sheets_agent import GoogleSheetsAgent
from .data_agent import DataAgent

__all__ = [
     "LegionAgent",
    "EmailAgent",
    "GoogleSheetsAgent",
    "DataAgent",
]

__version__ = "0.2.0"
