"""
Circuit Breaker Pattern Implementation for Legion.
Prevents cascading failures by stopping requests to failing services.
Implements three states: CLOSED, OPEN, HALF_OPEN.
"""
import logging
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
from functools import wraps
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service recovered
    
    Attributes:
        failure_threshold (int): Number of failures before opening
        timeout (int): Seconds to wait before trying again
        expected_exception (Exception): Exception type to catch
    """
    
    # Keep string constants for backward compatibility
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        # Use enum for state (tests expect CircuitBreakerState enum)
        self.state = CircuitBreakerState.CLOSED
        
        logger.info(
            f"Circuit breaker initialized: threshold={failure_threshold}, "
            f"timeout={timeout}s"
        )
    
    def __call__(self, func: Callable) -> Callable:
        """
        Make CircuitBreaker callable as a decorator.
        
        This allows using CircuitBreaker instances like:
            cb = CircuitBreaker()
            @cb
            async def my_function():
                pass
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function
        """
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return sync_wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. "
                    f"Will retry after {self.timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. "
                    f"Will retry after {self.timeout}s"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker recovered, transitioning to CLOSED")
            self.state = CircuitBreakerState.CLOSED
        
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker threshold reached ({self.failure_count}), "
                f"transitioning to OPEN"
            )
            self.state = CircuitBreakerState.OPEN
    
    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": (
                self.last_failure_time.isoformat() 
                if self.last_failure_time else None
            )
        }


def circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        failure_threshold: Failures before opening
        timeout: Seconds before retry
        expected_exception: Exception type to catch
    
    Example:
        @circuit_breaker(failure_threshold=3, timeout=30)
        async def risky_operation():
            # Your code here
            pass
    """
    breaker = CircuitBreaker(failure_threshold, timeout, expected_exception)
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator
