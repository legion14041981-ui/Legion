# 🛡️ Legion Framework

[![CI Pipeline](https://github.com/legion14041981-ui/Legion/actions/workflows/ci.yml/badge.svg)](https://github.com/legion14041981-ui/Legion/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/legion14041981-ui/Legion/branch/main/graph/badge.svg)](https://codecov.io/gh/legion14041981-ui/Legion)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Legion** — мультиагентный фреймворк для диспетчеризации и координации виртуального легиона ИИ-агентов.

## ✨ Особенности

- 🤖 **Интеллектуальная диспетчеризация задач** с routing на основе capabilities
- ⚡ **Async/await поддержка** для неблокирующего выполнения
- 🔒 **Безопасность** с whitelist validation и защитой от injection
- 📊 **Мониторинг производительности** с автоматическим rollback
- 🔄 **CI/CD integration** с автоматическим тестированием и проверкой качества
- 🐳 **Docker support** для простого развертывания
- 🧪 **80%+ test coverage** для надежности
- 📝 **Comprehensive documentation** и примеры использования

## 🚀 Быстрый старт

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### Базовое использование

```python
from legion.core import LegionCore
from legion.base_agent import LegionAgent

# Создание custom агента
class MyAgent(LegionAgent):
    def execute(self, task_data):
        # Ваша логика
        return {"status": "completed", "result": "success"}

# Инициализация Legion
core = LegionCore()

# Регистрация агента с capabilities
agent = MyAgent("my_agent")
core.register_agent("my_agent", agent, capabilities=["processing", "analysis"])

# Запуск системы
core.start()

# Диспетчеризация задачи
task = {"type": "processing", "data": "sample"}
result = core.dispatch_task("task_1", task, required_capability="processing")

print(result)  # {"status": "completed", "result": "success"}

# Остановка системы
core.stop()
```

## 🐳 Docker

### Быстрый запуск с Docker

```bash
# Сборка образа
docker build -t legion-framework .

# Запуск контейнера
docker run -p 8000:8000 -e LEGION_OS_ENABLED=true legion-framework

# Или с docker-compose
docker-compose up -d
```

### Docker Compose

```yaml
version: '3.8'
services:
  legion:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LEGION_OS_ENABLED=true
      - DATABASE_URL=postgresql://user:pass@db:5432/legion
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=legion
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

## 📁 Структура проекта

```
Legion/
├── src/legion/              # Основной код
│   ├── core.py              # Ядро системы
│   ├── base_agent.py        # Базовый класс агента
│   ├── database.py          # Database integration
│   ├── agents/              # Встроенные агенты
│   │   └── ci_healer/       # CI/CD healing agents
│   ├── neuro_architecture/  # Нейро-архитектура
│   │   ├── registry.py      # Architecture registry
│   │   └── watchdog.py      # Performance monitoring
│   └── orchestration/       # Оркестрация агентов
├── tests/                   # Тесты
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── conftest.py          # Pytest fixtures
├── docs/                    # Документация
├── .github/workflows/       # CI/CD pipelines
├── Dockerfile               # Docker configuration
└── requirements.txt         # Dependencies
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с coverage
pytest --cov=src/legion --cov-report=html

# Запуск только unit tests
pytest tests/unit/

# Запуск только integration tests
pytest tests/integration/
```

## 🔒 Безопасность

- ✅ **Security scanning** с Bandit и Safety
- ✅ **Package whitelist** для безопасной установки зависимостей
- ✅ **Input validation** для всех внешних данных
- ✅ **Dependabot** для автоматического обновления зависимостей

Для сообщения о уязвимостях, см. [SECURITY.md](SECURITY.md)

## 📊 CI/CD

Проект использует GitHub Actions для автоматизации:

- **Тестирование** на Python 3.9, 3.10, 3.11
- **Security scanning** (Bandit, Safety, pip-audit)
- **Code quality** (Ruff, Pylint, MyPy)
- **Coverage reporting** (Codecov)
- **Docker builds** с автоматическим push
- **Automated releases** при создании tags

## 📖 Документация

- [Installation Guide](docs/installation.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api/)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Участие в разработке

Мы приветствуем участие! См. [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

### Быстрый гайд

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Changelog

См. [CHANGELOG.md](CHANGELOG.md) для истории изменений.

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- Все contributors проекта
- Open source community за amazing tools

## 📞 Контакты

- GitHub: [@legion14041981-ui](https://github.com/legion14041981-ui)
- Issues: [GitHub Issues](https://github.com/legion14041981-ui/Legion/issues)

---

**Сделано с ❤️ для AI агентов**
