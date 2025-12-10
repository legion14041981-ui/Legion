"""
Event consumer base class and consumer utilities.

Consumers listen to message bus and process events.
Base template for agents that are event listeners.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import asyncio
import logging
from dataclasses import dataclass

from .broker import MessageBroker
from .events import Event, EventType
from .handlers import EventHandler, EventHandlerRegistry, HandlerPriority

logger = logging.getLogger(__name__)


@dataclass
class ConsumerConfig:
    """Configuration for event consumer."""
    
    agent_name: str
    broker: MessageBroker
    handler_registry: EventHandlerRegistry
    subscribed_events: List[EventType]
    buffer_size: int = 1000
    max_retries: int = 3
    retry_delay_ms: int = 100


class EventConsumer(ABC):
    """
    Base class for agents that consume events from message bus.
    
    Lifecycle:
    1. Initialize with config
    2. Register handlers via handler_registry
    3. Call start() to begin listening
    4. Receive events via registered handlers
    5. Call stop() to shutdown
    """
    
    def __init__(self, config: ConsumerConfig):
        self.config = config
        self.agent_name = config.agent_name
        self.broker = config.broker
        self.registry = config.handler_registry
        
        self._running = False
        self._listener_tasks: List[asyncio.Task] = []
        self.logger = logging.getLogger(f"{__name__}.{self.agent_name}")
    
    async def start(self) -> None:
        """Start consuming events from message bus."""
        if self._running:
            self.logger.warning("Consumer already running")
            return
        
        self._running = True
        self.logger.info(f"✅ Starting consumer for {self.config.subscribed_events}")
        
        for event_type in self.config.subscribed_events:
            task = asyncio.create_task(self._listen_to_channel(event_type.value))
            self._listener_tasks.append(task)
        
        self.logger.info(f"✅ Consumer {self.agent_name} started")
    
    async def stop(self) -> None:
        """Stop consuming events and cleanup."""
        if not self._running:
            return
        
        self._running = False
        self.logger.info(f"Stopping consumer {self.agent_name}...")
        
        for task in self._listener_tasks:
            task.cancel()
        
        await asyncio.gather(*self._listener_tasks, return_exceptions=True)
        self._listener_tasks.clear()
        
        self.logger.info(f"✅ Consumer {self.agent_name} stopped")
    
    async def _listen_to_channel(self, channel: str) -> None:
        """Listen to a message bus channel."""
        self.logger.debug(f"Listening to channel: {channel}")
        
        try:
            async def handler(event_data: dict) -> None:
                try:
                    event = Event.from_dict(event_data)
                    await self.registry.dispatch(event)
                except Exception as e:
                    self.logger.error(f"❌ Error processing event: {e}", exc_info=True)
            
            await self.broker.subscribe(channel, handler)
        except asyncio.CancelledError:
            self.logger.debug(f"Listener task cancelled for {channel}")
        except Exception as e:
            self.logger.error(f"❌ Listener error on {channel}: {e}", exc_info=True)
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize consumer resources."""
        pass
    
    async def get_status(self) -> dict:
        """Get consumer status."""
        return {
            'agent_name': self.agent_name,
            'running': self._running,
            'subscribed_events': [e.value for e in self.config.subscribed_events],
            'listener_tasks': len(self._listener_tasks),
            'registry_stats': await self.registry.get_stats(),
        }
