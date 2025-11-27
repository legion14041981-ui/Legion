"""
Comprehensive unit tests for Legion utils modules.

Covers:
- Circuit Breaker edge cases
- Retry edge cases  
- Error handling
- State transitions
- Configuration validation
"""

import pytest
import asyncio
import time
from typing import Any

from legion.utils.circuit_breaker import CircuitBreaker, CircuitBreakerState
from legion.utils.retry import retry, RetryableTask


class TestCircuitBreakerEdgeCases:
    """Edge case tests for Circuit Breaker."""

    def test_circuit_breaker_initialization(self):
        """Test various initialization parameters."""
        # Default parameters
        cb1 = CircuitBreaker()
        assert cb1.failure_threshold == 5
        assert cb1.timeout == 60

        # Custom parameters
        cb2 = CircuitBreaker(failure_threshold=10, timeout=120)
        assert cb2.failure_threshold == 10
        assert cb2.timeout == 120

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_persistence(self):
        """Test that circuit breaker state persists across calls."""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)
        call_count = 0

        @cb
        async def operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error")

        # First failure
        with pytest.raises(ValueError):
            await operation()
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.CLOSED

        # Second failure - should open circuit
        with pytest.raises(ValueError):
            await operation()
        assert cb.failure_count == 2
        assert cb.state == CircuitBreakerState.OPEN

        # Third call should be rejected
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await operation()
        assert call_count == 2  # Should not have executed

    @pytest.mark.asyncio
    async def test_circuit_breaker_reset_on_success(self):
        """Test that failure count resets on successful call."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)
        attempts = 0

        @cb
        async def flaky_operation():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary error")
            return "success"

        # Two failures
        with pytest.raises(ValueError):
            await flaky_operation()
        with pytest.raises(ValueError):
            await flaky_operation()

        assert cb.failure_count == 2

        # Success should reset
        result = await flaky_operation()
        assert result == "success"
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout_transition(self):
        """Test transition from OPEN to HALF_OPEN after timeout."""
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)

        @cb
        async def operation(should_fail=True):
            if should_fail:
                raise ValueError("Error")
            return "success"

        # Open circuit
        with pytest.raises(ValueError):
            await operation()

        assert cb.state == CircuitBreakerState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next successful call should close circuit
        result = await operation(should_fail=False)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self):
        """Test that failure in HALF_OPEN reopens circuit."""
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)

        @cb
        async def operation(should_fail=True):
            if should_fail:
                raise ValueError("Error")
            return "success"

        # Open circuit
        with pytest.raises(ValueError):
            await operation()

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Fail in HALF_OPEN - should reopen
        with pytest.raises(ValueError):
            await operation(should_fail=True)

        assert cb.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_exceptions(self):
        """Test circuit breaker with different exception types."""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)

        @cb
        async def operation(exc_type):
            if exc_type == "value":
                raise ValueError("Value error")
            elif exc_type == "type":
                raise TypeError("Type error")
            else:
                raise RuntimeError("Runtime error")

        # Different exceptions should all count as failures
        with pytest.raises(ValueError):
            await operation("value")
        with pytest.raises(TypeError):
            await operation("type")

        assert cb.state == CircuitBreakerState.OPEN


class TestRetryEdgeCases:
    """Edge case tests for Retry mechanism."""

    @pytest.mark.asyncio
    async def test_retry_with_zero_delay(self):
        """Test retry with zero delay."""
        attempts = 0

        @retry(max_attempts=3, delay=0)
        async def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Error")
            return "success"

        result = await operation()
        assert result == "success"
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_retry_single_attempt(self):
        """Test retry with max_attempts=1."""
        attempts = 0

        @retry(max_attempts=1, delay=0.01)
        async def operation():
            nonlocal attempts
            attempts += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            await operation()

        assert attempts == 1

    @pytest.mark.asyncio
    async def test_retry_preserves_exception_type(self):
        """Test that retry preserves original exception type."""

        @retry(max_attempts=2, delay=0.01)
        async def operation():
            raise CustomException("Custom error")

        with pytest.raises(CustomException, match="Custom error"):
            await operation()

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff_calculation(self):
        """Test exponential backoff timing."""
        delays: list[float] = []

        @retry(max_attempts=4, delay=0.1, backoff=2.0)
        async def operation():
            delays.append(time.time())
            raise ValueError("Error")

        with pytest.raises(ValueError):
            await operation()

        # Verify exponential backoff
        # Expected delays: 0.1, 0.2, 0.4
        assert len(delays) == 4

        if len(delays) >= 3:
            delay1 = delays[1] - delays[0]
            delay2 = delays[2] - delays[1]
            delay3 = delays[3] - delays[2]

            # Each delay should be approximately double
            assert 0.08 < delay1 < 0.15  # ~0.1s
            assert 0.15 < delay2 < 0.25  # ~0.2s
            assert 0.3 < delay3 < 0.5    # ~0.4s

    @pytest.mark.asyncio
    async def test_retry_with_custom_backoff(self):
        """Test retry with custom backoff factor."""
        attempts = 0

        @retry(max_attempts=3, delay=0.01, backoff=3.0)
        async def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Error")
            return "success"

        result = await operation()
        assert result == "success"
        assert attempts == 3


class TestRetryableTask:
    """Tests for RetryableTask class."""

    @pytest.mark.asyncio
    async def test_retryable_task_state_tracking(self):
        """Test that RetryableTask tracks state correctly."""
        attempts = 0

        async def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Error")
            return "success"

        task = RetryableTask(operation(), max_attempts=3, delay=0.01)
        assert task.attempt == 0
        assert task.success is False

        result = await task.execute()

        assert result == "success"
        assert task.attempt == 2
        assert task.success is True

    @pytest.mark.asyncio
    async def test_retryable_task_failure_tracking(self):
        """Test RetryableTask tracks failures."""
        async def failing_operation():
            raise ValueError("Always fails")

        task = RetryableTask(failing_operation(), max_attempts=3, delay=0.01)

        with pytest.raises(ValueError):
            await task.execute()

        assert task.attempt == 3
        assert task.success is False

    @pytest.mark.asyncio
    async def test_retryable_task_immediate_success(self):
        """Test RetryableTask with immediate success."""
        async def successful_operation():
            return "immediate success"

        task = RetryableTask(successful_operation(), max_attempts=5, delay=0.01)
        result = await task.execute()

        assert result == "immediate success"
        assert task.attempt == 1
        assert task.success is True


class TestErrorHandling:
    """Test error handling in utils."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_none_return(self):
        """Test circuit breaker with functions returning None."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        @cb
        async def operation():
            return None

        result = await operation()
        assert result is None
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_retry_with_none_return(self):
        """Test retry with functions returning None."""
        attempts = 0

        @retry(max_attempts=2, delay=0.01)
        async def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Error")
            return None

        result = await operation()
        assert result is None
        assert attempts == 2


class CustomException(Exception):
    """Custom exception for testing."""

    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
