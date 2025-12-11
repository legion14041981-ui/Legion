"""
Event publisher utilities and base publisher class.

Publishers send events to message bus.
Template for agents that produce events.
"""

from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
import asyncio

from .broker import MessageBroker
from .events import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class PublisherConfig:
    """Configuration for event publisher."""
    
    agent_name: str
    broker: MessageBroker
    default_priority: int = 5


class EventPublisher:
    """
    Base class for agents that publish events to message bus.
    
    Provides convenient interface for sending typed events.
    Handles serialization and error handling.
    """
    
    def __init__(self, config: PublisherConfig):
        self.agent_name = config.agent_name
        self.broker = config.broker
        self.logger = logging.getLogger(f"{__name__}.{self.agent_name}")
    
    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an event to message bus.
        
        Args:
            event_type: Type of event to publish
            data: Event payload
            correlation_id: Optional correlation ID for tracing
            metadata: Optional additional metadata
        """
        try:
            event = Event(
                type=event_type,
                data=data,
                source_agent=self.agent_name,
                correlation_id=correlation_id,
                metadata=metadata or {},
            )
            
            channel = event_type.value
            event_dict = event.to_dict()
            
            await self.broker.publish(channel, event_dict)
            
            self.logger.debug(f"📤 Published {event_type.value}")
            
        except Exception as e:
            self.logger.error(
                f"❌ Failed to publish {event_type.value}: {e}",
                exc_info=True
            )
            raise
    
    async def publish_batch(
        self,
        events: list[tuple[EventType, Dict[str, Any]]],
    ) -> int:
        """
        Publish multiple events efficiently.
        
        Args:
            events: List of (event_type, data) tuples
            
        Returns:
            Number of successfully published events
        """
        success_count = 0
        
        for event_type, data in events:
            try:
                await self.publish(event_type, data)
                success_count += 1
            except Exception as e:
                self.logger.warning(f"⚠️ Skipped event {event_type.value}: {e}")
                continue
        
        self.logger.info(f"📤 Published {success_count}/{len(events)} events")
        
        return success_count
    
    async def publish_with_retry(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        max_retries: int = 3,
        retry_delay_ms: int = 100,
    ) -> bool:
        """
        Publish event with automatic retry on failure.
        
        Args:
            event_type: Type of event
            data: Event payload
            max_retries: Max retry attempts
            retry_delay_ms: Delay between retries (milliseconds)
            
        Returns:
            True if published successfully
        """
        for attempt in range(max_retries):
            try:
                await self.publish(event_type, data)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"⚠️ Publish failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay_ms}ms: {e}"
                    )
                    await asyncio.sleep(retry_delay_ms / 1000.0)
                else:
                    self.logger.error(
                        f"❌ Failed to publish after {max_retries} attempts: {e}"
                    )
                    return False
        
        return False
