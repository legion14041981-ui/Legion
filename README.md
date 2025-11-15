# 🤖 Legion AI v2.0

> **Мультиагентный AI-фреймворк с браузерной автоматизацией и Model Context Protocol**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Supabase](https://img.shields.io/badge/Supabase-Ready-green)](https://supabase.com)
[![AI-Powered](https://img.shields.io/badge/AI-GPT--5.1-orange)](https://openai.com)
[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)

## 🎉 Что нового в v2.0

**Legion v2.0** - революционное обновление с интеграцией передовых AI-технологий 2025 года:

### 🌟 Ключевые новинки

- 🔌 **Model Context Protocol (MCP)** - стандарт интеграции с AI (Claude, GPT, etc.)
- 🌐 **Playwright Automation** - кросс-браузерная автоматизация (Chromium/Firefox/WebKit)
- 🤖 **GPT-5.1-Codex Integration** - генерация скриптов из естественного языка
- 🎭 **Multi-Agent Orchestration** - координация через LangGraph
- 🔄 **Self-Healing** - автоматическое восстановление при ошибках

> 📖 **[Quick Start Guide](docs/AI_ENHANCEMENTS_QUICKSTART.md)** | 📚 **[Full Documentation](https://www.notion.so/2ac65511388d815fa690c20766ed1206)**

---

## 📋 Описание

Legion - это AI-powered мультиагентный фреймворк на Python для создания, управления и координации распределённых ИИ-агентов с возможностями браузерной автоматизации, интеллектуального планирования задач и self-healing.

### ✨ Основные возможности

#### 🆕 Новое в v2.0

- 🔌 **MCP Server** - стандартизированный протокол для AI tool integration
- 🌐 **Browser Automation** - полноценная автоматизация через Playwright
- 🤖 **AI Script Generation** - natural language → Playwright code
- 🎭 **Multi-Agent System** - Planning + Execution + Monitoring agents
- 🔄 **Self-Healing** - AI-powered восстановление при сбоях
- 📊 **Tool Registry** - масштабируется до 100+ инструментов
- 🔐 **Sandboxed Execution** - безопасное выполнение кода

#### Базовые функции

- 🔄 **Асинхронная обработка задач** - полная поддержка async/await
- 🗄️ **Интеграция с Supabase** - облачная PostgreSQL база данных
- ⚡ **Edge Functions** - серверлесс-обработка через Supabase Functions
- 📊 **Task Queue** - встроенная система управления очередями задач
- 🔍 **Мониторинг агентов** - отслеживание статуса и активности в реальном времени
- 🎯 **Гибкая архитектура** - легко расширяемая система агентов

## 🏗️ Архитектура v2.0

```
Legion/
├── src/legion/
│   ├── core.py                  # LegionCore - главный координатор
│   ├── agents.py                # Базовый класс LegionAgent
│   ├── database.py              # Интеграция с Supabase
│   ├── queue.py                 # TaskQueue для управления задачами
│   │
│   ├── mcp/                     # 🆕 Model Context Protocol
│   │   ├── server.py            #     MCP сервер
│   │   ├── client.py            #     MCP клиент
│   │   ├── tools.py             #     Tool registry
│   │   └── executor.py          #     Code execution engine
│   │
│   ├── ai/                      # 🆕 AI Integration
│   │   └── script_generator.py  #     GPT-5.1-Codex генератор
│   │
│   ├── orchestration/           # 🆕 Multi-Agent Orchestration
│   │   ├── orchestrator.py      #     LangGraph orchestrator
│   │   ├── agents.py            #     Specialized agents
│   │   └── patterns.py          #     Execution patterns
│   │
│   ├── agents/                  # Agent implementations
│   │   └── browser_agent.py     # 🆕 Playwright browser agent
│   │
│   └── integration.py           # 🆕 Unified LegionAISystem
│
├── examples/
│   └── ai_automation_demo.py    # 🆕 AI automation demo
├── tests/
│   └── test_integration.py      # 🆕 Integration tests
├── docs/
│   └── AI_ENHANCEMENTS_QUICKSTART.md  # 🆕 Quick start guide
├── requirements.txt             # Dependencies (updated)
└── .env.example                 # Configuration (updated)
```

## 🚀 Быстрый старт

### Вариант 1: Базовая установка (v1.0 функциональность)

```bash
# Клонировать репозиторий
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt
```

### Вариант 2: AI-Enhanced установка (v2.0 функциональность) ⭐

```bash
# Checkout AI enhancements branch
git checkout feature/ai-enhancements-2025

# Установить зависимости
pip install -r requirements.txt

# Установить Playwright browsers
playwright install

# Настроить .env
cp .env.example .env
# Добавить OPENAI_API_KEY в .env

# Запустить demo
python examples/ai_automation_demo.py
```

> 📖 **Полная инструкция**: [AI Enhancements Quick Start](docs/AI_ENHANCEMENTS_QUICKSTART.md)

## 💡 Примеры использования

### Пример 1: Базовая функциональность (v1.0)

```python
import asyncio
from legion import LegionCore
from legion.queue import TaskQueue

async def main():
    core = LegionCore()
    queue = TaskQueue(core.db)
    
    task_id = await queue.add_task(
        task_data={'action': 'process_data', 'payload': 'example'},
        agent_id='agent-1'
    )
    
    await queue.start()
    await asyncio.sleep(30)
    await queue.stop()

asyncio.run(main())
```

### Пример 2: AI-Powered Automation (v2.0) 🆕⭐

```python
import asyncio
from src.legion.integration import LegionAISystem

async def main():
    # Инициализация AI системы
    system = LegionAISystem()
    
    # Выполнение задачи на естественном языке
    result = await system.execute_task(
        description="Перейди на Google и найди 'AI automation'",
        context={'url': 'https://google.com'}
    )
    
    print(f"Результат: {result}")
    
    await system.cleanup()

asyncio.run(main())
```

### Пример 3: MCP Tools (v2.0) 🆕

```python
from src.legion.integration import LegionAISystem

system = LegionAISystem()

# Список доступных инструментов
tools = system.tool_registry.list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# Прямое выполнение инструмента
result = await system.tool_registry.execute(
    'browser_navigate',
    url='https://example.com'
)
```

### Пример 4: Multi-Agent Orchestration (v2.0) 🆕

```python
from src.legion.orchestration import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

# Hierarchical pattern: Planning Agent → Execution Agent
orchestrator.register_agent('planning', planning_agent, 'planning')
orchestrator.register_agent('execution', exec_agent, 'execution')
orchestrator.build_hierarchical_workflow('planning', ['execution'])

result = await orchestrator.execute({
    'description': 'Сложная многошаговая задача',
    'url': 'https://example.com'
})
```

## 🛠️ Компоненты

### Базовые компоненты (v1.0)

#### LegionCore

Главный координатор системы, управляет агентами и их жизненным циклом.

#### LegionAgent

Базовый класс для создания собственных агентов.

#### TaskQueue

Система управления очередями задач с автоматической обработкой.

### Новые компоненты (v2.0) 🆕

#### LegionAISystem

Унифицированная AI-система, объединяющая все компоненты:

- MCP Server для tool integration
- AI Script Generator для генерации кода
- Browser Agent для автоматизации
- Orchestrator для координации

#### MCP Server

Model Context Protocol сервер для стандартизированной интеграции с AI:

- Tool registration & discovery
- Async tool execution
- Resource management
- HMAC security

#### PlaywrightBrowserAgent

Кросс-браузерный агент автоматизации:

- Chromium, Firefox, WebKit support
- Auto-wait for elements
- Screenshot & PDF generation
- Self-healing on selector changes

#### ScriptGenerator

AI-powered генератор Playwright скриптов:

- Natural language → code
- Syntax validation
- Self-healing script repair
- Context-aware generation

#### MultiAgentOrchestrator

Координатор множественных агентов:

- **PlanningAgent** - декомпозиция задач
- **ExecutionAgent** - выполнение браузерной автоматизации
- **MonitoringAgent** - обнаружение ошибок и восстановление
- 4 паттерна оркестрации (Sequential, Parallel, Hierarchical, Handoff)

## ☁️ Supabase Integration

### Edge Functions

Проект включает 2 развёрнутые Edge Functions:

1. **process-task** - Обработка задач (запуск/завершение)
2. **get-pending-tasks** - Получение списка задач в очереди

**Базовый URL**: `https://hdwvhqxyzcgkrkosbuzk.supabase.co/functions/v1/`

### База данных

- **agents** - информация об агентах
- **tasks** - очередь задач
- **mcp_sessions** 🆕 - логи MCP вызовов
- **legion_memory** - долгосрочная память агентов

## 📦 Зависимости

### Базовые (v1.0)

- `supabase>=2.9.0`
- `python-dotenv>=1.0.1`
- `httpx>=0.27.0`
- Google Sheets integration packages

### AI Enhancements (v2.0) 🆕

- `playwright==1.45.0` - браузерная автоматизация
- `openai>=1.0.0` - GPT-5.1-Codex
- `langgraph>=0.1.0` - multi-agent orchestration
- `fastapi==0.104.1` - MCP server
- `pytest-playwright>=0.4.0` - тестирование
- `restrictedpython>=6.2` - безопасное выполнение кода

## 🔧 Разработка

### Запуск тестов

```bash
# Базовые тесты
pytest tests/

# AI integration тесты (требует OPENAI_API_KEY)
pytest tests/test_integration.py -v
```

### Запуск демо

```bash
# AI automation demo
python examples/ai_automation_demo.py
```

## 🗺️ Roadmap

### v1.0 (Завершено)

- [x] Базовая координация агентов
- [x] Supabase integration
- [x] Task Queue
- [x] Google Sheets integration
- [x] Логирование
- [x] Edge Functions

### v2.0 (Завершено) 🆕

- [x] Model Context Protocol
- [x] Playwright browser automation
- [x] GPT-5.1-Codex integration
- [x] Multi-agent orchestration
- [x] Self-healing capabilities
- [x] AI script generation

### v3.0 (В разработке)

- [ ] Supabase Realtime для live-мониторинга
- [ ] Веб-интерфейс для управления
- [ ] Webhook система для внешних агентов
- [ ] Edge AI integration (ONNX Runtime)
- [ ] Prometheus/Grafana мониторинг
- [ ] Quantum-ready interfaces
- [ ] Advanced self-healing with pattern recognition

## 📚 Документация

- **[Quick Start Guide](docs/AI_ENHANCEMENTS_QUICKSTART.md)** - быстрый старт с v2.0
- **[Notion Documentation](https://www.notion.so/2ac65511388d815fa690c20766ed1206)** - полная документация
- **[Pull Request #1](https://github.com/legion14041981-ui/Legion/pull/1)** - детали AI enhancements
- **API Documentation** - генерируется через `system.tool_registry.generate_api_documentation()`

## 🤝 Вклад в проект

Вклад приветствуется! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License - см. LICENSE файл для деталей.

## 📞 Контакты

- **GitHub**: [@legion14041981-ui](https://github.com/legion14041981-ui)
- **Repository**: [Legion](https://github.com/legion14041981-ui/Legion)
- **Supabase Project**: [hdwvhqxyzcgkrkosbuzk](https://supabase.com/dashboard/project/hdwvhqxyzcgkrkosbuzk)
- **Documentation**: [Notion](https://www.notion.so/2ac65511388d815fa690c20766ed1206)

## 🏆 Credits

Legion v2.0 built with cutting-edge technologies from November 2025:

- **OpenAI GPT-5.1** (released Nov 12, 2025)
- **Anthropic MCP** (Model Context Protocol, Nov 2025)
- **Playwright** (cross-browser automation standard)
- **LangGraph** (Microsoft multi-agent framework)
- **Google Willow** (quantum computing inspiration)

---

**Legion v2.0** - AI-powered automation легко 🚀🤖