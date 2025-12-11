"""
Event middleware system for LEGION Message Bus.

STAGE 2A: Advanced Features
Component: Middleware Chain
Pattern: Chain of Responsibility
Purpose: Filter, enrich, transform events before dispatch

Features:
- Sequential middleware execution
- Event filtering
- Event enrichment
- Rate limiting
- Logging/monitoring

Risk Level: 🟢 LOW
Status: 🔥 IN DEVELOPMENT
Timeline: Week 1 of STAGE 2A
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Callable
import logging

logger = logging.getLogger(__name__)


class EventMiddleware(ABC):
    """
    Abstract base class for event middleware.
    
    Pattern: Chain of Responsibility
    Execution: Sequential (middleware in order)
    
    Middleware can:
    - Filter events (return None to skip)
    - Enrich events (add metadata)
    - Transform events (modify data)
    - Log/monitor events
    - Implement rate limiting
    """
    
    @abstractmethod
    async def process(self, event: 'Event') -> Optional['Event']:
        """
        Process event through middleware.
        
        Return: Modified event or None to skip
        """
        pass


class LoggingMiddleware(EventMiddleware):
    """Log all events passing through middleware chain."""
    
    async def process(self, event: 'Event') -> Optional['Event']:
        logger.info(
            f"📤 Event: {event.type.value} "
            f"from {event.source_agent}"
        )
        return event


class FilteringMiddleware(EventMiddleware):
    """Filter events based on predicate."""
    
    def __init__(self, predicate: Callable[['Event'], bool]):
        self.predicate = predicate
    
    async def process(self, event: 'Event') -> Optional['Event']:
        if not self.predicate(event):
            logger.debug(f"🔕 Event filtered: {event.type.value}")
            return None
        return event


class RateLimitMiddleware(EventMiddleware):
    """Rate limit events per source agent."""
    
    def __init__(self, redis_client, max_per_minute: int = 1000):
        self.redis = redis_client
        self.max_per_minute = max_per_minute
    
    async def process(self, event: 'Event') -> Optional['Event']:
        key = f"rate_limit:{event.source_agent}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 60)
        
        if count > self.max_per_minute:
            logger.warning(
                f"⚠️ Rate limit exceeded: {event.source_agent}"
            )
            return None
        
        return event


class EnrichmentMiddleware(EventMiddleware):
    """Add metadata to events."""
    
    async def process(self, event: 'Event') -> Optional['Event']:
        from datetime import datetime
        event.metadata['processed_at'] = datetime.utcnow().isoformat()
        event.metadata['middleware_version'] = '2.0'
        return event
