# Troubleshooting Guide

Решение распространенных проблем с Legion Framework.

## 📋 Содержание

- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Database Issues](#database-issues)
- [Common Error Messages](#common-error-messages)

## Installation Issues

### pip install fails

**Problem**: `pip install -r requirements.txt` fails

**Solutions**:

```bash
# 1. Upgrade pip
pip install --upgrade pip

# 2. Use --no-cache-dir
pip install --no-cache-dir -r requirements.txt

# 3. Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev build-essential

# 4. Install system dependencies (macOS)
brew install python@3.11
```

### Module not found error

**Problem**: `ModuleNotFoundError: No module named 'legion'`

**Solution**:

```bash
# Ensure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or install in editable mode
pip install -e .
```

## Runtime Errors

### TaskDispatchError

**Problem**: `TaskDispatchError: No agent found for capability 'X'`

**Solutions**:

1. **Register agent with correct capability**:
```python
core.register_agent('my_agent', agent, capabilities=['X'])
```

2. **Enable task queue**:
```python
core = LegionCore(config={'enable_task_queue': True})
```

3. **Use general capability**:
```python
core.register_agent('my_agent', agent, capabilities=['general'])
```

### AgentNotFoundError

**Problem**: `AgentNotFoundError: Agent 'X' not found`

**Solution**:

```python
# Check registered agents
agents = core.get_all_agents()
print(agents.keys())

# Register missing agent
core.register_agent('X', YourAgent('X'))
```

### Database connection fails

**Problem**: `ConnectionError: Could not connect to database`

**Solutions**:

```bash
# 1. Check DATABASE_URL
echo $DATABASE_URL

# 2. Test connection
psql $DATABASE_URL

# 3. Check database is running
docker-compose ps db

# 4. Check firewall
sudo ufw status
```

## Performance Issues

### High memory usage

**Problem**: Memory usage growing over time

**Solutions**:

1. **Check history size**:
```python
# Limit watchdog history
watchdog = PerformanceWatchdog(max_history_size=500)
```

2. **Enable garbage collection**:
```python
import gc
gc.collect()
```

3. **Monitor with profiler**:
```bash
python -m memory_profiler src/legion/main.py
```

### Slow task execution

**Problem**: Tasks taking too long

**Solutions**:

1. **Use async execution**:
```python
result = await core.dispatch_task_async('task1', data)
```

2. **Check agent load**:
```python
metrics = core.get_metrics()
print(f"Active agents: {metrics['active_agents']}")
```

3. **Profile code**:
```bash
python -m cProfile -o output.prof src/legion/main.py
pytest --profile
```

## Docker Issues

### Container won't start

**Problem**: `docker-compose up` fails

**Solutions**:

```bash
# 1. Check logs
docker-compose logs legion

# 2. Check port conflicts
lsof -i :8000

# 3. Rebuild image
docker-compose build --no-cache legion

# 4. Remove old containers
docker-compose down -v
docker system prune -a
```

### Volume mount issues

**Problem**: Files not syncing between host and container

**Solutions**:

```bash
# 1. Check permissions
ls -la data/

# 2. Fix permissions
sudo chown -R $USER:$USER data/

# 3. Use absolute paths
docker run -v $(pwd)/data:/app/data legion
```

## Database Issues

### Migration fails

**Problem**: Database migration error

**Solutions**:

```bash
# 1. Check current version
psql $DATABASE_URL -c "SELECT version FROM alembic_version;"

# 2. Reset migrations (CAUTION: deletes data)
alembic downgrade base
alembic upgrade head

# 3. Manual migration
psql $DATABASE_URL < migrations/001_initial.sql
```

### Connection pool exhausted

**Problem**: `OperationalError: connection pool exhausted`

**Solution**:

```python
# Increase pool size
DATABASE_CONFIG = {
    'pool_size': 20,
    'max_overflow': 10,
    'pool_timeout': 30
}
```

## Common Error Messages

### "No module named 'legion'"

```bash
# Solution
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### "UnicodeDecodeError in .env file"

```bash
# Solution: convert to UTF-8
iconv -f WINDOWS-1251 -t UTF-8 .env > .env.utf8
mv .env.utf8 .env
```

### "Permission denied"

```bash
# Solution
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

### "Port already in use"

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn legion.main:app --port 8001
```

## Debugging Tips

### Enable debug logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Use pdb debugger

```python
import pdb; pdb.set_trace()
```

### Check system health

```bash
# Check all components
curl http://localhost:8000/health

# Check specific agent
curl http://localhost:8000/agents/my_agent/status

# Check metrics
curl http://localhost:8000/metrics
```

## Getting Help

### Before asking for help

1. Check this troubleshooting guide
2. Search [existing issues](https://github.com/legion14041981-ui/Legion/issues)
3. Enable debug logging
4. Collect relevant information

### Information to provide

- Python version: `python --version`
- Legion version: `pip show legion`
- Operating system
- Error message (full traceback)
- Steps to reproduce
- Configuration (redact secrets)

### Where to ask

- [GitHub Issues](https://github.com/legion14041981-ui/Legion/issues)
- [Discussions](https://github.com/legion14041981-ui/Legion/discussions)

## Still stuck?

If you can't find a solution:

1. Create a [minimal reproducible example](https://stackoverflow.com/help/minimal-reproducible-example)
2. Open a [GitHub Issue](https://github.com/legion14041981-ui/Legion/issues/new)
3. Include all relevant information from "Information to provide" section
