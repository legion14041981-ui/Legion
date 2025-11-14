# 🤖 Legion

> **Мультиагентный фреймворк для диспетчеризации и координации виртуального легиона ИИ-агентов**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Supabase](https://img.shields.io/badge/Supabase-Ready-green)](https://supabase.com)

## 📋 Описание

Legion - это современный мультиагентный фреймворк на Python, предназначенный для создания, управления и координации распределённых ИИ-агентов. Проект интегрирован с Supabase для облачного хранения данных и Edge Functions для серверлесс-обработки задач.

### ✨ Ключевые возможности

- 🔄 **Асинхронная обработка задач** - полная поддержка async/await
- 🗄️ **Интеграция с Supabase** - облачная PostgreSQL база данных
- ⚡ **Edge Functions** - серверлесс-обработка через Supabase Functions
- 📊 **Task Queue** - встроенная система управления очередями задач
- 🔍 **Мониторинг агентов** - отслеживание статуса и активности в реальном времени
- 🎯 **Гибкая архитектура** - легко расширяемая система агентов

## 🏗️ Архитектура

```
Legion/
├── src/legion/
│   ├── __init__.py       # Экспорты модулей
│   ├── core.py           # LegionCore - главный координатор
│   ├── agents.py         # Базовый класс LegionAgent
│   ├── database.py       # Интеграция с Supabase
│   └── queue.py          # TaskQueue для управления задачами
├── tests/                # Тесты
├── docs/                 # Документация
├── requirements.txt      # Зависимости
└── .env.example          # Шаблон конфигурации
```

## 🚀 Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# Создать виртуальное окружение (Windows)
python -m venv venv
.\venv\Scripts\Activate

# Установить зависимости
pip install -r requirements.txt
```

### Конфигурация

1. Скопировать `.env.example` в `.env`:

```bash
copy .env.example .env
```

2. Заполнить переменные окружения:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Пример использования

```python
import asyncio
from legion import LegionCore
from legion.queue import TaskQueue

async def main():
    # Инициализация Legion
    core = LegionCore()
    
    # Создание Task Queue
    queue = TaskQueue(core.db)
    
    # Добавление задачи
    task_id = await queue.add_task(
        task_data={'action': 'process_data', 'payload': 'example'},
        agent_id='agent-1'
    )
    
    print(f"Task {task_id} created")
    
    # Запуск обработки очереди
    await queue.start()
    
    # Работа в течение 30 секунд
    await asyncio.sleep(30)
    
    # Остановка
    await queue.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

## 🛠️ Компоненты

### LegionCore

Главный координатор системы, управляет агентами и их жизненным циклом.

```python
from legion import LegionCore, LegionAgent

core = LegionCore()

# Регистрация агента
my_agent = MyCustomAgent()
core.register_agent('agent-1', my_agent)

# Запуск системы
core.start()
```

### LegionAgent

Базовый класс для создания собственных агентов.

```python
from legion import LegionAgent

class MyAgent(LegionAgent):
    async def execute(self, task):
        # Ваша логика обработки
        print(f"Processing task: {task}")
        return {'status': 'completed'}
```

### TaskQueue

Система управления очередями задач с автоматической обработкой.

```python
from legion.queue import TaskQueue

queue = TaskQueue(database)

# Добавить задачу
task_id = await queue.add_task(
    task_data={'type': 'email', 'to': 'user@example.com'},
    agent_id='email-agent'
)

# Получить статистику
stats = queue.get_queue_stats()
print(f"Pending tasks: {stats['pending_count']}")
```

## ☁️ Supabase Integration

### Edge Functions

Проект включает 2 развёрнутые Edge Functions:

#### 1. process-task

Обработка задач (запуск/завершение).

**Endpoint**: `https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/process-task`

**Пример использования**:

```bash
# Запустить задачу
curl -X POST 'https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/process-task' \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "task-123",
    "agent_id": "agent-1",
    "action": "start"
  }'

# Завершить задачу
curl -X POST 'https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/process-task' \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "task-123",
    "agent_id": "agent-1",
    "action": "complete"
  }'
```

#### 2. get-pending-tasks

Получение списка задач в очереди.

**Endpoint**: `https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/get-pending-tasks`

**Пример использования**:

```bash
# Получить все задачи
curl 'https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/get-pending-tasks'

# Фильтр по агенту
curl 'https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/get-pending-tasks?agent_id=agent-1'
```

### База данных

Структура таблиц:

**agents** - информация об агентах
```sql
CREATE TABLE agents (
    id BIGSERIAL PRIMARY KEY,
    agent_id TEXT UNIQUE NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'Not started',
    webhook_url TEXT,
    last_activity TIMESTAMP WITH TIME ZONE,
    error_count INTEGER DEFAULT 0,
    capabilities JSONB,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**tasks** - очередь задач
```sql
CREATE TABLE tasks (
    id BIGSERIAL PRIMARY KEY,
    task_id TEXT UNIQUE NOT NULL,
    agent_id TEXT REFERENCES agents(agent_id),
    task_data JSONB,
    status TEXT DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

## 📦 Зависимости

- `supabase>=2.9.0` - Supabase Python клиент
- `python-dotenv>=1.0.1` - Управление переменными окружения
- `httpx>=0.27.0` - HTTP клиент для async запросов

## 🔧 Разработка

### Запуск тестов

```bash
pytest tests/
```

### Структура проекта

- `src/legion/` - основной код фреймворка
- `tests/` - unit и интеграционные тесты
- `docs/` - документация проекта
- `.github/workflows/` - CI/CD конфигурация

## 🗺️ Roadmap

- [ ] Добавить конкретные реализации агентов (EmailAgent, DataAgent)
- [ ] Интегрировать Supabase Realtime для live-мониторинга
- [ ] Создать веб-интерфейс для управления
- [ ] Добавить систему логирования
- [ ] Интеграция с Google Sheets
- [ ] Webhook система для внешних агентов
- [ ] Метрики и аналитика

## 🤝 Вклад в проект

Вклад приветствуется! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл для деталей.

## 📞 Контакты

- GitHub: [@legion14041981-ui](https://github.com/legion14041981-ui)
- Supabase Project: [LEGION](https://supabase.com/dashboard/project/hdwvhqxyzcgkrkosbuzk)

---

**Legion** - создавайте умных агентов легко 🚀
