# 🤝 Contributing to Legion AI System

Спасибо за интерес к Legion! Мы рады любому вкладу.

## 📄 Code of Conduct

Участвуя в проекте, вы принимаете наш Кодекс поведения:

- Будьте дружелюбны и уважительны
- Принимайте конструктивную критику
- Фокусируйтесь на решении проблем

## 🚀 How to Contribute

### Reporting Bugs

Если вы нашли ошибку:

1. Проверьте [Issues](https://github.com/legion14041981-ui/Legion/issues)
2. Создайте новый issue с лейблом `bug`
3. Укажите:
   - Описание проблемы
   - Шаги воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение
   - Версию Python, OS

### Suggesting Features

1. Проверьте [Issues](https://github.com/legion14041981-ui/Legion/issues)
2. Создайте issue с лейблом `enhancement`
3. Опишите:
   - Use case
   - Предлагаемое решение
   - Альтернативы

### Pull Requests

#### Процесс

1. **Fork репозитория**

```bash
git clone https://github.com/YOUR-USERNAME/Legion.git
cd Legion
git remote add upstream https://github.com/legion14041981-ui/Legion.git
```

2. **Создайте ветку**

```bash
git checkout -b feature/amazing-feature
# или
git checkout -b fix/critical-bug
```

3. **Установите зависимости**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
pip install -e .[dev]
playwright install
```

4. **Внесите изменения**

- Следуйте [PEP 8](https://pep8.org/)
- Используйте type hints
- Добавьте docstrings
- Напишите тесты

5. **Запустите тесты**

```bash
pytest tests/ -v
black src/ tests/
flake8 src/ tests/
mypy src/
```

6. **Commit изменения**

```bash
git add .
git commit -m "feat: add amazing feature"
```

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - новая функциональность
- `fix:` - исправление ошибки
- `docs:` - документация
- `test:` - тесты
- `refactor:` - рефакторинг
- `chore:` - обслуживание

7. **Push изменения**

```bash
git push origin feature/amazing-feature
```

8. **Создайте Pull Request**

- Опишите изменения
- Ссылка на связанные issues
- Добавьте скриншоты (если нужно)

## 📑 Development Guidelines

### Code Style

```python
# ✅ Good
def calculate_sum(numbers: list[int]) -> int:
    """
    Calculate sum of numbers.
    
    Args:
        numbers: List of integers
        
    Returns:
        Sum of all numbers
    """
    return sum(numbers)

# ❌ Bad
def calc(n):
    return sum(n)
```

### Testing

- Пишите unit tests для нового кода
- Integration tests для API
- Используйте pytest markers:

```python
import pytest

@pytest.mark.unit
def test_basic_function():
    assert True

@pytest.mark.integration
@pytest.mark.playwright
async def test_browser_automation():
    # ...
```

### Documentation

- Docstrings для всех публичных функций/классов
- Обновляйте README.md и docs/
- Примеры в examples/

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Пример:

```
feat(mcp): add tool registry auto-discovery

Implemented automatic discovery of MCP tools from
registered plugins. Supports both sync and async handlers.

Closes #123
```

## 📚 Project Structure

```
Legion/
├── src/legion/          # Основной код
├── tests/              # Тесты
├── docs/               # Документация
├── examples/           # Примеры
└── .github/workflows/  # CI/CD
```

## ❓ Questions?

- Откройте [Discussion](https://github.com/legion14041981-ui/Legion/discussions)
- Посмотрите [Documentation](https://www.notion.so/2ac65511388d815fa690c20766ed1206)

## 🚀 Release Process

1. Update version in `src/legion/__init__.py`
2. Update CHANGELOG.md
3. Create PR to `main`
4. After merge, create release tag
5. GitHub Actions автоматически деплоит

---

**Спасибо за ваш вклад!** 🚀
