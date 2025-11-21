# 📚 Legion AI System v2.0 - Документация

## 📑 Оглавление

1. [Quick Start Guide](AI_ENHANCEMENTS_QUICKSTART.md) - Быстрый старт с v2.0
2. [Архитектура](#архитектура) - Обзор системы
3. [API Reference](#api-reference) - Справочник по API
4. [Примеры](#примеры) - Примеры использования
5. [Развертывание](#развертывание) - Production deployment

## 🏛️ Архитектура

### Общая схема

```
Legion AI System v2.0
│
├── LegionCore (Координатор)
│   ├── Agent Registry
│   ├── Task Queue
│   └── Lifecycle Management
│
├── MCP Layer (Model Context Protocol)
│   ├── MCP Server (FastAPI)
│   ├── Tool Registry (100+ tools)
│   ├── Code Executor (Sandboxed)
│   └── MCP Client (External servers)
│
├── AI Integration
│   ├── Script Generator (GPT-5.1-Codex)
│   ├── Syntax Validator
│   └── Self-Healing Engine
│
├── Multi-Agent Orchestration
│   ├── Planning Agent (Task decomposition)
│   ├── Execution Agent (Browser automation)
│   ├── Monitoring Agent (Error detection)
│   └── Patterns (Sequential/Parallel/Hierarchical/Handoff)
│
├── Browser Automation
│   ├── Playwright Agent
│   ├── Cross-browser (Chromium/Firefox/WebKit)
│   └── Auto-wait & Self-healing
│
└── Supabase Integration
    ├── PostgreSQL Database
    ├── Edge Functions
    └── Realtime subscriptions
```

### Ключевые компоненты

#### 1. **LegionCore** - Главный координатор

- Управление жизненным циклом агентов
- Регистрация и диспетчеризация задач
- Мониторинг состояния системы

#### 2. **MCP Server** - Model Context Protocol

- Стандартизированный протокол AI tool integration
- Совместимость с Claude, GPT, и другими AI
- Async tool execution
- HMAC security

#### 3. **PlaywrightBrowserAgent** - Браузерная автоматизация

- Кросс-браузерная поддержка
- Auto-wait для элементов
- Self-healing при изменении selectors
- Screenshot и PDF generation

#### 4. **ScriptGenerator** - AI-powered генерация кода

- Natural language → Playwright code
- Валидация синтаксиса
- Self-healing script repair
- Context-aware generation

#### 5. **MultiAgentOrchestrator** - Координация агентов

- **PlanningAgent** - Декомпозиция задач
- **ExecutionAgent** - Выполнение автоматизации
- **MonitoringAgent** - Обнаружение ошибок
- 4 паттерна оркестрации

## 📖 API Reference

### LegionAISystem

```python
from src.legion.integration import LegionAISystem

# Инициализация
system = LegionAISystem(
    openai_api_key="your-key",  # Опционально
    mcp_enabled=True,
    browser="chromium"
)

# Выполнение задачи
result = await system.execute_task(
    description="Описание задачи на естественном языке",
    context={"url": "https://example.com"}
)

# Очистка ресурсов
await system.cleanup()
```

### Tool Registry

```python
# Регистрация инструмента
system.tool_registry.register(
    name="custom_action",
    handler=my_function,
    description="Описание",
    input_schema={"param": "string"}
)

# Выполнение
result = await system.tool_registry.execute(
    "custom_action",
    param="value"
)

# Список инструментов
tools = system.tool_registry.list_tools()
```

### Multi-Agent Orchestration

```python
from src.legion.orchestration import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

# Hierarchical pattern
orchestrator.build_hierarchical_workflow(
    root_agent="planning",
    child_agents=["execution", "monitoring"]
)

result = await orchestrator.execute({
    "description": "Задача",
    "context": {}
})
```

## 💻 Примеры

См. [examples/](../examples/) для полных примеров:

- `ai_automation_demo.py` - Основное демо
- Более примеров в README проекта

## 🚀 Развертывание

### Локальная установка

```bash
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion
git checkout feature/ai-enhancements-2025
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
cp .env.example .env
# Редактируйте .env
```

### Docker Deployment

```bash
# В разработке
```

### Production Checklist

- [ ] Конфигурация `.env` с production значениями
- [ ] Supabase database migrations
- [ ] Настройка Prometheus/Grafana
- [ ] Запуск тестов в staging
- [ ] Настройка CI/CD pipeline
- [ ] Мониторинг и алерты

## 🔗 Ссылки

- **Notion Документация**: https://www.notion.so/2ac65511388d815fa690c20766ed1206
- **GitHub Repository**: https://github.com/legion14041981-ui/Legion
- **Supabase Project**: https://supabase.com/dashboard/project/hdwvhqxyzcgkrkosbuzk

## 👥 Контрибьюторы

Вклад приветствуется! См. [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📝 Лицензия

MIT License - см. [LICENSE](../LICENSE)
