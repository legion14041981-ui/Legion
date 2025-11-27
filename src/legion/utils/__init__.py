"""
Legion Utilities Module.

Provides reusable utilities for agents and orchestration:
- Circuit Breaker pattern
- Retry mechanism with exponential backoff
- Timeout management
- Error handling helpers

Version: 2.3.0
"""

try:
    from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, circuit_breaker
    from .retry import retry, RetryableTask
    
    __all__ = [
        'CircuitBreaker',
        'CircuitBreakerOpenError',
        'circuit_breaker',
        'retry',
        'RetryableTask'
    ]
except ImportError as e:
    # Грациозная обработка если модули не доступны
    import logging
    logging.getLogger(__name__).warning(f"Some utilities not available: {e}")
    __all__ = []

__version__ = "2.3.0"
