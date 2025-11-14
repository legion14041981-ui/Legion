"""
Специализированные агенты для Legion framework.

Этот модуль содержит готовые реализации агентов для различных задач:
- EmailAgent - отправка email через SMTP
- GoogleSheetsAgent - интеграция с Google Sheets
- DataAgent - обработка данных (планируется)
"""

from .email_agent import EmailAgent
from .sheets_agent import GoogleSheetsAgent

__all__ = [
    "EmailAgent",
    "GoogleSheetsAgent",
]

__version__ = "0.2.0"
