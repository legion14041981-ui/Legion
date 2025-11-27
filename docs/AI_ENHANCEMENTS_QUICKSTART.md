# Legion AI Enhancements v2.0 - Quick Start Guide

## 🚀 Overview

Legion v2.0 transforms the framework into an AI-powered automation system with:

- **MCP Protocol** - Industry standard for AI tool integration
- **Playwright** - Cross-browser automation with self-healing
- **GPT-5.1-Codex** - Natural language → automation scripts
- **Multi-Agent Orchestration** - Intelligent task coordination

## ⚡ Quick Start (5 minutes)

<<<<<<< HEAD
### 1. Clone & Checkout

```bash
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion
git checkout feature/ai-enhancements-2025
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 3. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your keys:
# OPENAI_API_KEY=sk-...
# SUPABASE_URL=https://...
# SUPABASE_KEY=...
```

### 4. Run Demo

```bash
python examples/ai_automation_demo.py
```

## 💻 Basic Usage

### Example 1: Simple Automation

```python
import asyncio
from src.legion.integration import LegionAISystem

async def main():
    # Initialize system
    system = LegionAISystem()
    
    # Execute task in natural language
    result = await system.execute_task(
        description="Navigate to Google and search for 'AI automation'",
        context={'url': 'https://google.com'}
    )
    
    print(f"Result: {result}")
    
    # Cleanup
    await system.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
```

### Example 2: Using MCP Tools

```python
from src.legion.integration import LegionAISystem

system = LegionAISystem()

# List available tools
tools = system.tool_registry.list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# Execute tool directly
result = await system.tool_registry.execute(
    'browser_navigate',
    url='https://example.com'
)
```

### Example 3: Multi-Agent Workflow

```python
from src.legion.orchestration import MultiAgentOrchestrator
from src.legion.orchestration.agents import PlanningAgent, ExecutionAgent

# Create orchestrator
orchestrator = MultiAgentOrchestrator()

# Register agents
orchestrator.register_agent('planning', PlanningAgent(script_gen), 'planning')
orchestrator.register_agent('execution', ExecutionAgent(browser_agent), 'execution')

# Build workflow
orchestrator.build_sequential_workflow(['planning', 'execution'])
orchestrator.compile()

# Execute
result = await orchestrator.execute({
    'description': 'Automate multi-step workflow',
    'url': 'https://example.com'
})
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-5.1 | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4-turbo` |
| `MCP_ENABLED` | Enable MCP server | `true` |
| `MCP_SERVER_PORT` | MCP server port | `8001` |
| `PLAYWRIGHT_BROWSER` | Browser to use | `chromium` |
| `PLAYWRIGHT_HEADLESS` | Run headless | `true` |
| `ORCHESTRATION_PATTERN` | Pattern to use | `hierarchical` |
| `SELF_HEALING_ENABLED` | Enable self-healing | `true` |

## 📦 What's New

### MCP Protocol

- Standard interface for AI tool integration
- Scales to 100+ tools without context overflow
- Compatible with Claude, ChatGPT, and other LLMs

```python
# Register custom tool
system.tool_registry.register(
    name='my_tool',
    handler=my_async_function,
    description='Does something useful',
    category='custom'
)
```

### Playwright Automation

- Cross-browser support (Chromium, Firefox, WebKit)
- Auto-wait for elements (no manual waits needed)
- Self-healing on selector changes

```python
# Browser agent usage
agent = PlaywrightBrowserAgent('browser-1')
await agent.initialize()

result = await agent.execute({
    'action': 'navigate',
    'params': {'url': 'https://example.com'}
})
```

### AI Script Generation

- Natural language → Playwright code
- Automatic syntax validation
- Self-healing script repair

```python
generator = ScriptGenerator()

result = await generator.generate_playwright_script(
    "Сделай скриншот главной страницы"
)

print(result['code'])  # Ready-to-use Playwright script
```

### Multi-Agent Orchestration

- **PlanningAgent** - Decomposes tasks with GPT-5.1
- **ExecutionAgent** - Runs browser automation
- **MonitoringAgent** - Detects errors and recovers

4 orchestration patterns:
1. **Sequential** - Execute agents one by one
2. **Parallel** - Execute agents simultaneously
3. **Hierarchical** - Supervisor + workers
4. **Handoff** - Dynamic delegation

## 🧪 Testing

### Run All Demos

```bash
python examples/ai_automation_demo.py
```

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_integration.py::test_system_initialization -v
```

## 🐛 Troubleshooting

### Issue: "Playwright not installed"

```bash
playwright install
```

### Issue: "OpenAI API key not set"

Add to `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

### Issue: "LangGraph not found"

```bash
pip install langgraph langchain langchain-core
```

### Issue: Browser fails to start

Check headless mode:
```bash
# In .env
PLAYWRIGHT_HEADLESS=false  # For debugging
```

## 📚 Documentation

- **Full Documentation**: See [Notion page](https://www.notion.so/2ac65511388d815fa690c20766ed1206)
- **API Reference**: Run `system.tool_registry.generate_api_documentation()`
- **Examples**: Check `examples/` directory
- **Tests**: Check `tests/` directory

## 🚀 Next Steps

1. **Try the demos** - Run example scripts
2. **Create custom agents** - Extend `LegionAgent` class
3. **Register tools** - Add your own MCP tools
4. **Build workflows** - Create orchestration patterns
5. **Deploy to production** - Use Docker/Kubernetes configs

## 📞 Support

- **GitHub Issues**: https://github.com/legion14041981-ui/Legion/issues
- **Pull Request**: https://github.com/legion14041981-ui/Legion/pull/1
- **Documentation**: https://www.notion.so/2ac65511388d815fa690c20766ed1206

## ✅ Compatibility

- **Python**: 3.9+
- **Operating Systems**: Linux, macOS, Windows
- **Browsers**: Chromium, Firefox, WebKit
- **AI Models**: GPT-4 Turbo, GPT-5.1, Claude, and other OpenAI-compatible APIs

---

**Ready to automate? Start with the examples above!** 🚀
=======
See full guide above for installation, configuration, and examples.

## 📚 Documentation

- **GitHub**: https://github.com/legion14041981-ui/Legion
- **Notion**: https://www.notion.so/2ac65511388d815fa690c20766ed1206
- **PR #1**: https://github.com/legion14041981-ui/Legion/pull/1

---

**Ready to automate? Start now!** 🚀
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
