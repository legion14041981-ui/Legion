# 🚀 GRAIL AGENT PRODUCTION DEPLOYMENT CHECKLIST

## ✅ ШАГИ ДЕПЛОЯ

### Шаг 1: Supabase Setup
- [ ] Создать проект Supabase
- [ ] Настроить таблицы: `predictions`, `trades`, `performance_metrics`
- [ ] Добавить RLS (Row Level Security) policies
- [ ] Сохранить URL и API KEY в `.env`

### Шаг 2: Local Setup (ПРОПУЩЕН)
*По вашему запросу этот шаг пропускаем*

### Шаг 3: Production Agent
- [ ] Создать `grail_agent_production.py`
- [ ] Добавить logging в Supabase
- [ ] Настроить error recovery и safety limits
- [ ] Интегрировать с Walbi API

### Шаг 4: Playwright Parser
- [ ] Создать `walbi_parser.py` с Playwright
- [ ] Настроить антидетект (user agent, viewport)
- [ ] Автоматизировать сбор ставок и рыночных данных
- [ ] Сохранять результаты в Supabase

### Шаг 5: GitHub Actions Workflow
- [ ] Создать `.github/workflows/grail_agent_deploy.yml`
- [ ] Настроить автозапуск по расписанию (cron)
- [ ] Добавить ручной триггер (workflow_dispatch)
- [ ] Интегрировать отчеты (Slack/Notion)

### Шаг 6: Проверка деплоя
- [ ] Запустить в demo режиме: `python grail_agent_production.py --mode demo --bankroll 100 --num-predictions 10`
- [ ] Проверить логи в Supabase
- [ ] Верифицировать connection к Walbi
- [ ] Переключиться на LIVE режим после успешных тестов

---

## 📋 ТРЕБОВАНИЯ

### Зависимости Python:
```bash
pip install playwright python-dotenv supabase-py requests
playwright install chromium
```

### Переменные окружения (.env):
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
WALBI_API_KEY=your_walbi_api_key  # если требуется
USER_EMAIL=your_email_for_logging
```

---

## 🎯 ФИНАЛЬНЫЙ ЗАПУСК

```bash
# Demo режим (виртуальные ставки)
python grail_agent_production.py --mode demo --bankroll 100 --num-predictions 10

# Production режим (реальные ставки)
python grail_agent_production.py --mode live --bankroll 1000 --num-predictions 50
```

---

## 📊 МОНИТОРИНГ

- **Supabase Dashboard**: Проверка логов и метрик
- **GitHub Actions**: Автозапуск и отчеты
- **Walbi Dashboard**: Реальные результаты ставок

---

**Статус**: ✅ Готов к запуску после выполнения всех шагов!
