# Legion Framework Architecture

Полное описание архитектуры Legion Framework.

## 🏛️ Обзор

Legion Framework — это multi-agent orchestration system, построенная на принципах:
- **Intelligent Task Routing** — автоматическое направление задач по capabilities
- **Async-First** — неблокирующее выполнение
- **Resilient** — обработка ошибок и fallback
- **Scalable** — horizontal scaling с connection pooling

## 📦 Компоненты

### 1. LegionCore

**Ответственность:** Центральный оркестратор системы

```python
class LegionCore:
    """Central orchestrator for agent management and task dispatching."""
    
    def register_agent(self, agent_id, agent, capabilities)
    def dispatch_task(self, task_id, task_data, required_capability)
    def dispatch_task_async(self, task_id, task_data, required_capability)
```

**Функции:**
- Регистрация агентов с capabilities
- Intelligent routing задач по capabilities
- Task queue для unmatched задач
- Health monitoring
- Metrics collection

### 2. LegionAgent (Base Class)

**Ответственность:** Базовый класс для всех агентов

```python
class LegionAgent:
    """Base class for all Legion agents."""
    
    def execute(self, task_data) -> Dict[str, Any]
    async def execute_async(self, task_data) -> Dict[str, Any]
    def get_status(self) -> Dict[str, Any]
```

**Функции:**
- Lifecycle management (start/stop)
- Sync/async execution
- Status reporting
- Error handling

### 3. Connection Pool

**Ответственность:** Управление database connections

```python
class ConnectionPool:
    """Thread-safe database connection pool."""
    
    def get_session(self) -> Session
    def health_check(self) -> bool
    def get_metrics(self) -> Dict[str, Any]
```

**Функции:**
- Connection lifecycle management
- Health checking
- Metrics tracking
- Auto-reconnection

### 4. Rate Limiter

**Ответственность:** Ограничение частоты вызовов

```python
class TokenBucketLimiter:
    """Token bucket rate limiter."""
    
    def allow(self) -> bool
    def wait_time(self) -> float
```

**Алгоритмы:**
- Token Bucket
- Sliding Window
- Per-user limits

### 5. Performance Watchdog

**Ответственность:** Мониторинг производительности

```python
class PerformanceWatchdog:
    """Performance monitoring and automatic rollback."""
    
    def track_execution(self, agent_id, duration, memory_used)
    def should_rollback(self, agent_id) -> bool
```

**Функции:**
- Performance tracking
- Automatic rollback
- Memory leak detection
- Circular buffer (deque)

## 🔄 Жизненный цикл задачи

```
1. Клиент → dispatch_task(task_id, task_data, capability)
       ↓
2. LegionCore → поиск агента с capability
       ↓
3a. Agent found → execute(task_data)
       ↓
4a. Result → возврат клиенту

3b. Agent not found → task_queue.append(task)
       ↓
4b. Ожидание регистрации агента
```

## 🔒 Безопасность

### Input Validation

```python
def _validate_task_data(self, task_data: Any) -> None:
    """Validate task data before execution."""
    if not isinstance(task_data, dict):
        raise ValueError("task_data must be dict")
```

### Package Whitelist

```python
ALLOWED_PACKAGES = {
    'pip', 'setuptools', 'wheel',
    # ... trusted packages
}
```

### Subprocess Security

```python
# ✅ SAFE - используем list args
subprocess.run(['pip', 'install', package], check=True)

# ❌ UNSAFE - избегаем shell=True
subprocess.run(f'pip install {package}', shell=True)
```

## ⚡ Производительность

### Async Execution

```python
async def dispatch_task_async(self, task_id, task_data, capability):
    """Non-blocking task dispatch."""
    agent = self._find_agent(capability)
    return await agent.execute_async(task_data)
```

### Connection Pooling

```python
# Повторное использование соединений
with pool.get_session() as session:
    result = session.execute(query)
```

### Rate Limiting

```python
@rate_limit(calls=100, period=60)
def expensive_operation():
    pass
```

## 📊 Мониторинг

### Metrics

```python
metrics = core.get_metrics()
# {
#     'total_agents': 5,
#     'active_agents': 3,
#     'tasks_dispatched': 1250,
#     'tasks_completed': 1200,
#     'tasks_failed': 50
# }
```

### Health Checks

```python
health = core.health_check()
# {
#     'status': 'healthy',
#     'agents': {...},
#     'database': 'connected',
#     'uptime': 3600
# }
```

## 🔧 Развертывание

### Docker

```yaml
services:
  legion:
    image: legion:2.3.0
    environment:
      - DATABASE_URL=postgresql://...
      - POOL_SIZE=20
    depends_on:
      - db
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legion
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: legion
        image: legion:2.3.0
```

## 📚 Дополнительно

- [API Reference](api/)
- [Deployment Guide](deployment.md)
- [Troubleshooting](troubleshooting.md)
- [Security Policy](../SECURITY.md)
