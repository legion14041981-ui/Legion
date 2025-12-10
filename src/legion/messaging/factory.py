"""
Message bus factory - создание и конфигурация message bus.

Централизованное создание broker + registry + config.
"""

from typing import Optional, Literal
import os
import logging

from .broker import MessageBroker, RedisMessageBroker, InMemoryMessageBroker
from .handlers import EventHandlerRegistry

logger = logging.getLogger(__name__)


BrokerType = Literal["redis", "memory"]


class MessageBusFactory:
    """
    Factory для создания message bus компонентов.
    
    Создаёт broker + registry на основе конфигурации.
    Поддерживает auto-detection окружения.
    """
    
    @staticmethod
    async def create_broker(
        broker_type: Optional[BrokerType] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ) -> MessageBroker:
        """
        Создать message broker.
        
        Args:
            broker_type: Тип broker ("redis" или "memory").
                         Если None — auto-detect из ENV.
            redis_host: Redis host (если используется Redis)
            redis_port: Redis port (если используется Redis)
            
        Returns:
            Настроенный message broker
        """
        if broker_type is None:
            broker_type = MessageBusFactory._detect_broker_type()
        
        if broker_type == "redis":
            logger.info(f"Creating Redis broker at {redis_host}:{redis_port}")
            broker = RedisMessageBroker(host=redis_host, port=redis_port)
            await broker.connect()
            return broker
        
        elif broker_type == "memory":
            logger.info("Creating in-memory broker (no Redis)")
            return InMemoryMessageBroker()
        
        else:
            raise ValueError(f"Unknown broker type: {broker_type}")
    
    @staticmethod
    def _detect_broker_type() -> BrokerType:
        """
        Auto-detect broker type из переменных окружения.
        
        Returns:
            Detected broker type
        """
        if os.getenv("LEGION_BROKER_TYPE"):
            broker_str = os.getenv("LEGION_BROKER_TYPE", "").lower()
            if broker_str in ("redis", "memory"):
                logger.info(f"Detected broker type from ENV: {broker_str}")
                return broker_str  # type: ignore
        
        if os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"):
            logger.info("Detected Redis from environment")
            return "redis"
        
        logger.warning("No broker config found, using in-memory broker")
        return "memory"
    
    @staticmethod
    def create_registry() -> EventHandlerRegistry:
        """
        Создать event handler registry.
        
        Returns:
            Новый экземпляр registry
        """
        return EventHandlerRegistry()
    
    @staticmethod
    async def create_message_bus(
        broker_type: Optional[BrokerType] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ) -> tuple[MessageBroker, EventHandlerRegistry]:
        """
        Создать полный message bus (broker + registry).
        
        Args:
            broker_type: Тип broker
            redis_host: Redis host
            redis_port: Redis port
            
        Returns:
            (broker, registry) tuple
        """
        broker = await MessageBusFactory.create_broker(
            broker_type=broker_type,
            redis_host=redis_host,
            redis_port=redis_port,
        )
        registry = MessageBusFactory.create_registry()
        
        logger.info("✅ Message bus created successfully")
        
        return broker, registry
