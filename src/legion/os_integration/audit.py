"""Audit Logger - аудит и логирование операций агентов.

Обеспечивает:
- Логирование всех операций агентов
- Отслеживание доступа к ресурсам
- Compliance reporting
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Уровни аудита."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent:
    """Событие аудита."""
    
    def __init__(self, agent_id: str, operation: str, level: AuditLevel, 
                 details: Optional[Dict[str, Any]] = None):
        self.timestamp = datetime.now()
        self.agent_id = agent_id
        self.operation = operation
        self.level = level
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'agent_id': self.agent_id,
            'operation': self.operation,
            'level': self.level.value,
            'details': self.details
        }
    
    def to_json(self) -> str:
        """Конвертировать в JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """Логгер аудита."""
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Инициализация логгера аудита.
        
        Args:
            log_file: Путь к файлу логов (если None, только в memory)
        """
        self.log_file = log_file
        self.events: List[AuditEvent] = []
        self.max_memory_events = 10000  # Максимум событий в памяти
        
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AuditLogger initialized (log_file: {log_file})")
    
    def log(self, agent_id: str, operation: str, level: AuditLevel = AuditLevel.INFO,
            details: Optional[Dict[str, Any]] = None):
        """
        Записать событие аудита.
        
        Args:
            agent_id: Идентификатор агента
            operation: Операция
            level: Уровень события
            details: Дополнительные детали
        """
        event = AuditEvent(agent_id, operation, level, details)
        
        # Добавить в memory
        self.events.append(event)
        
        # Ограничить размер в памяти
        if len(self.events) > self.max_memory_events:
            self.events = self.events[-self.max_memory_events:]
        
        # Записать в файл
        if self.log_file:
            self._write_to_file(event)
        
        logger.debug(f"Audit: {agent_id} - {operation} [{level.value}]")
    
    def _write_to_file(self, event: AuditEvent):
        """Записать событие в файл."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(event.to_json() + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_info(self, agent_id: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """Записать INFO событие."""
        self.log(agent_id, operation, AuditLevel.INFO, details)
    
    def log_warning(self, agent_id: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """Записать WARNING событие."""
        self.log(agent_id, operation, AuditLevel.WARNING, details)
    
    def log_error(self, agent_id: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """Записать ERROR событие."""
        self.log(agent_id, operation, AuditLevel.ERROR, details)
    
    def log_critical(self, agent_id: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """Записать CRITICAL событие."""
        self.log(agent_id, operation, AuditLevel.CRITICAL, details)
    
    def get_events(self, agent_id: Optional[str] = None, 
                   level: Optional[AuditLevel] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получить события аудита.
        
        Args:
            agent_id: Фильтр по агенту
            level: Фильтр по уровню
            limit: Максимум событий
        
        Returns:
            List[Dict]: События аудита
        """
        filtered = self.events
        
        if agent_id:
            filtered = [e for e in filtered if e.agent_id == agent_id]
        
        if level:
            filtered = [e for e in filtered if e.level == level]
        
        return [e.to_dict() for e in filtered[-limit:]]
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """
        Получить отчет о compliance.
        
        Returns:
            Dict: Отчет
        """
        total_events = len(self.events)
        level_counts = {
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        
        for event in self.events:
            level_counts[event.level.value] += 1
        
        agent_stats = {}
        for event in self.events:
            if event.agent_id not in agent_stats:
                agent_stats[event.agent_id] = 0
            agent_stats[event.agent_id] += 1
        
        return {
            'total_events': total_events,
            'level_counts': level_counts,
            'agent_stats': agent_stats,
            'critical_events': level_counts['critical'],
            'error_events': level_counts['error']
        }
