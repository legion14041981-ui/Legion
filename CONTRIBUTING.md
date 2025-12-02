# Contributing to Legion Framework

Первое — спасибо за желание внести вклад в Legion! 🎉

## Code of Conduct

Этот проект придерживается [Code of Conduct](CODE_OF_CONDUCT.md). Участвуя, вы соглашаетесь соблюдать его.

## Как я могу помочь?

### Reporting Bugs

Перед созданием bug report:

1. Проверьте [existing issues](https://github.com/legion14041981-ui/Legion/issues)
2. Убедитесь, что используете последнюю версию
3. Соберите информацию о баге

**Создание bug report:**

- Используйте понятный заголовок
- Опишите шаги для воспроизведения
- Укажите ожидаемое и фактическое поведение
- Приложите скриншоты если применимо
- Укажите версию Python и ОС

### Suggesting Enhancements

**Feature requests приветствуются!**

- Используйте понятный заголовок
- Подробно опишите предлагаемую функциональность
- Объясните, зачем она нужна
- Приведите примеры использования

### Pull Requests

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Legion.git
   cd Legion
   ```

2. **Create Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Setup Development Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Make Changes**
   - Следуйте style guide
   - Добавьте тесты
   - Обновите документацию

5. **Run Tests**
   ```bash
   pytest --cov=src/legion
   pylint src/legion
   mypy src/legion
   ```

6. **Commit**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   
   **Commit message format:**
   - `feat:` новая функциональность
   - `fix:` исправление бага
   - `docs:` изменения в документации
   - `test:` добавление тестов
   - `refactor:` рефакторинг кода
   - `style:` форматирование
   - `chore:` обновление зависимостей и т.д.

7. **Push & Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Следуйте **PEP 8**
- Используйте **type hints**
- Добавляйте **docstrings** для всех публичных методов
- Используйте **meaningful names**

```python
def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers to average.
    
    Returns:
        The arithmetic mean of the numbers.
    
    Raises:
        ValueError: If the list is empty.
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

### Testing

- **Все новые функции должны иметь тесты**
- Стремитесь к **80%+ coverage**
- Пишите как **unit**, так и **integration** тесты

```python
def test_calculate_average():
    """Test average calculation."""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0

def test_calculate_average_empty_list():
    """Test average with empty list."""
    with pytest.raises(ValueError):
        calculate_average([])
```

### Documentation

- Обновляйте **README.md** для новых функций
- Добавляйте **docstrings** для всех публичных API
- Обновляйте **CHANGELOG.md**
- Добавляйте примеры использования

## Review Process

1. **Automated Checks**
   - CI pipeline должен пройти
   - Tests должны быть green
   - Coverage не должно упасть

2. **Code Review**
   - Минимум 1 approval
   - Все комментарии должны быть resolved

3. **Merge**
   - Squash commits для чистой истории
   - Delete branch после merge

## Questions?

Не стесняйтесь задавать вопросы через [GitHub Issues](https://github.com/legion14041981-ui/Legion/issues).

## License

Внося вклад, вы соглашаетесь с лицензией проекта [MIT License](LICENSE).
