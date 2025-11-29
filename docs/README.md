# 🌟 Legion AI System v2.0 - Документация

## 📑 Оглавление

1. [Быстрый старт](#быстрый-старт) - Начало работы с v2.0
2. [Архитектура](#архитектура) - Обзор системы
3. [API Reference](#api-reference) - Справочник по API
4. [Примеры](#примеры) - Примеры использования
5. [Развертывание](#развертывание) - Production deployment

## 🏗️ Архитектура

### Общая схема

```
┌─────────────────┐
│  LegionAISystem │
└────────┬────────┘
        │
┌───────┼───────┐
│       │       │
▼       ▼       ▼
 MCP   AI    Browser
Server Script Automation
```

### Компоненты

- **LegionCore** - Ядро системы
- **MCP Server** - Model Context Protocol сервер
- **Orchestrator** - Оркестрация агентов
- **Browser Agent** - Playwright автоматизация

## 🚀 Быстрый старт

### Установка

```bash
pip install legion-ai
```

### Использование

```python
from legion import LegionAISystem

async def main():
    system = LegionAISystem()
    result = await system.execute_task("Анализ данных")
    print(result)
```

## 📚 API Reference

### LegionAISystem

```python
class LegionAISystem:
    async def execute_task(description: str, context: Optional[Dict] = None) -> Dict
    async def generate_script(prompt: str, language: str = "python") -> Dict
    async def browse(url: str, actions: Optional[list] = None) -> Dict
    async def cleanup() -> None
```

## 📦 Примеры

Смотрите директорию `examples/` для примеров использования.

## 🛠️ Развертывание

### Docker

```bash
docker-compose up -d
```

### Переменные окружения

| Переменная | Описание | По умолчанию |
|----------|----------|------------|
| LOG_LEVEL | Уровень логирования | INFO |
| MCP_SERVER_PORT | Порт MCP сервера | 8001 |
