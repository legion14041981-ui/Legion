"""Pytest configuration and shared fixtures.

Provides common fixtures used across test suite:
- Legion core instances
- Test agents
- Database connections
- Mock objects
"""

import pytest
import asyncio
import os
import tempfile
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from src.legion.core import LegionCore
from src.legion.base_agent import LegionAgent


class SimpleTestAgent(LegionAgent):
    """Simple agent for testing."""

    def __init__(self, agent_id: str, name: str = None, response: Dict[str, Any] = None):
        super().__init__(agent_id)
        self.name = name or agent_id
        self.response = response or {'status': 'completed'}
        self.call_count = 0

    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task and return response."""
        self.call_count += 1
        return {**self.response, 'task_data': task_data}

    async def execute_async(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task asynchronously."""
        await asyncio.sleep(0.001)
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
def sample_agent():
    """Create a sample test agent for testing.

    Returns:
        SimpleTestAgent: Test agent instance
    """
    return SimpleTestAgent(
        agent_id="test-agent",
        name="Test Agent"
    )


@pytest.fixture
def sample_task_data():
    """Create sample task data for testing.

    Returns:
        dict: Sample task data
    """
    return {
        'task_id': 'test-task-1',
        'action': 'test_action',
        'params': {'key': 'value'}
    }


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
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    yield url
    try:
        os.unlink(path)
    except Exception:
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


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing.

    Returns:
        AsyncMock: Mock Redis client
    """
    redis = AsyncMock()
    storage = {}

    async def mock_get(key):
        return storage.get(key)

    async def mock_setex(key, ttl, value):
        storage[key] = value
        return True

    async def mock_delete(key):
        if key in storage:
            del storage[key]
            return 1
        return 0

    async def mock_close():
        pass

    redis.get = AsyncMock(side_effect=mock_get)
    redis.setex = AsyncMock(side_effect=mock_setex)
    redis.delete = AsyncMock(side_effect=mock_delete)
    redis.close = AsyncMock(side_effect=mock_close)
    return redis


@pytest.fixture
async def mock_db_pool():
    """Mock asyncpg database pool for testing.

    Returns:
        AsyncMock: Mock database pool
    """
    pool = AsyncMock()
    mock_data = [
        {'id': 1, 'title': 'Test Task 1'},
        {'id': 2, 'title': 'Test Task 2'},
    ]

    async def mock_fetch(query, *args):
        return mock_data

    async def mock_fetchrow(query, *args):
        return mock_data[0] if mock_data else None

    async def mock_execute(query, *args):
        return "CREATE TABLE"

    async def mock_close():
        pass

    pool.fetch = AsyncMock(side_effect=mock_fetch)
    pool.fetchrow = AsyncMock(side_effect=mock_fetchrow)
    pool.execute = AsyncMock(side_effect=mock_execute)
    pool.close = AsyncMock(side_effect=mock_close)
    return pool


@pytest.fixture
async def mock_http_client():
    """Mock httpx AsyncClient for testing.

    Returns:
        AsyncMock: Mock HTTP client
    """
    client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.text = "Mock response"

    async def mock_get(*args, **kwargs):
        return mock_response

    async def mock_post(*args, **kwargs):
        return mock_response

    async def mock_aclose():
        pass

    client.get = AsyncMock(side_effect=mock_get)
    client.post = AsyncMock(side_effect=mock_post)
    client.aclose = AsyncMock(side_effect=mock_aclose)
    return client


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: marks tests as performance benchmarks"
    )
