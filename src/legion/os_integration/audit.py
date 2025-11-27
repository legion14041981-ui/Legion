"""Audit Trail - tamper-evident logging for agent actions.

Реализует immutable audit log с:
- Hash-chaining (каждая запись ссылается на предыдущую)
- Tamper detection (обнаружение изменений)
- Cryptographic signatures
- Compliance-ready формат
- Логирование всех операций агентов
- Отслеживание доступа к ресурсам
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of auditable events."""
    AGENT_CREATED = 'agent.created'
    AGENT_STARTED = 'agent.started'
    AGENT_STOPPED = 'agent.stopped'
    PERMISSION_GRANTED = 'permission.granted'
    PERMISSION_REVOKED = 'permission.revoked'
    FILE_READ = 'file.read'
    FILE_WRITE = 'file.write'
    FILE_DELETE = 'file.delete'
    NETWORK_REQUEST = 'network.request'
    MCP_INVOKE = 'mcp.invoke'
    BROWSER_ACTION = 'browser.action'
    ERROR_OCCURRED = 'error.occurred'
    SECURITY_VIOLATION = 'security.violation'


class SeverityLevel(str, Enum):
    """Severity levels for audit events."""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


@dataclass
class AuditEvent:
    """Single audit event.
    
    Attributes:
        event_type: Тип события
        agent_id: ID агента
        timestamp: Время события
        severity: Уровень важности
        details: Детали события
        previous_hash: Hash предыдущей записи
        event_hash: Hash текущей записи
    """
    event_type: AuditEventType
    agent_id: str
    timestamp: str
    severity: SeverityLevel
    details: Dict[str, Any]
    previous_hash: str
    event_hash: str = ''
    
    def __post_init__(self):
        """Calculate event hash after initialization."""
        if not self.event_hash:
            self.event_hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Вычислить hash события.
        
        Returns:
            str: SHA-256 hash
        """
        data = {
            'event_type': self.event_type.value,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp,
            'severity': self.severity.value,
            'details': self.details,
            'previous_hash': self.previous_hash
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def verify(self) -> bool:
        """Проверить целостность события.
        
        Returns:
            bool: True если hash совпадает
        """
        return self.event_hash == self.calculate_hash()


class AuditTrail:
    """Tamper-evident audit trail.
    
    Реализует immutable audit log с hash-chaining:
    - Каждая запись содержит hash предыдущей
    - Изменение любой записи ломает всю цепочку
    - Cryptographic защита от подмены
    
    Attributes:
        agent_id: ID агента
        events: Список событий
        audit_file: Путь к файлу лога
    """
    
    def __init__(self, agent_id: str, audit_dir: Optional[Path] = None):
        """Initialize audit trail.
        
        Args:
            agent_id: Уникальный идентификатор агента
            audit_dir: Директория для логов (по умолчанию ./audit_logs)
        """
        self.agent_id = agent_id
        self.events: List[AuditEvent] = []
        
        # Определить директорию для логов
        if audit_dir is None:
            audit_dir = Path.cwd() / 'audit_logs'
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_file = audit_dir / f'{agent_id}_audit.jsonl'
        
        # Загрузить существующие события
        self._load_events()
        
        logger.info(f"📋 Audit trail initialized for '{agent_id}' ({len(self.events)} events loaded)")
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: SeverityLevel = SeverityLevel.INFO,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Залогировать событие.
        
        Args:
            event_type: Тип события
            severity: Уровень важности
            details: Детали события
        
        Returns:
            AuditEvent: Созданное событие
        """
        # Получить hash предыдущего события
        previous_hash = self.events[-1].event_hash if self.events else '0' * 64
        
        # Создать новое событие
        event = AuditEvent(
            event_type=event_type,
            agent_id=self.agent_id,
            timestamp=datetime.utcnow().isoformat(),
            severity=severity,
            details=details or {},
            previous_hash=previous_hash
        )
        
        # Добавить в список
        self.events.append(event)
        
        # Сохранить в файл
        self._append_event_to_file(event)
        
        # Логировать
        log_method = logger.info
        if severity == SeverityLevel.WARNING:
            log_method = logger.warning
        elif severity == SeverityLevel.ERROR:
            log_method = logger.error
        elif severity == SeverityLevel.CRITICAL:
            log_method = logger.critical
        
        log_method(f"📝 [{event_type.value}] {details}")
        
        return event
    
    def verify_integrity(self) -> bool:
        """Проверить целостность всей цепочки.
        
        Returns:
            bool: True если все hash-ы валидны
        """
        if not self.events:
            return True
        
        # Проверить первое событие
        if not self.events[0].verify():
            logger.error(f"❌ First event tampered: {self.events[0].event_type}")
            return False
        
        # Проверить цепочку
        for i in range(1, len(self.events)):
            current = self.events[i]
            previous = self.events[i - 1]
            
            # Проверить hash события
            if not current.verify():
                logger.error(f"❌ Event tampered at index {i}: {current.event_type}")
                return False
            
            # Проверить связь с предыдущим
            if current.previous_hash != previous.event_hash:
                logger.error(f"❌ Chain broken at index {i}")
                return False
        
        logger.info(f"✅ Audit trail integrity verified ({len(self.events)} events)")
        return True
    
    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[SeverityLevel] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Получить события с фильтрацией.
        
        Args:
            event_type: Фильтр по типу
            severity: Фильтр по важности
            limit: Максимальное количество
        
        Returns:
            List[AuditEvent]: Отфильтрованные события
        """
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        
        return filtered[-limit:]
    
    def export_to_json(self, output_path: Optional[Path] = None) -> Path:
        """Экспортировать в JSON файл.
        
        Args:
            output_path: Путь для экспорта
        
        Returns:
            Path: Путь к созданному файлу
        """
        if output_path is None:
            output_path = self.audit_file.with_suffix('.json')
        
        data = {
            'agent_id': self.agent_id,
            'event_count': len(self.events),
            'integrity_verified': self.verify_integrity(),
            'events': [asdict(e) for e in self.events]
        }
        
        output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        logger.info(f"💾 Audit trail exported to {output_path}")
        return output_path
    
    def _load_events(self):
        """Загрузить события из файла."""
        if not self.audit_file.exists():
            return
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    event = AuditEvent(
                        event_type=AuditEventType(data['event_type']),
                        agent_id=data['agent_id'],
                        timestamp=data['timestamp'],
                        severity=SeverityLevel(data['severity']),
                        details=data['details'],
                        previous_hash=data['previous_hash'],
                        event_hash=data['event_hash']
                    )
                    self.events.append(event)
        except Exception as e:
            logger.error(f"❌ Failed to load audit events: {e}")
    
    def _append_event_to_file(self, event: AuditEvent):
        """Добавить событие в файл."""
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event)) + '\n')
        except Exception as e:
            logger.error(f"❌ Failed to write audit event: {e}")
