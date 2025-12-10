"""
Integration tests для messaging layer.

Тестирует полный flow: publish → broker → consumer → handler.
"""

import pytest
import asyncio
from datetime import datetime

from src.legion.messaging.broker import InMemoryMessageBroker
from src.legion.messaging.events import Event, EventType
from src.legion.messaging.handlers import (
    EventHandlerRegistry,
    EventHandler,
    HandlerPriority,
)
from src.legion.messaging.consumer import EventConsumer, ConsumerConfig
from src.legion.messaging.publisher import EventPublisher, PublisherConfig
from src.legion.messaging.factory import MessageBusFactory


class TestHandler(EventHandler):
    """Test handler для integration tests."""
    
    def __init__(self, agent_name: str):
        super().__init__(agent_name)
        self.received_events = []
    
    async def handle(self, event: Event) -> None:
        """Store event in list."""
        self.received_events.append(event)
    
    def can_handle(self, event: Event) -> bool:
        """Can handle market data events."""
        return event.type == EventType.MARKET_DATA_RECEIVED


class TestConsumer(EventConsumer):
    """Test consumer для integration tests."""
    
    def __init__(self, config: ConsumerConfig, test_handler: TestHandler):
        super().__init__(config)
        self.test_handler = test_handler
    
    async def initialize(self) -> None:
        """Register test handler."""
        await self.registry.register(
            event_type=EventType.MARKET_DATA_RECEIVED,
            handler_func=self.test_handler.handle,
            agent_name=self.agent_name,
            handler_id=f"{self.agent_name}_handler",
            priority=HandlerPriority.NORMAL,
        )


@pytest.mark.asyncio
async def test_full_message_bus_flow():
    """
    Test полного flow:
    Publisher → Broker → Consumer → Handler → Registry
    """
    # 1. Create message bus
    broker, registry = await MessageBusFactory.create_message_bus(
        broker_type="memory"
    )
    
    # 2. Create test handler
    test_handler = TestHandler(agent_name="test_agent")
    
    # 3. Create consumer
    consumer_config = ConsumerConfig(
        agent_name="test_consumer",
        broker=broker,
        handler_registry=registry,
        subscribed_events=[EventType.MARKET_DATA_RECEIVED],
    )
    consumer = TestConsumer(consumer_config, test_handler)
    await consumer.initialize()
    
    # 4. Create publisher
    publisher_config = PublisherConfig(
        agent_name="test_publisher",
        broker=broker,
    )
    publisher = EventPublisher(publisher_config)
    
    # 5. Start consumer
    await consumer.start()
    await asyncio.sleep(0.1)
    
    # 6. Publish event
    test_data = {"price": 50000, "volume": 100}
    await publisher.publish(
        event_type=EventType.MARKET_DATA_RECEIVED,
        data=test_data,
    )
    
    # 7. Wait for processing
    await asyncio.sleep(0.2)
    
    # 8. Verify event received
    assert len(test_handler.received_events) == 1
    received_event = test_handler.received_events[0]
    assert received_event.type == EventType.MARKET_DATA_RECEIVED
    assert received_event.data == test_data
    assert received_event.source_agent == "test_publisher"
    
    # 9. Check registry stats
    stats = await registry.get_stats()
    assert stats['total_executions'] == 1
    assert stats['total_errors'] == 0
    
    # 10. Cleanup
    await consumer.stop()
    await broker.close()


@pytest.mark.asyncio
async def test_handler_priority_execution_order():
    """Test что handlers выполняются по priority."""
    broker = InMemoryMessageBroker()
    registry = EventHandlerRegistry()
    
    execution_order = []
    
    async def high_priority_handler(event: Event):
        execution_order.append("HIGH")
    
    async def normal_priority_handler(event: Event):
        execution_order.append("NORMAL")
    
    async def low_priority_handler(event: Event):
        execution_order.append("LOW")
    
    # Register в обратном порядке
    await registry.register(
        EventType.MARKET_DATA_RECEIVED,
        low_priority_handler,
        "agent",
        "low",
        HandlerPriority.LOW,
    )
    await registry.register(
        EventType.MARKET_DATA_RECEIVED,
        normal_priority_handler,
        "agent",
        "normal",
        HandlerPriority.NORMAL,
    )
    await registry.register(
        EventType.MARKET_DATA_RECEIVED,
        high_priority_handler,
        "agent",
        "high",
        HandlerPriority.CRITICAL,
    )
    
    # Publish event
    event = Event(
        type=EventType.MARKET_DATA_RECEIVED,
        data={},
        source_agent="test",
    )
    
    await registry.dispatch(event)
    
    # Verify execution order: CRITICAL → NORMAL → LOW
    assert execution_order == ["HIGH", "NORMAL", "LOW"]


@pytest.mark.asyncio
async def test_batch_publishing():
    """Test batch publishing."""
    broker = InMemoryMessageBroker()
    publisher = EventPublisher(
        PublisherConfig(agent_name="test", broker=broker)
    )
    
    # Publish batch
    events = [
        (EventType.MARKET_DATA_RECEIVED, {"price": i})
        for i in range(10)
    ]
    
    count = await publisher.publish_batch(events)
    
    assert count == 10
    assert len(broker.history) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
