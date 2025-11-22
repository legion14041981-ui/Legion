# 🚀 Legion AI System - Quick Start Guide

**Get started with Legion in 5 minutes!**

---

## 🐳 Option 1: Docker (Recommended)

**Fastest way to run Legion with all services**

### Prerequisites
- Docker 24.0+
- Docker Compose 2.20+
- 4GB RAM minimum

### Steps

```bash
# 1. Clone repository
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# 2. Create .env file
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY=your-key-here
# - SUPABASE_URL=your-url
# - SUPABASE_KEY=your-key

# 3. Start all services (ONE COMMAND!)
docker-compose up -d

# 4. Verify services
curl http://localhost:8001/health  # MCP Server
curl http://localhost:9090/metrics # Prometheus
open http://localhost:3000         # Grafana (admin/legion)
```

**That's it!** Legion is running.

---

## 🐍 Option 2: Python Local Setup

**For development and customization**

### Prerequisites
- Python 3.9, 3.10, or 3.11
- pip 23.0+
- 2GB RAM minimum

### Steps

```bash
# 1. Clone repository
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# 3. Quick install (ONE COMMAND!)
make install-dev

# OR manual install
pip install -r requirements.txt
playwright install chromium
pre-commit install

# 4. Configure
cp .env.example .env
# Edit .env with your API keys

# 5. Run Legion
python -m src.main
```

---

## ✅ Verification

### Test MCP Server

```bash
curl http://localhost:8001/tools
# Should return list of available tools
```

### Test Browser Automation

```python
python examples/ai_automation_demo.py
```

### Run Tests

```bash
make test
# OR
pytest tests/ -v
```

---

## 📚 Common Use Cases

### 1. Natural Language Browser Automation

```python
from src.legion.integration import LegionAISystem
import asyncio

async def main():
    system = LegionAISystem()
    
    # Natural language task
    result = await system.execute_task(
        "Перейди на Google и найди 'AI automation'",
        context={'url': 'https://google.com'}
    )
    
    print(result)
    await system.cleanup()

asyncio.run(main())
```

### 2. Using MCP Tools Directly

```python
from src.legion.mcp.tools import LegionToolRegistry

registry = LegionToolRegistry()

# List available tools
tools = registry.list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# Execute a tool
result = await registry.execute(
    'browser_navigate',
    url='https://example.com'
)
```

### 3. Multi-Agent Orchestration

```python
from src.legion.orchestration import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

# Execute with Planning → Execution → Monitoring
result = await orchestrator.execute({
    'description': 'Сложная многошаговая задача',
    'url': 'https://example.com'
})
```

---

## 🛠️ Development Commands

### Using Makefile (Recommended)

```bash
make help              # Show all commands
make install-dev       # Install dev dependencies
make lint              # Run linters
make format            # Auto-format code
make test              # Run tests with coverage
make docker-build      # Build Docker image
make docker-compose-up # Start all services
make clean             # Remove cache/artifacts
```

### Manual Commands

```bash
# Linting
ruff check src/ tests/
mypy src/legion
bandit -r src/

# Formatting
black src/ tests/

# Testing
pytest tests/ -v --cov=src/legion

# Docker
docker build -t legion:2.0 .
docker run -d -p 8001:8001 legion:2.0
```

---

## 🐞 Troubleshooting

### Issue: "playwright not found"

```bash
pip install playwright
playwright install chromium
```

### Issue: "OPENAI_API_KEY not set"

```bash
# Add to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Issue: "Port 8001 already in use"

```bash
# Change port in .env
MCP_SERVER_PORT=8002

# Or kill existing process
lsof -ti:8001 | xargs kill -9
```

### Issue: Docker "no space left"

```bash
# Clean Docker system
docker system prune -a --volumes
```

### Issue: Import errors

```bash
# Reinstall in development mode
pip install -e .

# OR ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

---

## 📚 Next Steps

1. **Read Full Documentation**: [Notion](https://www.notion.so/2ac65511388d815fa690c20766ed1206)
2. **Check Examples**: `examples/ai_automation_demo.py`
3. **Explore Tools**: http://localhost:8001/tools
4. **View Metrics**: http://localhost:9090/metrics
5. **See Dashboards**: http://localhost:3000 (Grafana)

---

## 🔗 Useful Links

- **GitHub**: https://github.com/legion14041981-ui/Legion
- **Documentation**: https://www.notion.so/2ac65511388d815fa690c20766ed1206
- **Issues**: https://github.com/legion14041981-ui/Legion/issues
- **Supabase**: https://supabase.com/dashboard/project/hdwvhqxyzcgkrkosbuzk

---

## ❓ Getting Help

- **Discord**: Join our community (coming soon)
- **Issues**: [GitHub Issues](https://github.com/legion14041981-ui/Legion/issues)
- **Email**: legion14041981@gmail.com

---

**Happy Automating!** 🤖🚀
