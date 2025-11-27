# 🚀 Legion + Aider Integration Guide

## Overview

This document describes the comprehensive integration of **Aider CLI** (AI-powered code assistance) with the **Legion multi-agent framework**. This integration enables Legion agents to leverage advanced code analysis, generation, refactoring, and optimization capabilities powered by Aider and OpenRouter.

## Architecture

### Components

#### 1. **AiderBridge** (`src/legion/integrations/aider_bridge.py`)
- Asynchronous wrapper around Aider CLI
- Manages subprocess communication through stdin/stdout pipes
- Thread-safe command execution with locks
- Event callback system for extensibility
- Session tracking and status monitoring

**Features:**
- Single command execution: `bridge.send_command()`
- Batch processing: `bridge.send_batch()`
- Event callbacks: `register_callback()`, `trigger_callback()`
- Context manager support: `with AiderBridge() as bridge:`

#### 2. **AiderAgent** (`src/legion/agents/aider_agent.py`)
- LegionAgent subclass wrapping AiderBridge
- High-level interface for code tasks
- Task execution with result tracking
- Batch task processing

**Supported Task Types:**
- `"analyze"` - Code analysis and recommendations
- `"generate"` - Code generation from descriptions
- `"refactor"` - Code refactoring and optimization
- `"bugfix"` - Bug identification and fixing
- `"document"` - Documentation generation
- Custom tasks for generic queries

#### 3. **AiderProtocol** (Planned)
- Standardized message protocol
- Serialization/deserialization
- Error handling and retry logic

## Setup & Configuration

### Prerequisites

1. **Aider CLI** installed:
   ```powershell
   pip install aider-chat
   ```

2. **API Key** (OpenRouter recommended for free tier):
   ```powershell
   $env:OPENROUTER_API_KEY = "your-key-here"
   ```

3. **Git Repository** initialized in working directory

### Installation

```bash
# Clone Legion
git clone https://github.com/legion14041981-ui/Legion.git
cd Legion

# Install dependencies
pip install -r requirements.txt
```

## Usage Examples

### Basic Bridge Usage

```python
from legion.integrations.aider_bridge import AiderBridge

# Create bridge
bridge = AiderBridge(repo_path=r"C:\Legion")

# Start
if bridge.start():
    # Send command
    result = bridge.send_command("Analyze the project structure")
    print(result)
    
    # Close
    bridge.close()

# Or use context manager
with AiderBridge() as bridge:
    result = bridge.send_command("Generate API documentation")
    print(result)
```

### AiderAgent Usage

```python
import asyncio
from legion.agents.aider_agent import AiderAgent

async def main():
    # Create agent
    agent = AiderAgent(agent_id="aider-1")
    
    # Initialize
    await agent.initialize()
    
    # Execute tasks
    task = {
        "type": "refactor",
        "description": "Improve variable naming in core.py"
    }
    result = await agent.execute(task)
    print(result)
    
    # Shutdown
    await agent.shutdown()

asyncio.run(main())
```

### Batch Processing

```python
tasks = [
    {"type": "analyze", "description": "Security review"},
    {"type": "generate", "description": "Create utils module"},
    {"type": "refactor", "description": "Optimize queries"},
]

results = await agent.batch_execute(tasks)
print(f"Completed {results['total_tasks']} tasks")
```

## Integration with Legion Core

### Registering AiderAgent

```python
from legion.core import LegionCore
from legion.agents.aider_agent import AiderAgent

core = LegionCore()

# Register aider agent
aider_agent = AiderAgent(agent_id="aider-main")
await aider_agent.initialize()
core.register_agent("aider-main", aider_agent)
```

### Task Routing

```python
# Legion can route code-related tasks to AiderAgent
task = {
    "target_agent": "aider-main",
    "type": "analyze",
    "description": "Review new feature implementation"
}

result = await core.execute_task(task)
```

## Advanced Features

### Event Callbacks

```python
def on_task_complete(data):
    logger.info(f"Task completed: {data}")

bridge.register_callback("on_task_complete", on_task_complete)
bridge.trigger_callback("on_task_complete", {"result": "..."})
```

### Custom Models

```python
# Use different LLM model
agent = AiderAgent(
    agent_id="gpt4-agent",
    model="gpt-4-turbo"
)
```

### Status Monitoring

```python
status = agent.get_status()
print(f"Tasks executed: {status['tasks_executed']}")
print(f"Agent status: {status['status']}")
print(f"Bridge status: {status['bridge_status']}")
```

## Performance Considerations

1. **Concurrency**: Use asyncio for parallel task execution
2. **Batching**: Group related tasks to reduce overhead
3. **Caching**: Cache model responses when possible
4. **Timeouts**: Configure timeouts for long-running operations
5. **Error Handling**: Implement retry logic for network issues

## Error Handling

```python
try:
    result = await agent.execute(task)
    if result['status'] == 'error':
        logger.error(f"Task failed: {result['error']}")
except Exception as e:
    logger.error(f"Execution error: {str(e)}", exc_info=True)
```

## Testing

```bash
# Run integration tests
pytest tests/test_aider_integration.py -v

# Run demo
python examples/aider_integration_demo.py
```

## Troubleshooting

### Aider not found
```powershell
# Ensure aider is in PATH
pip install --upgrade aider-chat
```

### API Key issues
```powershell
# Verify environment variable
echo $env:OPENROUTER_API_KEY
```

### Git Repository errors
```bash
# Ensure git repo is initialized
git init
git config user.email "agent@legion.local"
git config user.name "Legion Agent"
```

## Future Enhancements

- [ ] AiderProtocol for standardized messaging
- [ ] WebSocket support for real-time streaming
- [ ] Multi-agent coordination for complex tasks
- [ ] Advanced caching layer
- [ ] Integration with Supabase for task persistence
- [ ] Metrics and telemetry
- [ ] Web dashboard for monitoring

## Contributing

Contributions are welcome! Please follow the Legion contribution guidelines and include:
- Unit tests for new functionality
- Documentation updates
- Example usage
- Performance benchmarks when applicable

## License

MIT License - See LICENSE file for details

## References

- [Aider Documentation](https://aider.chat/)
- [OpenRouter API](https://openrouter.ai/)
- [Legion Framework](https://github.com/legion14041981-ui/Legion)
- [AsyncIO Guide](https://docs.python.org/3/library/asyncio.html)
