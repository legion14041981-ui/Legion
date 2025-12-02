"""Integration tests for task dispatching."""

import pytest
from legion.core import LegionCore
from legion.base_agent import LegionAgent


class CodingAgent(LegionAgent):
    """Test coding agent."""
    
    def execute(self, task_data):
        return {'status': 'code_written', 'lines': 100}


class TestingAgent(LegionAgent):
    """Test testing agent."""
    
    def execute(self, task_data):
        return {'status': 'tests_passed', 'count': 42}


class TestTaskDispatchIntegration:
    """Integration tests for task dispatching system."""
    
    def test_multi_agent_registration(self):
        """Test registering multiple agents with different capabilities."""
        core = LegionCore()
        
        coding_agent = CodingAgent('coder', {})
        testing_agent = TestingAgent('tester', {})
        
        core.register_agent('coder', coding_agent, ['coding', 'review'])
        core.register_agent('tester', testing_agent, ['testing', 'qa'])
        
        assert len(core.agents) == 2
        assert core.agent_capabilities['coder'] == ['coding', 'review']
        assert core.agent_capabilities['tester'] == ['testing', 'qa']
    
    def test_capability_based_routing(self):
        """Test task routing based on capabilities."""
        core = LegionCore()
        
        coding_agent = CodingAgent('coder', {})
        testing_agent = TestingAgent('tester', {})
        
        core.register_agent('coder', coding_agent, ['coding'])
        core.register_agent('tester', testing_agent, ['testing'])
        
        # Dispatch coding task
        coding_task = {'type': 'coding', 'description': 'Write function'}
        result = core.dispatch_task('task1', coding_task, 'coding')
        assert result['status'] == 'code_written'
        
        # Dispatch testing task
        testing_task = {'type': 'testing', 'description': 'Run tests'}
        result = core.dispatch_task('task2', testing_task, 'testing')
        assert result['status'] == 'tests_passed'
    
    def test_general_capability_fallback(self):
        """Test fallback to general capability."""
        core = LegionCore()
        
        general_agent = CodingAgent('general', {})
        core.register_agent('general', general_agent, ['general'])
        
        # Any task should route to general agent
        task = {'type': 'unknown', 'description': 'Do something'}
        result = core.dispatch_task('task1', task, 'unknown')
        assert result is not None
    
    def test_task_queuing_when_no_agent(self):
        """Test task queuing when no suitable agent exists."""
        core = LegionCore(config={'enable_task_queue': True})
        
        coding_agent = CodingAgent('coder', {})
        core.register_agent('coder', coding_agent, ['coding'])
        
        # Dispatch task requiring testing capability (not available)
        task = {'type': 'testing', 'description': 'Run tests'}
        result = core.dispatch_task('task1', task, 'testing')
        
        assert result is None
        assert core.get_task_queue_size() == 1
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: register -> start -> dispatch -> stop."""
        core = LegionCore()
        
        agent = CodingAgent('worker', {})
        core.register_agent('worker', agent, ['coding'])
        
        # Start system
        core.start()
        assert core.is_running is True
        
        # Start agent
        agent.start()
        assert agent.is_active is True
        
        # Dispatch task
        task = {'type': 'coding', 'description': 'Write code'}
        result = core.dispatch_task('task1', task, 'coding')
        assert result['status'] == 'code_written'
        
        # Check health
        health = core.get_health()
        assert health['status'] == 'healthy'
        assert health['agents']['active'] == 1
        
        # Stop agent
        agent.stop()
        assert agent.is_active is False
        
        # Stop system
        core.stop()
        assert core.is_running is False
