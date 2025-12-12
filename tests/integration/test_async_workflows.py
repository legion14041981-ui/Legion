"""Integration tests for async workflows."""

import pytest
import asyncio
from typing import Dict, Any

from src.legion.core import LegionCore
from src.legion.base_agent import LegionAgent


class AsyncTestAgent(LegionAgent):
    """Test agent with async execution."""

    def __init__(self, agent_id: str, delay: float = 0.01):
        super().__init__(agent_id)
        self.delay = delay
        self.execution_count = 0

    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task synchronously (required by base class)."""
        return asyncio.run(self.execute_async(task_data))

    async def execute_async(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task asynchronously."""
        self.execution_count += 1
        await asyncio.sleep(self.delay)
        return {
            'status': 'completed',
            'agent_id': self.agent_id,
            'task_data': task_data,
            'execution_count': self.execution_count
        }


class TestAsyncWorkflows:
    """Test asynchronous workflow patterns."""

    @pytest.fixture
    def core(self):
        """Create Legion core with async agents."""
        core = LegionCore()

        # Register multiple async agents
        for i in range(3):
            agent = AsyncTestAgent(f"async_agent_{i}")
            core.register_agent(f"async_agent_{i}", agent, capabilities=["async_task"])

        core.start()
        yield core
        core.stop()
