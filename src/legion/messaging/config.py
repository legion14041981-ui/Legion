"""
Configuration module для messaging layer.

Централизованное управление конфигурацией message bus.
"""

from dataclasses import dataclass
from typing import Optional, Literal
import os


BrokerType = Literal["redis", "memory"]


@dataclass
class MessageBusConfig:
    """
    Конфигурация message bus.
    
    Все настройки для broker, registry, consumers, publishers.
    """
    
    # Broker configuration
    broker_type: BrokerType = "memory"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Consumer configuration
    consumer_buffer_size: int = 1000
    consumer_max_retries: int = 3
    consumer_retry_delay_ms: int = 100
    
    # Publisher configuration
    publisher_default_priority: int = 5
    publisher_batch_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_events: bool = True
    
    @classmethod
    def from_env(cls) -> "MessageBusConfig":
        """
        Создать конфигурацию из переменных окружения.
        
        Returns:
            Экземпляр MessageBusConfig
        """
        broker_type_str = os.getenv("LEGION_BROKER_TYPE", "memory").lower()
        if broker_type_str not in ("redis", "memory"):
            broker_type_str = "memory"
        broker_type: BrokerType = broker_type_str  # type: ignore
        
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_db = int(os.getenv("REDIS_DB", "0"))
        
        buffer_size = int(os.getenv("LEGION_CONSUMER_BUFFER_SIZE", "1000"))
        max_retries = int(os.getenv("LEGION_CONSUMER_MAX_RETRIES", "3"))
        retry_delay = int(os.getenv("LEGION_CONSUMER_RETRY_DELAY_MS", "100"))
        
        pub_priority = int(os.getenv("LEGION_PUBLISHER_PRIORITY", "5"))
        batch_size = int(os.getenv("LEGION_PUBLISHER_BATCH_SIZE", "100"))
        
        log_level = os.getenv("LEGION_LOG_LEVEL", "INFO")
        log_events = os.getenv("LEGION_LOG_EVENTS", "true").lower() == "true"
        
        return cls(
            broker_type=broker_type,
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            redis_db=redis_db,
            consumer_buffer_size=buffer_size,
            consumer_max_retries=max_retries,
            consumer_retry_delay_ms=retry_delay,
            publisher_default_priority=pub_priority,
            publisher_batch_size=batch_size,
            log_level=log_level,
            log_events=log_events,
        )
    
    def to_dict(self) -> dict:
        """Serialize config to dict."""
        return {
            'broker_type': self.broker_type,
            'redis_host': self.redis_host,
            'redis_port': self.redis_port,
            'redis_db': self.redis_db,
            'consumer_buffer_size': self.consumer_buffer_size,
            'consumer_max_retries': self.consumer_max_retries,
            'consumer_retry_delay_ms': self.consumer_retry_delay_ms,
            'publisher_default_priority': self.publisher_default_priority,
            'publisher_batch_size': self.publisher_batch_size,
            'log_level': self.log_level,
            'log_events': self.log_events,
        }
