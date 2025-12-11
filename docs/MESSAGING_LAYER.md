# LEGION Messaging Layer - Complete Documentation

## Overview

Месседжинг слой обеспечивает **event-driven communication** между агентами Legion.

**Ключевые принципы:**
- ✅ **Decoupling**: Агенты не знают друг о друге
- ✅ **Scalability**: Новые агенты приобретают систему без рефакторинга
- ✅ **Async-native**: 100% asyncio compatible
- ✅ **Type-safe**: Strict typing + Pydantic-like validation
- ✅ **Redis optional**: Works with in-memory or Redis broker

---

## Architecture

```
┌────────────────────────────────┐
│             MESSAGE BUS LAYER ARCHITECTURE          │
├────────────────────────────────┤
│                                                      │
│  ┌──────────┐      ┌──────────┐    │
│  │ Publishers  │      │ Consumers  │    │
│  └──────────┘      └──────────┘    │
│           ↑                     ↓             │
│           └──────────────────────└             │
│                                                      │
│              ┌────────────┐                 │
│              │  Message Broker  │                 │
│              │ (Redis/Memory)  │                 │
│              └────────────┘                 │
│                      ↑ ↓                         │
│              ┌────────────┐                 │
│              │ Event Channels  │                 │
│              │ (Pub/Sub)       │                 │
│              └────────────┘                 │
│                                                      │
│              ┌────────────┐                 │
│              │ Handler Registry│                 │
│              │ (Priority Queue) │                 │
│              └────────────┘                 │
│                                                      │
├────────────────────────────────┤
│  Events → Types → Data → Handlers → Processing  │
└────────────────────────────────┘
```

---

## Core Components

### 1. **Event** (`events.py`)

Стандартная единица коммуникации.

```python
@dataclass
class Event:
    type: EventType          # Какое событие
    data: Dict[str, Any]    # Положная часть
    source_agent: str       # Кто отправил
    timestamp: datetime     # Когда
    correlation_id: str     # Для трейсинга
```

**EventType enum**:
- `MARKET_DATA_RECEIVED` - Новые данные рынка
- `FEATURES_COMPUTED` - Основы вычислены
- `SIGNAL_GENERATED` - Генератор выдал сигнал
- `TRADE_APPROVED` - Трейд риск-менеджер одобрил
- `ORDER_EXECUTED` - Ордер исполнен
- `AGENT_HEARTBEAT` - Агент еще жив
- и ещё 20+

---

### 2. **MessageBroker** (`broker.py`)

Основной pub/sub абстракт.

**Два реализации:**

#### 📘 **InMemoryMessageBroker**

```python
broker = InMemoryMessageBroker()
await broker.publish("market_data", event_dict)
await broker.subscribe("market_data", handler_func)
await broker.close()
```

Тестирование + local development. Без сложностей.

#### 🔴 **RedisMessageBroker**

```python
broker = RedisMessageBroker(host="localhost", port=6379)
await broker.connect()
await broker.publish("market_data", event_dict)
await broker.subscribe("market_data", handler_func)
await broker.close()
```

Production-grade. Надежные доставка.

---

### 3. **EventHandlerRegistry** (`handlers.py`)

Центральный реестр для всех обработчиков.

```python
registry = EventHandlerRegistry()

# Register handler
await registry.register(
    event_type=EventType.MARKET_DATA_RECEIVED,
    handler_func=async_handler_function,
    agent_name="feature_agent",
    handler_id="feature_agent_market_handler",
    priority=HandlerPriority.NORMAL,
)

# Dispatch event to all handlers
executed = await registry.dispatch(event)

# Get stats
stats = await registry.get_stats()
print(f"Total handlers: {stats['total_handlers']}")
print(f"Error rate: {stats['error_rate']:.2%}")
```

**HandlerPriority**:
- `CRITICAL = 0` - Системные обработчики (риск-менеджмент)
- `HIGH = 1` - Важные (генератор сигналов)
- `NORMAL = 5` - Обычные
- `LOW = 10` - Фоновые маны

---

### 4. **EventConsumer** (`consumer.py`)

База для агентов, которые потребляют события.

```python
class MarketDataAgent(EventConsumer):
    async def initialize(self):
        # Register handlers here
        await self.registry.register(
            event_type=EventType.MARKET_DATA_RECEIVED,
            handler_func=self.on_market_data,
            agent_name=self.agent_name,
            handler_id=f"{self.agent_name}_market_handler",
        )
    
    async def on_market_data(self, event: Event):
        # Process the event
        price = event.data['price']
        print(f"Market price: {price}")

# Usage
agent = MarketDataAgent(consumer_config)
await agent.initialize()
await agent.start()  # Start consuming

# Later:
await agent.stop()  # Stop consuming
```

---

### 5. **EventPublisher** (`publisher.py`)

Простой интерфейс для публикации.

```python
publisher = EventPublisher(
    PublisherConfig(agent_name="feature_agent", broker=broker)
)

# Publish single event
await publisher.publish(
    event_type=EventType.FEATURES_COMPUTED,
    data={"features": [...], "timestamp": ...},
    correlation_id="market_data_123",
)

# Publish batch
events = [
    (EventType.FEATURES_COMPUTED, {"features": f1}),
    (EventType.FEATURES_COMPUTED, {"features": f2}),
]
count = await publisher.publish_batch(events)

# Publish with retry
success = await publisher.publish_with_retry(
    event_type=EventType.SIGNAL_GENERATED,
    data={...},
    max_retries=3,
    retry_delay_ms=100,
)
```

---

## Quick Start

### 1. **Setup Message Bus**

```python
from src.legion.messaging import MessageBusFactory

# Create broker + registry
broker, registry = await MessageBusFactory.create_message_bus(
    broker_type="memory"  # or "redis"
)
```

### 2. **Create Consumer Agent**

```python
from src.legion.messaging import EventConsumer, ConsumerConfig
from src.legion.messaging.events import EventType

class MyAgent(EventConsumer):
    async def initialize(self):
        await self.registry.register(
            EventType.MARKET_DATA_RECEIVED,
            self.handle_market_data,
            self.agent_name,
            "my_handler",
        )
    
    async def handle_market_data(self, event):
        print(f"Got data: {event.data}")

config = ConsumerConfig(
    agent_name="my_agent",
    broker=broker,
    handler_registry=registry,
    subscribed_events=[EventType.MARKET_DATA_RECEIVED],
)

agent = MyAgent(config)
await agent.initialize()
await agent.start()
```

### 3. **Create Publisher Agent**

```python
from src.legion.messaging import EventPublisher, PublisherConfig

publisher = EventPublisher(
    PublisherConfig(agent_name="data_agent", broker=broker)
)

await publisher.publish(
    EventType.MARKET_DATA_RECEIVED,
    {"price": 50000, "volume": 100},
)
```

---

## Configuration

### Environment Variables

```bash
# Broker selection
export LEGION_BROKER_TYPE=redis  # or "memory"
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=secret

# Consumer config
export LEGION_CONSUMER_BUFFER_SIZE=1000
export LEGION_CONSUMER_MAX_RETRIES=3
export LEGION_CONSUMER_RETRY_DELAY_MS=100

# Logging
export LEGION_LOG_LEVEL=INFO
export LEGION_LOG_EVENTS=true
```

### Python Config

```python
from src.legion.messaging import MessageBusConfig

# From environment
config = MessageBusConfig.from_env()

# Or manual
config = MessageBusConfig(
    broker_type="redis",
    redis_host="localhost",
    redis_port=6379,
    consumer_buffer_size=1000,
    log_level="DEBUG",
)

print(config.to_dict())
```

---

## Best Practices

### ✅ **DO**

```python
# Use typed handlers
async def handle_market_data(event: Event) -> None:
    price = event.data.get('price')
    if price is None:
        logger.warning(f"Missing price in {event}")
        return
    # Process

# Use correlation IDs for tracing
await publisher.publish(
    EventType.SIGNAL_GENERATED,
    {...},
    correlation_id=event.correlation_id,  # Link to parent
)

# Handle errors gracefully
try:
    await publisher.publish_with_retry(...)
except Exception as e:
    logger.error(f"Final publish failed: {e}")
    # Fallback logic

# Use batch publishing for throughput
count = await publisher.publish_batch(events)
logger.info(f"Published {count} events")
```

### ❌ **DON'T**

```python
# Don't raise exceptions in handlers
async def bad_handler(event: Event) -> None:
    raise ValueError("Oops")  # Handler will be marked failed

# Instead, log and handle gracefully
async def good_handler(event: Event) -> None:
    try:
        # Process
    except ValueError as e:
        logger.error(f"Processing failed: {e}")
        # Continue

# Don't block in handlers
async def bad_handler(event: Event) -> None:
    time.sleep(10)  # Blocks entire bus

# Use async operations
async def good_handler(event: Event) -> None:
    await asyncio.sleep(10)  # Non-blocking
```

---

## Testing

```bash
# Run integration tests
pytest tests/messaging/test_integration.py -v

# Run specific test
pytest tests/messaging/test_integration.py::test_full_message_bus_flow -v

# With coverage
pytest tests/messaging/ --cov=src/legion/messaging
```

---

## Troubleshooting

### ✨ "No handlers registered for event"

```python
# Make sure you registered before publishing
await registry.register(EventType.MY_EVENT, handler, ...)
await publisher.publish(EventType.MY_EVENT, data)  # Now it works
```

### 😩 "Broker not connected"

```python
# For Redis, must call connect()
broker = RedisMessageBroker()
await broker.connect()  # <-- Required
await broker.publish(...)

# Memory broker doesn't need connect()
broker = InMemoryMessageBroker()  # Ready to use
await broker.publish(...)
```

### 🤧 "Circular dependencies"

Не будет! Agents communicate only via message bus.

---

## Performance Characteristics

| Operation | In-Memory | Redis |
|-----------|-----------|-------|
| Publish | < 1ms | ~5-10ms |
| Subscribe | < 1ms | ~1-2ms |
| Handler dispatch | O(n handlers) | O(n handlers) |
| Throughput | Limited by CPU | Limited by network |
| Persistence | None | Configurable |

---

## Next Steps (STEP 1.4)

- ✅ Distribution + multi-process support
- ✅ Dead-letter queue for failed events
- ✅ Event filtering + middleware
- ✅ Distributed tracing integration

**Status**: 🚀 **STAGE 1 COMPLETE**
