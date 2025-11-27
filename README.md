## 🤖 CI-Healer Agent (v2.0)

Автономный агент для автоматического исправления CI/CD ошибок в Legion AI System.

### Возможности
- Обработка CI ошибок, компиляции, тестов, импортов, merge conflict
- AST-based патчинг для точечных минимальных исправлений
- Multi-error detection: SyntaxError, ModuleNotFoundError, TypeError, ImportError, тесты, конфликты
- Оценка риска патчей (4 уровня)
- Авто-фикс зависимостей (pip/npm) через DependencyDoctor
- Semantic file indexing для поиска релевантного кода
- Телеметрия: интеграция с Slack и S3
- Полная интеграция с GitHub Actions

### Интеграция и настройка

1. **Добавьте секреты в GitHub Actions:**
   ```bash
   gh secret set SLACK_WEBHOOK -b "https://hooks.slack.com/..."
   gh secret set AWS_ACCESS_KEY_ID -b "..."
   gh secret set AWS_SECRET_ACCESS_KEY -b "..."
   ```
2. **Workflow-файл** расположен по пути `.github/workflows/ci-healer.yml`.
3. **Unit-тесты** — `tests/agents/test_ci_healer_agent.py`
4. Все действия и патчи фиксируются через PR после каждого успешного run.

### Пример запуска агента
```python
from legion.agents.ci_healer_agent import CIHealerAgent

def main():
    agent = CIHealerAgent(max_loops=10, risk_limit=1)
    webhook = {"workflow_run": {"conclusion": "failure"}, "repository": {"full_name": "your/repo"}}
    result = agent.handle_webhook(webhook)
    print(result.to_json())

if __name__ == "__main__":
    main()
```

### Быстрый старт для CI-Healer
- Ветка разработки: `feature/ai-enhancements-2025`
- Автоматический запуск CI-Healer при ошибке CI/CD
- Используйте dry-run/production режим для безопасного внедрения
- Все логи и отчёты можно просматривать через Slack или S3

----
**Legion v2.0 с CI-Healer Agent** — теперь CI/CD чинится полностью автономно!
