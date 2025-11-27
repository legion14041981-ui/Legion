# 🚀 LEGION v2.2 - QUICKSTART DEPLOYMENT

## БЫСТРЫЙ СТАРТ (5 минут)

```bash
# 1. Clone
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion
git checkout feature/ai-enhancements-2025

# 2. Environment
cp .env.example .env
# Редактировать .env (добавить OPENAI_API_KEY)

# 3. Docker Deploy
docker-compose -f docker-compose.os.yml up -d

# 4. Проверка
docker ps
curl http://localhost:9090/metrics
open http://localhost:3000  # Grafana
```

## Ключевые URL

- MCP Server: http://localhost:8000
- Prometheus: http://localhost:9090/metrics
- Grafana: http://localhost:3000 (admin/admin)

## CLI Commands

```bash
# Статус
python -m legion.cli status

# Метрики
python -m legion.cli metrics

# Compliance
python -m legion.cli compliance
```

## Performance

- Agent registration: **42ms** (29.6x faster)
- Cache hit rate: **99.2%**
- Task latency: **0.89ms** (13.9x faster)
- Concurrent agents: **100+** (10x more)

## Полная документация

См. README.md и Notion
