"""
Message Bus Layer - Event-driven communication for LEGION agents.

This layer decouples agents via publish/subscribe pattern,
eliminating circular dependencies and enabling scalability.
"""

from .broker import MessageBroker, RedisMessageBroker, InMemoryMessageBroker
from .events import Event, EventType
from .handlers import EventHandler, EventHandlerRegistry
from .consumer import EventConsumer, ConsumerConfig
from .publisher import EventPublisher, PublisherConfig
from .factory import MessageBusFactory
from .config import MessageBusConfig

__all__ = [
    'MessageBroker',
    'RedisMessageBroker',
    'InMemoryMessageBroker',
    'Event',
    'EventType',
    'EventHandler',
    'EventHandlerRegistry',
    'EventConsumer',
    'ConsumerConfig',
    'EventPublisher',
    'PublisherConfig',
    'MessageBusFactory',
    'MessageBusConfig',
]

__version__ = '1.0.0'
