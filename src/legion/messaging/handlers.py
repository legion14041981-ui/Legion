"""
Event handler interface and handler registry.

Handlers are the bridge between agents and message bus.
Each agent registers handlers for events it cares about.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Any, Optional, Awaitable
from dataclasses import dataclass, field
import asyncio
import logging
from enum import Enum
from datetime import datetime

from .events import Event, EventType

logger = logging.getLogger(__name__)


class HandlerPriority(int, Enum):
    """Handler execution priority."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 5
    LOW = 10


@dataclass
class HandlerMetadata:
    """Metadata about a registered handler."""
    
    handler_id: str
    event_type: EventType
    priority: HandlerPriority
    agent_name: str
    async_func: Callable[[Event], Awaitable[None]]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_count: int = 0
    last_execution: Optional[str] = None
    error_count: int = 0
    last_error: Optional[str] = None


class EventHandler(ABC):
    """
    Abstract base class for event handlers.
    
    Each agent that processes events should subclass this
    and implement handle() method.
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """
        Process an event.
        
        Must be implemented by subclasses.
        Should not raise exceptions (log them instead).
        
        Args:
            event: Event to process
        """
        pass
    
    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """
        Check if this handler can process the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if handler can process event
        """
        pass


class EventHandlerRegistry:
    """
    Central registry for all event handlers.
    
    Manages:
    - Handler registration/unregistration
    - Handler lookup by event type
    - Handler execution with priority
    - Error tracking and retry logic
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[HandlerMetadata]] = {}
        self._all_handlers: Dict[str, HandlerMetadata] = {}
        self._lock = asyncio.Lock()
    
    async def register(
        self,
        event_type: EventType,
        handler_func: Callable[[Event], Awaitable[None]],
        agent_name: str,
        handler_id: str,
        priority: HandlerPriority = HandlerPriority.NORMAL
    ) -> str:
        """
        Register a handler for an event type.
        
        Args:
            event_type: EventType to handle
            handler_func: Async function to call
            agent_name: Name of agent registering handler
            handler_id: Unique handler identifier
            priority: Execution priority
            
        Returns:
            Handler ID
        """
        async with self._lock:
            metadata = HandlerMetadata(
                handler_id=handler_id,
                event_type=event_type,
                priority=priority,
                agent_name=agent_name,
                async_func=handler_func,
            )
            
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            self._handlers[event_type].append(metadata)
            self._all_handlers[handler_id] = metadata
            
            self._handlers[event_type].sort(key=lambda h: h.priority)
            
            logger.info(
                f"✅ Registered handler {handler_id} for {event_type.value} "
                f"(agent={agent_name}, priority={priority.name})"
            )
            
            return handler_id
    
    async def unregister(self, handler_id: str) -> bool:
        """
        Unregister a handler.
        
        Args:
            handler_id: Handler ID to remove
            
        Returns:
            True if handler was found and removed
        """
        async with self._lock:
            if handler_id not in self._all_handlers:
                return False
            
            metadata = self._all_handlers.pop(handler_id)
            self._handlers[metadata.event_type].remove(metadata)
            
            logger.info(f"✅ Unregistered handler {handler_id}")
            return True
    
    async def get_handlers(self, event_type: EventType) -> List[HandlerMetadata]:
        """
        Get all handlers for an event type (sorted by priority).
        
        Args:
            event_type: EventType to get handlers for
            
        Returns:
            List of handler metadata, sorted by priority (lowest first)
        """
        async with self._lock:
            return self._handlers.get(event_type, []).copy()
    
    async def dispatch(self, event: Event) -> int:
        """
        Execute all handlers for an event in priority order.
        
        Args:
            event: Event to dispatch
            
        Returns:
            Number of handlers executed successfully
        """
        handlers = await self.get_handlers(event.type)
        
        if not handlers:
            logger.debug(f"No handlers registered for {event.type.value}")
            return 0
        
        executed = 0
        
        for metadata in handlers:
            try:
                await metadata.async_func(event)
                
                async with self._lock:
                    metadata.execution_count += 1
                    metadata.last_execution = datetime.utcnow().isoformat()
                
                executed += 1
                
            except Exception as e:
                logger.error(
                    f"❌ Handler {metadata.handler_id} failed: {e}",
                    exc_info=True
                )
                async with self._lock:
                    metadata.error_count += 1
                    metadata.last_error = str(e)
        
        logger.debug(
            f"Dispatched {event.type.value} to {executed}/{len(handlers)} handlers"
        )
        
        return executed
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Stats dict with handler counts, error rates, etc.
        """
        async with self._lock:
            total_handlers = len(self._all_handlers)
            total_executions = sum(h.execution_count for h in self._all_handlers.values())
            total_errors = sum(h.error_count for h in self._all_handlers.values())
            
            return {
                'total_handlers': total_handlers,
                'event_types': len(self._handlers),
                'total_executions': total_executions,
                'total_errors': total_errors,
                'error_rate': total_errors / max(1, total_executions),
                'handlers_by_event': {
                    et.value: len(handlers)
                    for et, handlers in self._handlers.items()
                },
            }
    
    async def clear(self) -> None:
        """Clear all registered handlers."""
        async with self._lock:
            self._handlers.clear()
            self._all_handlers.clear()
            logger.info("✅ Handler registry cleared")
