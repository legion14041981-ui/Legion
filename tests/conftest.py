"""Pytest configuration and shared fixtures.

Provides common fixtures used across test suite:
- Legion core instances
- Test agents
- Database connections
- Mock objects
"""

import pytest
import asyncio
from typing import Dict, Any
import tempfile
import os

from src.legion.core import LegionCore
from src.legion.base_agent import LegionAgent


class SimpleTestAgent(LegionAgent):
    """Simple agent for testing."""
    
    def __init__(self, agent_id: str, response: Dict[str, Any] = None):
        super().__init__(agent_id)
        self.response = response or {'status': 'completed'}
        self.call_count = 0
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task and return response."""
        self.call_count += 1
        return {**self.response, 'task_data': task_data}
    
    async def execute_async(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task asynchronously."""
        await asyncio.sleep(0.001)  # Simulate async work
        return self.execute(task_data)


@pytest.fixture
def legion_core():
    """Create a fresh Legion core instance.
    
    Yields:
        LegionCore: Fresh core instance
    """
    core = LegionCore()
    core.start()
    yield core
    core.stop()


@pytest.fixture
def simple_agent():
    """Create a simple test agent.
    
    Returns:
        SimpleTestAgent: Test agent instance
    """
    return SimpleTestAgent("test_agent")


@pytest.fixture
def core_with_agent(legion_core, simple_agent):
    """Create Legion core with registered agent.
    
    Returns:
        tuple: (core, agent)
    """
    legion_core.register_agent(
        "test_agent",
        simple_agent,
        capabilities=["test_capability"]
    )
    return legion_core, simple_agent


@pytest.fixture
def temp_db_url():
    """Create temporary database URL for testing.
    
    Yields:
        str: SQLite database URL
    """
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    url = f"sqlite:///{path}"
    yield url
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests.
    
    Yields:
        asyncio.AbstractEventLoop: Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setenv("LEGION_OS_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("POOL_SIZE", "5")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m "not slow"'")
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
