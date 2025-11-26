"""
Tests for Legion v2.3 features:
- Circuit Breaker pattern
- Retry mechanism
- Health checks
- Async core methods
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from legion.utils.circuit_breaker import CircuitBreaker, CircuitBreakerState
from legion.utils.retry import retry, RetryableTask
from legion.core import LegionCore


class TestCircuitBreaker:
    """Tests for Circuit Breaker pattern."""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test successful call through circuit breaker."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        @cb
        async def successful_operation():
            return "success"
        
        result = await successful_operation()
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)
        
        @cb
        async def failing_operation():
            raise ValueError("Test error")
        
        # First 3 failures should be recorded
        for i in range(3):
            with pytest.raises(ValueError):
                await failing_operation()
        
        # Circuit should be OPEN now
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3
        
        # Next call should be rejected without executing
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await failing_operation()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker transitions to HALF_OPEN after timeout."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        @cb
        async def operation(should_fail=True):
            if should_fail:
                raise ValueError("Error")
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await operation()
        
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # Next call should transition to HALF_OPEN
        result = await operation(should_fail=False)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED


class TestRetryMechanism:
    """Tests for retry decorator and mechanism."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test retry succeeds on first attempt."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_operation()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Test retry succeeds after some failures."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01, backoff=1.0)
        async def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"
        
        result = await eventually_successful()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Test retry fails after max attempts."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            await always_fails()
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test retry uses exponential backoff."""
        delays = []
        
        @retry(max_attempts=3, delay=0.1, backoff=2.0)
        async def track_delays():
            import time
            delays.append(time.time())
            raise ValueError("Test")
        
        with pytest.raises(ValueError):
            await track_delays()
        
        # Should have 3 attempts
        assert len(delays) == 3
        
        # Check delays are increasing (exponential backoff)
        # First delay: ~0.1s, second delay: ~0.2s
        if len(delays) >= 3:
            delay1 = delays[1] - delays[0]
            delay2 = delays[2] - delays[1]
            # Allow some tolerance
            assert delay2 > delay1


class TestRetryableTask:
    """Tests for RetryableTask class."""
    
    @pytest.mark.asyncio
    async def test_retryable_task_execution(self):
        """Test RetryableTask successful execution."""
        async def test_coroutine():
            return "result"
        
        task = RetryableTask(test_coroutine(), max_attempts=3, delay=0.01)
        result = await task.execute()
        assert result == "result"
        assert task.attempt == 1
        assert task.success is True
    
    @pytest.mark.asyncio
    async def test_retryable_task_with_failures(self):
        """Test RetryableTask with transient failures."""
        attempts = 0
        
        async def flaky_operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Transient error")
            return "success"
        
        task = RetryableTask(flaky_operation(), max_attempts=3, delay=0.01)
        result = await task.execute()
        assert result == "success"
        assert task.attempt == 2
        assert task.success is True


class TestLegionCoreV23:
    """Tests for LegionCore v2.3 features."""
    
    @pytest.mark.asyncio
    async def test_async_agent_registration(self):
        """Test async agent registration."""
        core = LegionCore()
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.agent_id = "test_agent"
        mock_agent.start = AsyncMock()
        
        await core.register_agent_async("test_agent", mock_agent)
        assert "test_agent" in core.agents
    
    @pytest.mark.asyncio
    async def test_health_check_api(self):
        """Test health check returns proper status."""
        core = LegionCore()
        health = core.get_health()
        
        assert "status" in health
        assert "timestamp" in health
        assert "agents" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        """Test metrics are tracked correctly."""
        core = LegionCore()
        metrics = core.get_metrics()
        
        assert "total_agents" in metrics
        assert "active_agents" in metrics
        assert "total_tasks" in metrics
        assert isinstance(metrics["total_agents"], int)
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown stops all agents."""
        core = LegionCore()
        
        # Mock agents
        mock_agent1 = Mock()
        mock_agent1.agent_id = "agent1"
        mock_agent1.stop = AsyncMock()
        mock_agent1.is_active = True
        
        mock_agent2 = Mock()
        mock_agent2.agent_id = "agent2"
        mock_agent2.stop = AsyncMock()
        mock_agent2.is_active = True
        
        await core.register_agent_async("agent1", mock_agent1)
        await core.register_agent_async("agent2", mock_agent2)
        
        # Graceful shutdown
        await core.stop_async()
        
        # Verify all agents were stopped
        mock_agent1.stop.assert_called_once()
        mock_agent2.stop.assert_called_once()


class TestAsyncCoreIntegration:
    """Integration tests for async core functionality."""
    
    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        """Test full start/stop lifecycle."""
        core = LegionCore()
        
        await core.start_async()
        assert core.is_running is True
        
        await core.stop_async()
        assert core.is_running is False
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self):
        """Test multiple agents can operate concurrently."""
        core = LegionCore()
        
        # Create multiple mock agents
        agents = []
        for i in range(3):
            mock_agent = Mock()
            mock_agent.agent_id = f"agent_{i}"
            mock_agent.start = AsyncMock()
            mock_agent.stop = AsyncMock()
            agents.append(mock_agent)
            await core.register_agent_async(f"agent_{i}", mock_agent)
        
        # Start all
        await core.start_async()
        
        # Verify all started
        for agent in agents:
            agent.start.assert_called()
        
        # Stop all
        await core.stop_async()
        
        # Verify all stopped
        for agent in agents:
            agent.stop.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
