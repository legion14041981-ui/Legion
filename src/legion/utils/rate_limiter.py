"""Rate limiting utilities for Legion Framework.

Provides decorators and classes for:
- Function call rate limiting
- Token bucket algorithm
- Sliding window rate limiting
- Per-user/per-endpoint limits
"""

import time
import logging
from functools import wraps
from typing import Dict, Optional, Callable, Any
from collections import deque
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


@dataclass
class RateLimit:
    """Rate limit configuration."""
    
    calls: int  # Number of calls allowed
    period: float  # Time period in seconds
    
    def __post_init__(self):
        """Validate configuration."""
        if self.calls <= 0:
            raise ValueError("calls must be positive")
        if self.period <= 0:
            raise ValueError("period must be positive")


class TokenBucketLimiter:
    """Token bucket rate limiter.
    
    Example:
        >>> limiter = TokenBucketLimiter(rate_limit=RateLimit(calls=10, period=1.0))
        >>> if limiter.allow():
        ...     # Perform action
        ...     pass
    """
    
    def __init__(self, rate_limit: RateLimit):
        """Initialize token bucket.
        
        Args:
            rate_limit: Rate limit configuration
        """
        self.rate_limit = rate_limit
        self.tokens = float(rate_limit.calls)
        self.last_update = time.time()
        self._lock = Lock()
    
    def allow(self) -> bool:
        """Check if action is allowed under rate limit.
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            
            # Refill tokens based on time passed
            self.tokens = min(
                self.rate_limit.calls,
                self.tokens + time_passed * (self.rate_limit.calls / self.rate_limit.period)
            )
            self.last_update = now
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            
            return False
    
    def wait_time(self) -> float:
        """Get time to wait before next allowed action.
        
        Returns:
            Seconds to wait (0 if action is allowed now)
        """
        with self._lock:
            if self.tokens >= 1.0:
                return 0.0
            
            tokens_needed = 1.0 - self.tokens
            return tokens_needed * (self.rate_limit.period / self.rate_limit.calls)


class SlidingWindowLimiter:
    """Sliding window rate limiter.
    
    Example:
        >>> limiter = SlidingWindowLimiter(rate_limit=RateLimit(calls=100, period=60.0))
        >>> if limiter.allow(user_id="user123"):
        ...     # Perform action
        ...     pass
    """
    
    def __init__(self, rate_limit: RateLimit):
        """Initialize sliding window limiter.
        
        Args:
            rate_limit: Rate limit configuration
        """
        self.rate_limit = rate_limit
        self._windows: Dict[str, deque] = {}
        self._lock = Lock()
    
    def allow(self, key: str = "default") -> bool:
        """Check if action is allowed for given key.
        
        Args:
            key: Identifier (e.g., user_id, endpoint)
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self._lock:
            now = time.time()
            
            # Initialize window if needed
            if key not in self._windows:
                self._windows[key] = deque()
            
            window = self._windows[key]
            
            # Remove old timestamps outside window
            cutoff = now - self.rate_limit.period
            while window and window[0] < cutoff:
                window.popleft()
            
            # Check if under limit
            if len(window) < self.rate_limit.calls:
                window.append(now)
                return True
            
            return False
    
    def reset(self, key: str) -> None:
        """Reset rate limit for given key.
        
        Args:
            key: Identifier to reset
        """
        with self._lock:
            if key in self._windows:
                del self._windows[key]


def rate_limit(calls: int, period: float, raise_on_limit: bool = False):
    """Decorator for rate limiting function calls.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
        raise_on_limit: If True, raise RateLimitExceeded; if False, wait
    
    Example:
        >>> @rate_limit(calls=10, period=1.0)
        ... def my_function():
        ...     pass
    """
    limiter = TokenBucketLimiter(RateLimit(calls=calls, period=period))
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.allow():
                if raise_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded: {calls} calls per {period}s"
                    )
                else:
                    wait_time = limiter.wait_time()
                    logger.warning(
                        f"Rate limit hit for {func.__name__}, "
                        f"waiting {wait_time:.2f}s"
                    )
                    time.sleep(wait_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def async_rate_limit(calls: int, period: float, raise_on_limit: bool = False):
    """Async decorator for rate limiting.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
        raise_on_limit: If True, raise RateLimitExceeded; if False, wait
    
    Example:
        >>> @async_rate_limit(calls=10, period=1.0)
        ... async def my_async_function():
        ...     pass
    """
    import asyncio
    limiter = TokenBucketLimiter(RateLimit(calls=calls, period=period))
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not limiter.allow():
                if raise_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded: {calls} calls per {period}s"
                    )
                else:
                    wait_time = limiter.wait_time()
                    logger.warning(
                        f"Rate limit hit for {func.__name__}, "
                        f"waiting {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
