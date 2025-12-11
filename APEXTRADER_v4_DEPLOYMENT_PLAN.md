# 🚀 **APEXTRADER v4.0 + STAGE 2A INTEGRATION: COMBAT DEPLOYMENT**

**Status**: 🔥 **FULL BATTLE DEPLOYMENT**  
**Timeline**: Weeks 1-4 (Priority Integration)  
**Objective**: Deploy ApexTrader v4 (7 agents) on top of LEGION Message Bus v2.0

---

## 🔫 **IMMEDIATE DEPLOYMENT STRATEGY**

### **Phase 0: Integration Architecture (Days 1-2)**

```
ApexTrader v4.0 Architecture:
┌─────────────────────────────────────────────────────────┐
│                   MARKET DATA LAYER                       │
│        (Binance, Bybit, OKX public API)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼──────────┐        ┌────────▼──────────┐
│ 1. MarketScanner │        │ 4. EventWatcher   │
└────────┬─────────┘        └────────┬──────────┘
         │                           │
         │    ┌─────────────────────────────────────┐
         │    │  LEGION MESSAGE BUS v2.0 (STAGE 2A) │
         │    │  [DLQ + Middleware + Tracing]       │
         │    └─────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 2. FeatureEngineer               │
│    (ATR, RSI, MACD, CVD)        │
└────────┬───────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 3. StrategyBuilder               │
│    (Breakout, Mean-Reversion)   │
└────────┬───────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 5. Backtester/Simulator          │
│    (Walk-forward validation)     │
└────────┬───────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 6. RiskManager                   │
│    (Final gate, position sizing) │
└────────┬───────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 7. ExecutionAgent                │
│    (Order execution)             │
└──────────────────────────────────┘
```

**Integration Points**:
- All agent-to-agent communication via LEGION Message Bus
- Each agent as independent process/pod
- Events published to event streams (not direct calls)
- DLQ captures failed agent outputs
- Middleware chain for validation/enrichment
- Full tracing for entire pipeline

---

### **Phase 1: Agent Containerization (Week 1)**

#### **1.1 Docker Images for each Agent**

```bash
# agents/market_scanner/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:5001/health || exit 1
```

#### **1.2 Message Bus Integration**

```python
# agents/market_scanner/main.py

from legion.messaging import EventPublisher, Event, EventType
import asyncio

class MarketScannerAgent(EventPublisher):
    def __init__(self, broker_url: str = "redis://localhost:6379"):
        super().__init__(broker_url=broker_url)
        self.source_agent = "MarketScanner"
    
    async def collect_market_data(self, symbol: str = "BTCUSDT"):
        """Collect OHLCV, funding, depth data."""
        
        # Fetch from Binance, Bybit, OKX
        data = await self._fetch_multiexchange(symbol)
        
        # Publish as event
        event = Event(
            type=EventType.MARKET_DATA_RECEIVED,
            data={
                "symbol": symbol,
                "ohlcv": data["ohlcv"],
                "funding": data["funding"],
                "depth": data["depth"],
                "liquidations_24h": data["liquidations"]
            },
            source_agent=self.source_agent,
            correlation_id=self.generate_correlation_id()
        )
        
        # Publish to message bus
        await self.publish(event)
        
        self.logger.info(f"Published market data: {symbol}")
        
    async def start_continuous_collection(self):
        """Run continuous data collection."""
        while True:
            try:
                await self.collect_market_data("BTCUSDT")
                await asyncio.sleep(0.5)  # 2 Hz frequency
            except Exception as e:
                self.logger.error(f"Collection error: {e}")
                await asyncio.sleep(1)

app = FastAPI()
agent = MarketScannerAgent()

@app.on_event("startup")
async def startup():
    asyncio.create_task(agent.start_continuous_collection())

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "MarketScanner"}

@app.get("/metrics")
async def metrics():
    return {
        "events_published": agent.event_count,
        "last_update_ms": agent.last_update_time,
        "data_freshness_ms": agent.data_freshness_ms
    }
```

#### **1.3 Feature Engineer with Message Bus**

```python
# agents/feature_engineer/main.py

from legion.messaging import EventConsumer, Event, EventType, EventPublisher

class FeatureEngineerAgent(EventConsumer, EventPublisher):
    def __init__(self, broker_url: str = "redis://localhost:6379"):
        EventConsumer.__init__(self, broker_url=broker_url)
        EventPublisher.__init__(self, broker_url=broker_url)
        self.source_agent = "FeatureEngineer"
    
    async def handle_market_data(self, event: Event):
        """Process market data and compute features."""
        
        try:
            data = event.data
            symbol = data["symbol"]
            
            # Compute indicators
            features = {
                "atr_14": self._compute_atr(data["ohlcv"], 14),
                "rsi_14": self._compute_rsi(data["ohlcv"], 14),
                "macd": self._compute_macd(data["ohlcv"]),
                "ema": self._compute_emas(data["ohlcv"], [20, 50, 200])
            }
            
            # Create feature event
            feature_event = Event(
                type=EventType.FEATURES_COMPUTED,
                data={
                    "symbol": symbol,
                    "features": features,
                    "timestamp": event.timestamp
                },
                source_agent=self.source_agent,
                correlation_id=event.correlation_id  # Preserve correlation
            )
            
            # Publish to message bus
            await self.publish(feature_event)
            self.logger.info(f"Features computed: {symbol}")
            
        except Exception as e:
            self.logger.error(f"Feature computation error: {e}")
            # Error will be captured by DLQ via middleware
            raise
    
    async def start(self):
        """Subscribe to market data events."""
        await self.subscribe(
            event_type=EventType.MARKET_DATA_RECEIVED,
            handler=self.handle_market_data,
            priority="HIGH"
        )
        await self.run()

app = FastAPI()
agent = FeatureEngineerAgent()

@app.on_event("startup")
async def startup():
    asyncio.create_task(agent.start())

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "FeatureEngineer"}
```

---

### **Phase 2: Docker Compose Orchestration (Week 2)**

```yaml
# docker-compose.production.yml

version: '3.8'

services:
  
  # Infrastructure
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
  
  # STAGE 2A Components
  message-bus:
    build:
      context: ./infrastructure/message-bus
      dockerfile: Dockerfile
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    volumes:
      - ./config.json:/app/config.json
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  # ApexTrader Agents
  market-scanner:
    build:
      context: ./agents/market_scanner
      dockerfile: Dockerfile
    depends_on:
      message-bus:
        condition: service_healthy
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - REDIS_URL=redis://redis:6379
      - AGENT_NAME=MarketScanner
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    ports:
      - "5001:5001"
    restart: on-failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  feature-engineer:
    build:
      context: ./agents/feature_engineer
      dockerfile: Dockerfile
    depends_on:
      market-scanner:
        condition: service_healthy
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - REDIS_URL=redis://redis:6379
      - AGENT_NAME=FeatureEngineer
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    ports:
      - "5002:5002"
    restart: on-failure
  
  event-watcher:
    build:
      context: ./agents/event_watcher
      dockerfile: Dockerfile
    depends_on:
      message-bus:
        condition: service_healthy
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - AGENT_NAME=EventWatcher
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    ports:
      - "5003:5003"
    restart: on-failure
  
  strategy-builder:
    build:
      context: ./agents/strategy_builder
      dockerfile: Dockerfile
    depends_on:
      - feature-engineer
      - event-watcher
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - AGENT_NAME=StrategyBuilder
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    ports:
      - "5004:5004"
    restart: on-failure
  
  backtester:
    build:
      context: ./agents/backtester
      dockerfile: Dockerfile
    depends_on:
      - strategy-builder
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - AGENT_NAME=Backtester
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "5005:5005"
    restart: on-failure
  
  risk-manager:
    build:
      context: ./agents/risk_manager
      dockerfile: Dockerfile
    depends_on:
      - backtester
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - AGENT_NAME=RiskManager
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    ports:
      - "5006:5006"
    restart: on-failure
  
  execution-agent:
    build:
      context: ./agents/execution_agent
      dockerfile: Dockerfile
    depends_on:
      - risk-manager
    environment:
      - MESSAGE_BUS_URL=http://message-bus:8000
      - EXCHANGE_API_KEY=${EXCHANGE_API_KEY}
      - EXCHANGE_API_SECRET=${EXCHANGE_API_SECRET}
      - DRY_RUN=${DRY_RUN:-true}
    volumes:
      - ./config.json:/app/config.json
      - ./logs:/app/logs
    ports:
      - "5007:5007"
    restart: on-failure
  
  # Observability Stack
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "6831:6831/udp"  # OpenTelemetry UDP
      - "16686:16686"    # UI
    environment:
      - COLLECTOR_ZIPKIN_HTTP_PORT=9411
  
  grafana:
    image: grafana/grafana:latest
    depends_on:
      - prometheus
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

---

### **Phase 3: Deployment Scripts (Week 3)**

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Starting ApexTrader v4 + STAGE 2A deployment..."

# 1. Build all Docker images
echo "Building Docker images..."
docker-compose -f docker-compose.production.yml build --no-cache

# 2. Start infrastructure
echo "Starting infrastructure (Redis, Prometheus, Jaeger)..."
docker-compose -f docker-compose.production.yml up -d redis prometheus jaeger

# 3. Wait for redis to be ready
echo "Waiting for Redis..."
for i in {1..30}; do
  if docker exec $(docker ps -f name=redis -q) redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✓ Redis ready"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 1
done

# 4. Start message bus
echo "Starting LEGION Message Bus v2.0..."
docker-compose -f docker-compose.production.yml up -d message-bus

# Wait for message bus
sleep 5
curl http://localhost:8000/health || exit 1

# 5. Start agents in order
echo "Starting agents..."
for agent in market-scanner feature-engineer event-watcher strategy-builder backtester risk-manager execution-agent; do
  echo "Starting $agent..."
  docker-compose -f docker-compose.production.yml up -d $agent
  sleep 3
done

# 6. Start observability
echo "Starting observability stack..."
docker-compose -f docker-compose.production.yml up -d grafana

# 7. Run health checks
echo "Running health checks..."
for port in 5001 5002 5003 5004 5005 5006 5007; do
  for i in {1..10}; do
    if curl -s http://localhost:$port/health | grep -q healthy; then
      echo "✓ Agent on port $port healthy"
      break
    fi
    echo "Waiting for port $port... ($i/10)"
    sleep 1
  done
done

echo ""
echo "✅ DEPLOYMENT COMPLETE"
echo ""
echo "Access points:"
echo "  - Grafana:    http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Jaeger:     http://localhost:16686"
echo "  - APIs:       http://localhost:500X (X = 1-7 for agents)"
echo ""
```

---

## 📋 **INTEGRATION CHECKLIST**

### **Week 1: Architecture & Setup**
- [ ] Message Bus interface designed
- [ ] Event types defined for all agent outputs
- [ ] Docker images for each agent created
- [ ] redis setup for message broker
- [ ] Health check endpoints implemented

### **Week 2: Agent Integration**
- [ ] MarketScanner → Message Bus
- [ ] FeatureEngineer → Event consumer/publisher
- [ ] EventWatcher → Message Bus events
- [ ] StrategyBuilder → Event-driven
- [ ] Backtester → Async validation
- [ ] RiskManager → Final approval gate
- [ ] ExecutionAgent → Order submission

### **Week 3: Testing & Monitoring**
- [ ] End-to-end flow test (paper trading)
- [ ] Prometheus metrics collected
- [ ] Jaeger traces flowing
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] Load test (100 events/sec)

### **Week 4: Production Readiness**
- [ ] Canary deployment (5% capital)
- [ ] Monitor for 7 days
- [ ] Full rollout (100%)
- [ ] 24/7 monitoring active
- [ ] Runbook created

---

## 🚀 **DEPLOYMENT TIMELINE**

```
Week 1 (Dec 11-17):
├─ Mon: Architecture finalized
├─ Tue-Wed: Docker images built
├─ Thu-Fri: Local testing
└─ Weekend: Integration debugging

Week 2 (Dec 18-24):
├─ Mon-Tue: Agent event integration
├─ Wed-Thu: Message Bus flow testing
├─ Fri: Staging deployment
└─ Weekend: Paper trading on staging

Week 3 (Dec 25-31):
├─ Mon-Tue: Observability setup
├─ Wed-Thu: Load testing
├─ Fri: Production environment setup
└─ Weekend: Final validation

Week 4 (Jan 1-7):
├─ Mon: Canary deployment (5%)
├─ Tue-Thu: Monitor canary
├─ Fri: Full rollout
└─ Ongoing: 24/7 monitoring
```

---

## 🔥 **GO/NO-GO CRITERIA**

### **STAGE 2A + ApexTrader v4 Live Requirements**

- [ ] Message Bus: > 99% uptime, < 100ms latency
- [ ] DLQ: Capture all failed events, zero loss
- [ ] Tracing: 100% correlation ID propagation
- [ ] Agents: All healthy checks passing
- [ ] Backtest: All strategies positive expectancy
- [ ] Risk: No margin violations over 7-day paper trade
- [ ] Execution: < 5bps average slippage
- [ ] Monitoring: All dashboards live and alerts active

---

**Generated**: 2025-12-11 09:17 MSK  
**Mode**: 🔥 COMBAT DEPLOYMENT  
**Status**: ✅ READY FOR IMMEDIATE ROLLOUT
