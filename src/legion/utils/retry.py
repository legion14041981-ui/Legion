"""
Retry mechanism with exponential backoff for Legion.

Automatically retries failed operations with configurable backoff.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type
import time

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch
        on_retry: Callback function called on each retry
    
    Example:
        @retry(max_attempts=5, delay=2.0, backoff=2.0)
        async def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                current_delay = delay
                last_exception = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt == max_attempts:
                            logger.error(
                                f"Function {func.__name__} failed after "
                                f"{max_attempts} attempts: {e}"
                            )
                            raise
                        
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt}/"
                            f"{max_attempts}): {e}. Retrying in {current_delay}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                
                # Should never reach here, but for type safety
                raise last_exception
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                current_delay = delay
                last_exception = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt == max_attempts:
                            logger.error(
                                f"Function {func.__name__} failed after "
                                f"{max_attempts} attempts: {e}"
                            )
                            raise
                        
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt}/"
                            f"{max_attempts}): {e}. Retrying in {current_delay}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                
                # Should never reach here, but for type safety
                raise last_exception
            
            return sync_wrapper
    
    return decorator


class RetryableTask:
    """
    Wrapper for retryable tasks with state tracking.
    
    Useful when you need more control over retry logic.
    """
    
    def __init__(
        self,
        func: Callable,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0
    ):
        """
        Initialize retryable task.
        
        Args:
            func: Function to execute
            max_attempts: Maximum attempts
            delay: Initial delay
            backoff: Backoff multiplier
        """
        self.func = func
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
        
        self.attempts = 0
        self.last_error: Optional[Exception] = None
        self.success = False
    
    async def execute_async(self, *args, **kwargs) -> Any:
        """Execute async task with retry logic."""
        current_delay = self.delay
        
        for attempt in range(1, self.max_attempts + 1):
            self.attempts = attempt
            
            try:
                result = await self.func(*args, **kwargs)
                self.success = True
                return result
            except Exception as e:
                self.last_error = e
                
                if attempt == self.max_attempts:
                    raise
                
                logger.warning(
                    f"Task failed (attempt {attempt}/{self.max_attempts}): {e}"
                )
                await asyncio.sleep(current_delay)
                current_delay *= self.backoff
    
    def execute(self, *args, **kwargs) -> Any:
        """Execute sync task with retry logic."""
        current_delay = self.delay
        
        for attempt in range(1, self.max_attempts + 1):
            self.attempts = attempt
            
            try:
                result = self.func(*args, **kwargs)
                self.success = True
                return result
            except Exception as e:
                self.last_error = e
                
                if attempt == self.max_attempts:
                    raise
                
                logger.warning(
                    f"Task failed (attempt {attempt}/{self.max_attempts}): {e}"
                )
                time.sleep(current_delay)
                current_delay *= self.backoff
