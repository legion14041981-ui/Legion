"""Unit tests for Legion Core module."""

import pytest
from legion.core import (
    LegionCore, 
    LegionError, 
    TaskDispatchError, 
    AgentNotFoundError,
    ConfigurationError
)


class TestLegionCore:
    """Test suite for LegionCore."""
    
    def test_initialization(self):
        """Test LegionCore initialization."""
        core = LegionCore()
        assert core.is_running is False
        assert len(core.agents) == 0
        assert len(core.agent_capabilities) == 0
    
    def test_initialization_with_config(self):
        """Test LegionCore initialization with config."""
        config = {'enable_task_queue': True, 'test': 'value'}
        core = LegionCore(config=config)
        assert core.config == config
        assert core.config['enable_task_queue'] is True
    
    def test_agent_registration(self, legion_core, sample_agent):
        """Test agent registration."""
        legion_core.register_agent('test_agent', sample_agent)
        assert 'test_agent' in legion_core.agents
        assert legion_core.agents['test_agent'] == sample_agent
    
    def test_agent_registration_with_capabilities(self, legion_core, sample_agent):
        """Test agent registration with capabilities."""
        capabilities = ['coding', 'testing']
        legion_core.register_agent('test_agent', sample_agent, capabilities)
        assert legion_core.agent_capabilities['test_agent'] == capabilities
    
    def test_duplicate_agent_registration(self, legion_core, sample_agent):
        """Test that duplicate agent registration raises error."""
        legion_core.register_agent('test_agent', sample_agent)
        with pytest.raises(ValueError, match="already registered"):
            legion_core.register_agent('test_agent', sample_agent)
    
    def test_get_agent(self, legion_core, sample_agent):
        """Test getting agent by ID."""
        legion_core.register_agent('test_agent', sample_agent)
        retrieved = legion_core.get_agent('test_agent')
        assert retrieved == sample_agent
    
    def test_get_nonexistent_agent(self, legion_core):
        """Test getting non-existent agent raises error."""
        with pytest.raises(AgentNotFoundError):
            legion_core.get_agent('nonexistent')
    
    def test_get_all_agents(self, legion_core, sample_agent):
        """Test getting all agents."""
        legion_core.register_agent('agent1', sample_agent)
        legion_core.register_agent('agent2', sample_agent)
        agents = legion_core.get_all_agents()
        assert len(agents) == 2
        assert 'agent1' in agents
        assert 'agent2' in agents
    
    def test_start_stop(self, legion_core):
        """Test starting and stopping core."""
        assert legion_core.is_running is False
        legion_core.start()
        assert legion_core.is_running is True
        legion_core.stop()
        assert legion_core.is_running is False
    
    def test_dispatch_task_with_capability(self, legion_core, sample_agent, sample_task_data):
        """Test task dispatching with specific capability."""
        legion_core.register_agent('test_agent', sample_agent, ['general'])
        result = legion_core.dispatch_task('task1', sample_task_data, 'general')
        assert result is not None
        assert result['status'] == 'completed'
    
    def test_dispatch_task_no_matching_agent(self, legion_core, sample_task_data):
        """Test task dispatching with no matching agent queues task."""
        result = legion_core.dispatch_task('task1', sample_task_data, 'nonexistent')
        assert result is None
        assert legion_core.get_task_queue_size() == 1
    
    def test_dispatch_task_no_queue(self, sample_agent, sample_task_data):
        """Test task dispatching with queue disabled raises error."""
        core = LegionCore(config={'enable_task_queue': False})
        with pytest.raises(TaskDispatchError, match="No agent found"):
            core.dispatch_task('task1', sample_task_data, 'nonexistent')
    
    def test_get_health_healthy(self, legion_core, sample_agent):
        """Test health check when system is healthy."""
        legion_core.register_agent('agent1', sample_agent)
        sample_agent.is_active = True
        legion_core.start()
        health = legion_core.get_health()
        assert health['status'] == 'healthy'
        assert health['is_running'] is True
        assert health['agents']['total'] == 1
        assert health['agents']['active'] == 1
    
    def test_get_health_unhealthy(self, legion_core):
        """Test health check when system is unhealthy."""
        health = legion_core.get_health()
        assert health['status'] == 'unhealthy'
        assert health['is_running'] is False
    
    def test_get_metrics(self, legion_core, sample_agent):
        """Test metrics retrieval."""
        legion_core.register_agent('agent1', sample_agent)
        legion_core.start()
        metrics = legion_core.get_metrics()
        assert metrics['total_agents'] == 1
        assert metrics['system_running'] is True
        assert 'queued_tasks' in metrics
    
    def test_task_queue_size(self, legion_core, sample_task_data):
        """Test task queue size tracking."""
        assert legion_core.get_task_queue_size() == 0
        legion_core.dispatch_task('task1', sample_task_data, 'nonexistent')
        assert legion_core.get_task_queue_size() == 1


class TestCustomExceptions:
    """Test custom exception hierarchy."""
    
    def test_legion_error(self):
        """Test base LegionError."""
        with pytest.raises(LegionError):
            raise LegionError("Test error")
    
    def test_task_dispatch_error(self):
        """Test TaskDispatchError."""
        with pytest.raises(TaskDispatchError):
            raise TaskDispatchError("Dispatch failed")
    
    def test_agent_not_found_error(self):
        """Test AgentNotFoundError."""
        with pytest.raises(AgentNotFoundError):
            raise AgentNotFoundError("Agent not found")
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Invalid config")
