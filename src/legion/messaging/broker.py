"""
Message broker interface and Redis implementation.

This module provides the pub/sub abstraction layer that decouples agents.
"""

from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageBroker(ABC):
    """
    Abstract message broker interface.
    
    All agents communicate ONLY through this interface.
    Implementations can use Redis, RabbitMQ, Kafka, etc.
    """
    
    @abstractmethod
    async def publish(
        self, 
        channel: str, 
        event_data: dict
    ) -> None:
        """
        Publish event to channel.
        
        Args:
            channel: Channel name (e.g., 'market_data', 'signals')
            event_data: Event dict to publish
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[dict], None]
    ) -> None:
        """
        Subscribe to channel and handle events.
        
        Args:
            channel: Channel name to subscribe to
            handler: Async callable that processes events
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close broker connection."""
        pass


class RedisMessageBroker(MessageBroker):
    """
    Redis-based message broker implementation.
    
    Uses Redis pub/sub for event distribution.
    Supports channel subscriptions with async handlers.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379):
        """
        Initialize Redis broker.
        
        Args:
            host: Redis host
            port: Redis port
        """
        self.host = host
        self.port = port
        self.redis = None
        self.subscriptions: dict = {}
    
    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            import redis.asyncio as redis_module
            self.redis = await redis_module.from_url(
                f'redis://{self.host}:{self.port}',
                decode_responses=True,
                auto_close_conn_pool=False
            )
            logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
        except ImportError:
            raise ImportError(
                "redis[asyncio] not installed. Install with: pip install 'redis[asyncio]'"
            )
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def publish(
        self,
        channel: str,
        event_data: dict
    ) -> None:
        """Publish event to Redis channel."""
        if not self.redis:
            raise RuntimeError("Broker not connected. Call connect() first.")
        
        try:
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.utcnow().isoformat()
            
            message = json.dumps(event_data)
            await self.redis.publish(channel, message)
            logger.debug(f"Published to {channel}: {message[:100]}...")
        except Exception as e:
            logger.error(f"❌ Publish failed on {channel}: {e}")
            raise
    
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[dict], None]
    ) -> None:
        """Subscribe to Redis channel with async handler."""
        if not self.redis:
            raise RuntimeError("Broker not connected. Call connect() first.")
        
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"✅ Subscribed to channel: {channel}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        event_data = json.loads(message['data'])
                        await handler(event_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON decode error in {channel}: {e}")
                    except Exception as e:
                        logger.error(f"❌ Handler error in {channel}: {e}")
        except Exception as e:
            logger.error(f"❌ Subscribe failed on {channel}: {e}")
            raise
        finally:
            await pubsub.unsubscribe(channel)
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("✅ Redis connection closed")


class InMemoryMessageBroker(MessageBroker):
    """
    In-memory message broker for testing.
    
    Does NOT require Redis. Stores messages in memory.
    Useful for unit tests and local development.
    """
    
    def __init__(self):
        self.subscriptions: dict = {}
        self.history: List[dict] = []
    
    async def publish(self, channel: str, event_data: dict) -> None:
        """Store event in memory."""
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.utcnow().isoformat()
        
        self.history.append({
            'channel': channel,
            'data': event_data
        })
        
        if channel in self.subscriptions:
            for handler in self.subscriptions[channel]:
                await handler(event_data)
    
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[dict], None]
    ) -> None:
        """Register handler for channel."""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        self.subscriptions[channel].append(handler)
    
    async def close(self) -> None:
        """Clear all subscriptions."""
        self.subscriptions.clear()
