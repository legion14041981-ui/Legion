"""Unit tests for base agent module."""

import pytest
import asyncio
from legion.base_agent import LegionAgent


class ConcreteAgent(LegionAgent):
    """Concrete implementation for testing."""
    
    def __init__(self, agent_id, config=None):
        super().__init__(agent_id, config)
        self.execute_count = 0
    
    def execute(self, task_data):
        """Execute task."""
        self.execute_count += 1
        return {'status': 'success', 'data': task_data}


class TestLegionAgent:
    """Test suite for LegionAgent base class."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = ConcreteAgent('test_agent')
        assert agent.agent_id == 'test_agent'
        assert agent.is_active is False
        assert agent.config == {}
    
    def test_initialization_with_config(self):
        """Test agent initialization with config."""
        config = {'key': 'value', 'number': 42}
        agent = ConcreteAgent('test_agent', config)
        assert agent.config == config
    
    def test_start_stop(self):
        """Test starting and stopping agent."""
        agent = ConcreteAgent('test_agent')
        assert agent.is_active is False
        agent.start()
        assert agent.is_active is True
        agent.stop()
        assert agent.is_active is False
    
    def test_execute(self):
        """Test task execution."""
        agent = ConcreteAgent('test_agent')
        task_data = {'type': 'test', 'payload': 'data'}
        result = agent.execute(task_data)
        assert result['status'] == 'success'
        assert result['data'] == task_data
        assert agent.execute_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_async_default(self):
        """Test default async execution (delegates to sync)."""
        agent = ConcreteAgent('test_agent')
        task_data = {'type': 'test'}
        result = await agent.execute_async(task_data)
        assert result['status'] == 'success'
        assert agent.execute_count == 1
    
    def test_get_status(self):
        """Test status retrieval."""
        config = {'test': True}
        agent = ConcreteAgent('test_agent', config)
        agent.start()
        status = agent.get_status()
        assert status['agent_id'] == 'test_agent'
        assert status['is_active'] is True
        assert status['config'] == config
    
    def test_validate_task_valid(self):
        """Test task validation with valid data."""
        agent = ConcreteAgent('test_agent')
        assert agent.validate_task({'key': 'value'}) is True
    
    def test_validate_task_none(self):
        """Test task validation with None."""
        agent = ConcreteAgent('test_agent')
        assert agent.validate_task(None) is False
    
    def test_repr(self):
        """Test string representation."""
        agent = ConcreteAgent('test_agent')
        repr_str = repr(agent)
        assert 'test_agent' in repr_str
        assert 'active=False' in repr_str
        agent.start()
        repr_str = repr(agent)
        assert 'active=True' in repr_str
