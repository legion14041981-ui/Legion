# Staging Deployment Guide

Руководство по развертыванию Legion Framework в staging окружении.

## 🎯 Цели Staging

- Тестирование в production-like окружении
- Проверка интеграций
- Load testing
- Валидация релизов перед production

## 📦 Prerequisites

### System Requirements

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space

### Environment Setup

```bash
# Clone repository
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# Checkout release
git checkout v2.4.0

# Copy environment template
cp .env.example .env.staging

# Edit configuration
nano .env.staging
```

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose -f docker-compose.staging.yml up -d

# View logs
docker-compose logs -f legion

# Check health
curl http://localhost:8000/health
```

### Manual Docker

```bash
# Build image
docker build -t legion:2.4.0-staging .

# Run container
docker run -d \
  --name legion-staging \
  -p 8000:8000 \
  --env-file .env.staging \
  -v $(pwd)/data:/app/data \
  legion:2.4.0-staging

# Check status
docker ps
docker logs legion-staging
```

## 🛠️ Configuration

### docker-compose.staging.yml

```yaml
version: '3.8'

services:
  legion:
    build:
      context: .
      dockerfile: Dockerfile
    image: legion:2.4.0-staging
    container_name: legion-staging
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=staging
      - LEGION_OS_ENABLED=true
      - DATABASE_URL=postgresql://legion:legion@db:5432/legion_staging
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15
    container_name: legion-db-staging
    environment:
      - POSTGRES_DB=legion_staging
      - POSTGRES_USER=legion
      - POSTGRES_PASSWORD=legion_staging_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: legion-redis-staging
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: legion-prometheus-staging
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: legion-grafana-staging
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=staging_admin
      - GF_INSTALL_PLUGINS=
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: legion-staging
```

## 🧪 Тестирование

### Smoke Tests

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# API endpoints
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "data": "smoke test"}'
```

### Load Testing

```bash
# Run benchmark
python scripts/benchmark.py --tasks 10000 --agents 10

# Or use locust
locust -f tests/load/locustfile.py --host http://localhost:8000
```

### Integration Tests

```bash
# Run full test suite against staging
ENVIRONMENT=staging pytest tests/integration/
```

## 📊 Мониторинг

### Access Monitoring

- **Grafana**: http://localhost:3000 (admin/staging_admin)
- **Prometheus**: http://localhost:9090

### Key Metrics

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_failed_total[5m])

# Response time (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active agents
agents_active

# Task queue size
task_queue_size
```

## 🔍 Траблшутинг

### Проверка логов

```bash
# Application logs
docker-compose logs -f legion

# Database logs
docker-compose logs -f db

# All services
docker-compose logs --tail=100
```

### Common Issues

**Database connection failed:**
```bash
# Check database is running
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**High memory usage:**
```bash
# Check container stats
docker stats legion-staging

# Adjust pool size in .env.staging
POOL_SIZE=10
MAX_OVERFLOW=5
```

## 🔄 Update Process

```bash
# Pull latest changes
git pull origin main

# Rebuild image
docker-compose build legion

# Rolling update (zero downtime)
docker-compose up -d --no-deps --build legion

# Verify
curl http://localhost:8000/health
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (CAUTION: deletes data)
docker-compose down -v

# Clean up images
docker image prune -a
```

## ✅ Pre-Production Checklist

Before promoting to production:

- [ ] All smoke tests passing
- [ ] Load tests show acceptable performance
- [ ] No errors in logs during 24h observation
- [ ] Metrics within expected ranges
- [ ] Database migrations tested
- [ ] Rollback procedure documented
- [ ] Monitoring alerts configured
- [ ] Security scan passed
- [ ] Backup/restore tested

## 📞 Support

Для помощи:
- [GitHub Issues](https://github.com/legion14041981-ui/Legion/issues)
- [Documentation](https://github.com/legion14041981-ui/Legion/tree/main/docs)
- [Troubleshooting Guide](troubleshooting.md)
