# 📨 **LEGION Message Bus v2.0 Integration Guide**

**For**: ApexTrader v4 Agents  
**Status**: 🔥 **PRODUCTION INTEGRATION PROTOCOL**

## **Part 1: Event Publishing from Agent**

```python
from legion.messaging import EventPublisher, Event, EventType
import logging

logger = logging.getLogger(__name__)

class TradingAgent(EventPublisher):
    """Base class for trading agents."""
    
    def __init__(self, agent_name: str, broker_url: str = "redis://localhost:6379"):
        super().__init__(broker_url=broker_url)
        self.agent_name = agent_name
    
    async def publish_trade_signal(self, signal_data: dict):
        """
        Publish trade signal to message bus.
        
        Data will flow through:
        1. Middleware chain (logging, filtering, rate limiting)
        2. Subscriber handlers (StrategyBuilder, RiskManager)
        3. DLQ captures failures
        4. Tracing tracks correlation ID
        """
        
        event = Event(
            type=EventType.STRATEGY_SIGNAL_GENERATED,
            data=signal_data,
            source_agent=self.agent_name,
            correlation_id=self.generate_correlation_id()  # Auto-generated
        )
        
        try:
            await self.publish(event)
            logger.info(f"Signal published: {event.message_id}")
        except Exception as e:
            logger.error(f"Publish failed: {e}")
            # Will be captured by DLQ if handler fails
            raise
```

## **Part 2: Event Consumption and Middleware**

```python
from legion.messaging import EventConsumer, EventType
from legion.messaging.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    EnrichmentMiddleware
)

class StrategyBuilder(EventConsumer):
    """Subscribe to features and generate trading strategies."""
    
    def __init__(self, broker_url: str = "redis://localhost:6379"):
        super().__init__(broker_url=broker_url)
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Configure middleware chain."""
        
        # Middleware execute in order: Logging -> RateLimit -> Enrichment
        self.middleware = [
            LoggingMiddleware(),
            RateLimitMiddleware(
                redis_client=self.redis,
                max_per_minute=10000  # Allow high frequency
            ),
            EnrichmentMiddleware()
        ]
    
    async def handle_features(self, event: Event):
        """Process feature event and generate strategies."""
        
        # Middleware already executed - event is clean and enriched
        features = event.data["features"]
        
        # Generate candidate trades
        trades = self._generate_candidates(features)
        
        for trade in trades:
            strategy_event = Event(
                type=EventType.STRATEGY_CANDIDATE_CREATED,
                data=trade,
                source_agent="StrategyBuilder",
                correlation_id=event.correlation_id  # Preserve chain
            )
            
            # Error here will go to DLQ automatically
            await self.publish(strategy_event)
    
    async def start(self):
        """Start consuming events."""
        await self.subscribe(
            event_type=EventType.FEATURES_COMPUTED,
            handler=self.handle_features,
            middleware=self.middleware,
            priority="HIGH"
        )
        
        logger.info("StrategyBuilder listening for features...")
        await self.run()
```

## **Part 3: DLQ Error Recovery**

```python
from legion.messaging.dlq import DeadLetterQueue

class ErrorRecoveryService:
    """Monitor and recover from event failures."""
    
    def __init__(self, redis_client, redis_url: str):
        self.dlq = DeadLetterQueue(
            redis_client=redis_client,
            ttl_days=30
        )
        self.redis_url = redis_url
    
    async def monitor_dlq(self):
        """Check for failed events and attempt recovery."""
        
        while True:
            # Get pending failures
            failures = await self.dlq.get_failed_events(
                limit=100,
                status="pending"
            )
            
            for failure in failures:
                logger.warning(f"Failed event in DLQ: {failure.dlq_id}")
                
                # Attempt automatic retry
                if failure.retry_count < 3:
                    success = await self._retry_event(failure)
                    
                    if success:
                        logger.info(f"✓ Event recovered: {failure.dlq_id}")
                    else:
                        logger.error(f"✗ Retry failed: {failure.dlq_id}")
                else:
                    logger.critical(f"Max retries exceeded: {failure.dlq_id}")
                    # Alert team
                    await self._send_alert(failure)
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _retry_event(self, failure) -> bool:
        """Attempt to reprocess failed event."""
        try:
            # Get original handler
            handler_name = failure.failed_handler_id
            handler = self._get_handler(handler_name)
            
            # Re-invoke with original event
            await handler(failure.event)
            
            # Mark as resolved
            await self.dlq.mark_resolved(failure.dlq_id)
            return True
            
        except Exception as e:
            logger.error(f"Retry error: {e}")
            return False
```

## **Part 4: Distributed Tracing**

```python
from legion.messaging.tracing import TracingMiddleware
from opentelemetry import trace

class ObservableAgent(EventConsumer, EventPublisher):
    """Agent with full tracing support."""
    
    def __init__(self):
        super().__init__()
        self.tracer = trace.get_tracer(__name__)
    
    async def process_with_tracing(self, event: Event):
        """Process event with distributed tracing."""
        
        with self.tracer.start_as_current_span(
            f"process:{event.type.value}"
        ) as span:
            # Add attributes for Jaeger
            span.set_attribute("event.id", event.message_id)
            span.set_attribute("event.type", event.type.value)
            span.set_attribute("event.source", event.source_agent)
            span.set_attribute("correlation_id", event.correlation_id)
            
            # Do processing
            try:
                result = await self._process(event)
                span.set_attribute("status", "success")
                return result
            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error.message", str(e))
                raise
    
    # Result visible in Jaeger UI:
    # - Full event flow with timing
    # - Error detection and stack traces
    # - Performance bottlenecks
    # - Correlation IDs linking all events in single trade lifecycle
```

## **Part 5: Event Versioning & Migration**

```python
from legion.messaging.versioning import EventVersion

# When event schema changes:
# Strategy event v0.9 → v1.0
# Old schema: {entry, stop, take}
# New schema: {entry, stop, take, confidence, rationale}

event_old_schema = Event(
    type=EventType.STRATEGY_CANDIDATE_CREATED,
    data={
        "entry": 95550,
        "stop": 95000,
        "take": 96500
    },
    schema_version="0.9"  # Mark old version
)

# On consumption, auto-migrate:
event_migrated = event_old_schema.migrate_to_current()
# Now has: entry, stop, take, confidence=0.7, rationale="auto_migrated"
```

## **Part 6: Metrics & Observability**

```python
from legion.messaging.metrics import MetricsCollector
import prometheus_client

collector = MetricsCollector()

# Automatically tracked:
# - legion_events_total{event_type="MARKET_DATA_RECEIVED", source="MarketScanner"}
# - legion_handler_duration_ms{handler_id="StrategyBuilder", event_type="..."}
# - legion_errors_total{handler_id="ExecutionAgent", error_type="SlippageExceeded"}
# - legion_dlq_entries{status="pending", handler_id="RiskManager"}
# - legion_middleware_latency_ms{middleware="RateLimitMiddleware"}

# Metrics available at:
# GET /metrics (Prometheus format)
```

---

**Status**: ✅ **INTEGRATION READY**  
**Next**: Deploy agents and validate event flow
