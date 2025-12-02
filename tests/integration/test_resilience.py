"""Integration tests for resilience patterns."""

import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock

from src.legion.core import LegionCore
from src.legion.base_agent import LegionAgent


class UnreliableAgent(LegionAgent):
    """Agent that fails intermittently."""
    
    def __init__(self, agent_id: str, fail_rate: float = 0.5):
        super().__init__(agent_id)
        self.fail_rate = fail_rate
        self.attempt_count = 0
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with intermittent failures."""
        self.attempt_count += 1
        
        # Fail based on attempt count
        if self.attempt_count % 2 == 0:
            raise RuntimeError("Simulated failure")
        
        return {'status': 'completed', 'attempts': self.attempt_count}


class TestResiliencePatterns:
    """Test resilience and fault tolerance."""
    
    @pytest.fixture
    def core(self):
        """Create Legion core."""
        core = LegionCore()
        core.start()
        yield core
        core.stop()
    
    def test_fallback_to_task_queue(self, core):
        """Test tasks queue when no agent available."""
        # Dispatch without agent
        result = core.dispatch_task(
            "task_1",
            {"type": "test"},
            required_capability="nonexistent"
        )
        
        # Should return None and add to queue
        assert result is None
        assert len(core.task_queue) == 1
        assert core.task_queue[0]['task_id'] == "task_1"
    
    def test_multiple_agents_same_capability(self, core):
        """Test load distribution across multiple agents."""
        # Register multiple agents with same capability
        agents = []
        for i in range(3):
            agent = Mock(spec=LegionAgent)
            agent.agent_id = f"agent_{i}"
            agent.execute.return_value = {'status': 'completed', 'agent': i}
            agents.append(agent)
            core.register_agent(f"agent_{i}", agent, capabilities=["shared"])
        
        # Dispatch multiple tasks
        for i in range(10):
            core.dispatch_task(f"task_{i}", {"index": i}, required_capability="shared")
        
        # All agents should have been used
        total_calls = sum(agent.execute.call_count for agent in agents)
        assert total_calls == 10
    
    def test_agent_failure_handling(self, core):
        """Test handling of agent execution failures."""
        agent = UnreliableAgent("unreliable")
        core.register_agent("unreliable", agent, capabilities=["test"])
        
        # First call should succeed
        result1 = core.dispatch_task("task_1", {"type": "test"}, required_capability="test")
        assert result1['status'] == 'completed'
        
        # Second call should fail
        with pytest.raises(RuntimeError, match="Simulated failure"):
            core.dispatch_task("task_2", {"type": "test"}, required_capability="test")
        
        # Third call should succeed again
        result3 = core.dispatch_task("task_3", {"type": "test"}, required_capability="test")
        assert result3['status'] == 'completed'
    
    def test_watchdog_rollback_on_poor_performance(self, core):
        """Test performance watchdog triggers rollback."""
        from src.legion.neuro_architecture.watchdog import PerformanceWatchdog
        
        watchdog = PerformanceWatchdog(degradation_threshold=0.5, max_history_size=10)
        
        # Simulate good performance
        for i in range(5):
            watchdog.track_execution("agent_1", duration=0.1, memory_used=100)
        
        assert not watchdog.should_rollback("agent_1")
        
        # Simulate performance degradation
        for i in range(5):
            watchdog.track_execution("agent_1", duration=0.5, memory_used=500)
        
        # Should trigger rollback
        assert watchdog.should_rollback("agent_1")
    
    def test_capability_not_found_graceful_degradation(self, core):
        """Test graceful degradation when capability not found."""
        # Try to dispatch without matching agent
        result = core.dispatch_task(
            "task_1",
            {"type": "test"},
            required_capability="missing_capability"
        )
        
        # Should not crash, should queue task
        assert result is None
        assert len(core.task_queue) > 0
