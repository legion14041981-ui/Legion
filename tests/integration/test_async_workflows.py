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
    
    @pytest.mark.asyncio
    async def test_single_async_dispatch(self, core):
        """Test single async task dispatch."""
        result = await core.dispatch_task_async(
            "task_1",
            {"type": "test", "data": "value"},
            required_capability="async_task"
        )
        
        assert result['status'] == 'completed'
        assert 'agent_id' in result
        assert result['task_data']['data'] == 'value'
    
    @pytest.mark.asyncio
    async def test_concurrent_async_dispatch(self, core):
        """Test concurrent async task dispatching."""
        tasks = [
            core.dispatch_task_async(
                f"task_{i}",
                {"type": "test", "index": i},
                required_capability="async_task"
            )
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result['status'] == 'completed'
            assert result['task_data']['index'] == i
    
    @pytest.mark.asyncio
    async def test_async_performance(self, core):
        """Test async execution is faster than sync."""
        import time
        
        # Async execution
        start = time.time()
        tasks = [
            core.dispatch_task_async(
                f"task_{i}",
                {"type": "test"},
                required_capability="async_task"
            )
            for i in range(10)
        ]
        await asyncio.gather(*tasks)
        async_duration = time.time() - start
        
        # Should complete all 10 tasks in ~delay time (concurrent)
        # With 0.01s delay, should be < 0.1s total
        assert async_duration < 0.1
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self, core):
        """Test error handling in async workflows."""
        
        class FailingAgent(LegionAgent):
            async def execute_async(self, task_data):
                raise ValueError("Simulated error")
        
        core.register_agent("failing", FailingAgent("failing"), capabilities=["fail"])
        
        with pytest.raises(ValueError, match="Simulated error"):
            await core.dispatch_task_async(
                "task_fail",
                {"type": "test"},
                required_capability="fail"
            )
    
    @pytest.mark.asyncio
    async def test_async_timeout(self, core):
        """Test async task timeout."""
        
        class SlowAgent(LegionAgent):
            async def execute_async(self, task_data):
                await asyncio.sleep(10)  # Very slow
                return {'status': 'completed'}
        
        core.register_agent("slow", SlowAgent("slow"), capabilities=["slow"])
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                core.dispatch_task_async(
                    "task_slow",
                    {"type": "test"},
                    required_capability="slow"
                ),
                timeout=0.1
            )
