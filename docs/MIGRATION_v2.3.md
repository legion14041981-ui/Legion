# Legion v2.3 - Руководство по миграции

## 📋 Обзор изменений

Версия 2.3 включает критические исправления и улучшения архитектуры:

### ✅ Исправленные проблемы

1. **Опечатки в документации** (`core.py`)
   - "руковиндица" → "руководящая"
   - "Обиче инициализации" → "Объект инициализации"

2. **Отсутствие async/await поддержки**
   - Добавлены async методы для всех операций
   - Неблокирующая регистрация агентов

3. **Слабая обработка ошибок БД**
   - Retry механизм с exponential backoff
   - Автоматический reconnect

4. **Отсутствие timeout**
   - Timeout для всех async операций
   - Конфигурируемые таймауты

5. **Отсутствие graceful shutdown**
   - Корректная остановка всех агентов
   - Управление shutdown events

---

## 🎉 Новые возможности

### 1. Async-First Architecture

```python
import asyncio
from legion.core import LegionCore

async def main():
    core = LegionCore()
    
    # Async регистрация агентов
    await core.register_agent_async("agent1", agent1)
    await core.register_agent_async("agent2", agent2)
    
    # Async запуск
    await core.start_async()
    
    # Ваша логика
    
    # Graceful shutdown
    await core.stop_async()

asyncio.run(main())
```

### 2. Circuit Breaker Pattern

Защита от cascading failures:

```python
from legion.utils import circuit_breaker

@circuit_breaker(failure_threshold=5, timeout=60)
async def risky_operation():
    """
    При 5 неудачных попытках подряд,
    circuit breaker откроется на 60 секунд.
    """
    # Ваш код
    pass
```

### 3. Retry Mechanism

Автоматический retry с exponential backoff:

```python
from legion.utils import retry

@retry(max_attempts=3, delay=2.0, backoff=2.0)
async def fetch_data():
    """
    Попытки: 1, 2, 3
    Задержки: 2s, 4s, 8s
    """
    # Ваш код
    pass
```

### 4. Health Checks & Metrics

```python
core = LegionCore()

# Health status
health = core.get_health()
print(health)
# {
#   "status": "running",
#   "timestamp": "2025-11-26T01:00:00",
#   "agents_count": 5,
#   "metrics": {
#     "agents_registered": 5,
#     "tasks_dispatched": 100,
#     "errors": 2
#   }
# }

# Metrics
metrics = core.get_metrics()
print(metrics)
# {
#   "agents_registered": 5,
#   "tasks_dispatched": 100,
#   "errors": 2
# }
```

### 5. Agent-level Metrics

```python
agent = MyAgent("my_agent")

# Выполнение с timeout и retry
result = await agent.execute_async(
    task_data,
    timeout=30.0,
    max_retries=3
)

# Получить метрики
status = agent.get_status()
print(status)
# {
#   "agent_id": "my_agent",
#   "is_active": true,
#   "circuit_breaker": {
#     "state": "closed",
#     "failures": 0
#   },
#   "metrics": {
#     "executions": 50,
#     "successes": 48,
#     "failures": 2,
#     "avg_duration": 1.5
#   }
# }
```

---

## 🔄 Миграция существующего кода

### Шаг 1: Обновить инициализацию

**До (v2.2):**
```python
from legion.core import LegionCore

core = LegionCore()
core.register_agent("agent1", agent1)
core.start()

# Ваш код

core.stop()
```

**После (v2.3):**
```python
import asyncio
from legion.core import LegionCore

async def main():
    core = LegionCore()
    await core.register_agent_async("agent1", agent1)
    await core.start_async()
    
    # Ваш код
    
    await core.stop_async()

asyncio.run(main())
```

### Шаг 2: Добавить обработку ошибок

**До:**
```python
class MyAgent(LegionAgent):
    def execute(self, task_data):
        # Простой код без обработки ошибок
        return process(task_data)
```

**После:**
```python
from legion.agents import LegionAgent
from legion.utils import retry, circuit_breaker

class MyAgent(LegionAgent):
    def execute(self, task_data):
        # Legacy метод (deprecated)
        return process(task_data)
    
    @retry(max_attempts=3, delay=1.0)
    @circuit_breaker(failure_threshold=5, timeout=60)
    async def _execute_native_async(self, task_data):
        """Новый async метод с retry и circuit breaker."""
        result = await process_async(task_data)
        return result
```

### Шаг 3: Настроить конфигурацию

```python
agent = MyAgent(
    agent_id="my_agent",
    config={
        "timeout": 30.0,  # Timeout для операций
        "circuit_breaker_threshold": 5,  # Порог для circuit breaker
        "circuit_breaker_timeout": 60  # Таймаут circuit breaker
    }
)
```

---

## ⚠️ Breaking Changes

### Deprecated методы

Следующие методы помечены как deprecated, но продолжают работать:

- `register_agent()` → используйте `register_agent_async()`
- `start()` → используйте `start_async()`
- `stop()` → используйте `stop_async()`

При использовании deprecated методов будет выведено предупреждение в логи.

### Новые зависимости

Убедитесь, что установлены все зависимости:

```bash
pip install -r requirements.txt
```

---

## 🧪 Тестирование после миграции

### Базовая проверка

```python
import asyncio
from legion.core import LegionCore
from legion.agents import LegionAgent

class TestAgent(LegionAgent):
    def execute(self, task_data):
        return {"status": "ok"}
    
    async def _execute_native_async(self, task_data):
        await asyncio.sleep(0.1)
        return {"status": "ok"}

async def test():
    # Создать core
    core = LegionCore()
    
    # Зарегистрировать агента
    agent = TestAgent("test_agent")
    success = await core.register_agent_async("test_agent", agent)
    assert success, "Registration failed"
    
    # Запустить
    await core.start_async()
    
    # Проверить health
    health = core.get_health()
    assert health["status"] == "running"
    assert health["agents_count"] == 1
    
    # Выполнить задачу
    result = await agent.execute_async({"test": "data"}, timeout=5.0)
    assert result["status"] == "ok"
    
    # Остановить
    await core.stop_async()
    
    # Проверить состояние
    health = core.get_health()
    assert health["status"] == "stopped"
    
    print("✅ Все тесты пройдены!")

asyncio.run(test())
```

### Проверка Circuit Breaker

```python
from legion.utils import CircuitBreaker

async def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=3, timeout=1)
    
    # Имитация ошибок
    async def failing_func():
        raise Exception("Test error")
    
    # Вызвать 3 раза (порог)
    for i in range(3):
        try:
            await cb.call_async(failing_func)
        except Exception:
            pass
    
    # Circuit breaker должен быть открыт
    state = cb.get_state()
    assert state["state"] == "open"
    print("✅ Circuit breaker работает корректно!")

asyncio.run(test_circuit_breaker())
```

### Проверка Retry

```python
from legion.utils import retry

async def test_retry():
    attempts = []
    
    @retry(max_attempts=3, delay=0.1, backoff=2.0)
    async def flaky_function():
        attempts.append(1)
        if len(attempts) < 3:
            raise Exception("Not yet")
        return "success"
    
    result = await flaky_function()
    assert result == "success"
    assert len(attempts) == 3
    print("✅ Retry работает корректно!")

asyncio.run(test_retry())
```

---

## 📊 Мониторинг

### Интеграция с Prometheus

```python
from legion.monitoring import LegionPrometheusExporter

async def setup_monitoring():
    core = LegionCore()
    
    # Запустить Prometheus exporter
    exporter = LegionPrometheusExporter(core, port=8000)
    await exporter.start()
    
    # Метрики доступны на http://localhost:8000/metrics
```

### Логирование

Включить debug логирование:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

---

## 🐛 Troubleshooting

### Проблема: Circuit breaker постоянно открыт

**Причина:** Слишком низкий threshold или повторяющиеся ошибки.

**Решение:**
```python
# Увеличить threshold
agent.config["circuit_breaker_threshold"] = 10

# Или проверить логи
status = agent.get_status()
print(status["circuit_breaker"])
```

### Проблема: Timeout при выполнении

**Причина:** Задача выполняется дольше timeout.

**Решение:**
```python
# Увеличить timeout
result = await agent.execute_async(
    task_data,
    timeout=60.0  # Увеличено до 60 секунд
)
```

### Проблема: Database connection errors

**Причина:** Проблемы с подключением к Supabase.

**Решение:**
```python
# Проверить .env файл
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

# Проверить логи
logger.setLevel(logging.DEBUG)
```

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи с уровнем DEBUG
2. Проверьте метрики через `get_health()` и `get_status()`
3. Откройте issue на GitHub с:
   - Версией Legion
   - Полным stack trace
   - Минимальным воспроизводимым примером

---

## 🚀 Что дальше?

Следующие улучшения (v2.4+):

- [ ] Distributed agent coordination
- [ ] Advanced monitoring dashboard
- [ ] Auto-scaling agents
- [ ] Multi-region support
- [ ] Enhanced AI integration

---

**Версия документа:** 2.3.0  
**Дата обновления:** 26.11.2025
