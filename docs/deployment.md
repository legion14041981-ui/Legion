# Deployment Guide

Полное руководство по развертыванию Legion Framework в production.

## 📋 Содержание

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.9+
- Docker 20.10+
- PostgreSQL 13+ (опционально)
- 2GB RAM minimum
- 10GB disk space

### Environment Setup

```bash
# Создать .env файл
cp .env.example .env

# Отредактировать конфигурацию
nano .env
```

**Необходимые переменные:**

```bash
# Core
LEGION_OS_ENABLED=true
DATABASE_URL=postgresql://user:pass@localhost:5432/legion

# API Keys (опционально)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

## Local Development

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests
pytest

# 5. Start application
python -m legion.main
```

### Development Server

```bash
# With auto-reload
uvicorn legion.main:app --reload --port 8000

# Access at http://localhost:8000
```

## Docker Deployment

### Single Container

```bash
# Build image
docker build -t legion-framework:latest .

# Run container
docker run -d \
  --name legion \
  -p 8000:8000 \
  -e LEGION_OS_ENABLED=true \
  -v $(pwd)/data:/app/data \
  legion-framework:latest
```

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  legion:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LEGION_OS_ENABLED=true
      - DATABASE_URL=postgresql://legion:legion@db:5432/legion
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=legion
      - POSTGRES_USER=legion
      - POSTGRES_PASSWORD=legion
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

**Запуск:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f legion

# Stop services
docker-compose down
```

## Production Deployment

### Cloud Platforms

#### AWS ECS

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name legion-framework

# 2. Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t legion-framework .
docker tag legion-framework:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/legion-framework:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/legion-framework:latest

# 3. Create ECS task definition
# See: docs/aws-ecs-task-definition.json

# 4. Create ECS service
aws ecs create-service \
  --cluster legion-cluster \
  --service-name legion-service \
  --task-definition legion-task \
  --desired-count 2
```

#### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: legion
  template:
    metadata:
      labels:
        app: legion
    spec:
      containers:
      - name: legion
        image: ghcr.io/legion14041981-ui/legion:latest
        ports:
        - containerPort: 8000
        env:
        - name: LEGION_OS_ENABLED
          value: "true"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: legion-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

**Deploy:**

```bash
# Apply configuration
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=legion

# View logs
kubectl logs -f deployment/legion
```

## Monitoring

### Prometheus Metrics

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'legion'
    static_configs:
      - targets: ['legion:8000']
```

### Grafana Dashboards

1. Access Grafana: http://localhost:3000
2. Login: admin/admin
3. Add Prometheus datasource
4. Import dashboard from `monitoring/grafana-dashboard.json`

### Health Checks

```bash
# Health endpoint
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

## Troubleshooting

См. [docs/troubleshooting.md](troubleshooting.md) для подробностей.

### Common Issues

**Database connection failed:**
```bash
# Check database is running
docker-compose ps db

# Check logs
docker-compose logs db
```

**Port already in use:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable security scanning
- [ ] Set up monitoring alerts
- [ ] Regular backups configured
- [ ] Update dependencies regularly

## Performance Tuning

### Database

```sql
-- Create indexes
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

### Application

```python
# config.py
CONFIG = {
    'max_workers': 10,
    'connection_pool_size': 20,
    'cache_ttl': 300,
    'task_queue_size': 1000
}
```

## Maintenance

### Backup

```bash
# Database backup
docker-compose exec db pg_dump -U legion legion > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20251202.sql | docker-compose exec -T db psql -U legion legion
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Restart with zero downtime
docker-compose up -d --no-deps --build legion
```

## Support

Для помощи:
- [GitHub Issues](https://github.com/legion14041981-ui/Legion/issues)
- [Documentation](https://github.com/legion14041981-ui/Legion/tree/main/docs)
