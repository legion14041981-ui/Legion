"""
Event type definitions and event model for message bus.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from datetime import datetime
import uuid


class EventType(str, Enum):
    """All event types in LEGION system."""
    
    # Market data events
    MARKET_DATA_RECEIVED = "market_data_received"
    DEPTH_SNAPSHOT = "depth_snapshot"
    FUNDING_UPDATE = "funding_update"
    
    # Feature computation events
    FEATURES_COMPUTED = "features_computed"
    INDICATORS_UPDATED = "indicators_updated"
    
    # Strategy events
    SIGNAL_GENERATED = "signal_generated"
    CANDIDATE_TRADE = "candidate_trade"
    
    # Backtesting events
    BACKTEST_COMPLETE = "backtest_complete"
    BACKTEST_RESULT = "backtest_result"
    
    # Risk management events
    TRADE_APPROVED = "trade_approved"
    TRADE_REJECTED = "trade_rejected"
    RISK_ALERT = "risk_alert"
    
    # Execution events
    ORDER_EXECUTED = "order_executed"
    ORDER_FAILED = "order_failed"
    POSITION_UPDATED = "position_updated"
    
    # System health events
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_HEALTH_CHECK = "agent_health_check"
    AGENT_STATUS_UPDATE = "agent_status_update"
    
    # System events
    AGENT_READY = "agent_ready"
    AGENT_ERROR = "agent_error"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class Event:
    """
    Standard event model for message bus.
    
    Attributes:
        type: Event type from EventType enum
        data: Event payload (can be any serializable dict)
        source_agent: Name of agent that published event
        timestamp: Event creation timestamp
        correlation_id: For tracing related events
        message_id: Unique message identifier
        metadata: Additional context (headers, tags, etc.)
    """
    
    type: EventType
    data: Dict[str, Any]
    source_agent: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dict for message bus."""
        return {
            'type': self.type.value,
            'data': self.data,
            'source_agent': self.source_agent,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'message_id': self.message_id,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Deserialize event from dict."""
        return cls(
            type=EventType(data['type']),
            data=data['data'],
            source_agent=data['source_agent'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            message_id=data.get('message_id'),
            metadata=data.get('metadata', {}),
        )
