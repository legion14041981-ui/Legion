"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        'type': 'general',
        'description': 'Test task',
        'priority': 1
    }


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    from legion.base_agent import LegionAgent
    
    class TestAgent(LegionAgent):
        def execute(self, task_data):
            return {'status': 'completed', 'result': 'test'}
    
    return TestAgent('test_agent', {'test': True})


@pytest.fixture
def legion_core():
    """Create LegionCore instance for testing."""
    from legion.core import LegionCore
    return LegionCore(config={'enable_task_queue': True})
