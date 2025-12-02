"""Unit tests for rate limiter module."""

import pytest
import time
import asyncio
from unittest.mock import patch

from src.legion.utils.rate_limiter import (
    RateLimit,
    RateLimitExceeded,
    TokenBucketLimiter,
    SlidingWindowLimiter,
    rate_limit,
    async_rate_limit
)


class TestRateLimit:
    """Test RateLimit dataclass."""
    
    def test_valid_config(self):
        """Test valid rate limit configuration."""
        rl = RateLimit(calls=10, period=1.0)
        assert rl.calls == 10
        assert rl.period == 1.0
    
    def test_invalid_calls(self):
        """Test invalid calls raises ValueError."""
        with pytest.raises(ValueError, match="calls must be positive"):
            RateLimit(calls=0, period=1.0)
        
        with pytest.raises(ValueError, match="calls must be positive"):
            RateLimit(calls=-1, period=1.0)
    
    def test_invalid_period(self):
        """Test invalid period raises ValueError."""
        with pytest.raises(ValueError, match="period must be positive"):
            RateLimit(calls=10, period=0)
        
        with pytest.raises(ValueError, match="period must be positive"):
            RateLimit(calls=10, period=-1.0)


class TestTokenBucketLimiter:
    """Test TokenBucketLimiter class."""
    
    def test_init(self):
        """Test initialization."""
        rl = RateLimit(calls=10, period=1.0)
        limiter = TokenBucketLimiter(rl)
        
        assert limiter.rate_limit == rl
        assert limiter.tokens == 10.0
    
    def test_allow_within_limit(self):
        """Test allow() returns True when under limit."""
        limiter = TokenBucketLimiter(RateLimit(calls=10, period=1.0))
        
        for _ in range(10):
            assert limiter.allow() is True
    
    def test_allow_exceeds_limit(self):
        """Test allow() returns False when over limit."""
        limiter = TokenBucketLimiter(RateLimit(calls=2, period=1.0))
        
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False  # Over limit
    
    def test_token_refill(self):
        """Test tokens refill over time."""
        limiter = TokenBucketLimiter(RateLimit(calls=2, period=1.0))
        
        # Use all tokens
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False
        
        # Wait for refill
        time.sleep(0.6)  # Half the period
        assert limiter.allow() is True  # Should have ~1 token
        assert limiter.allow() is False  # Back to 0
    
    def test_wait_time_no_wait(self):
        """Test wait_time() returns 0 when action allowed."""
        limiter = TokenBucketLimiter(RateLimit(calls=10, period=1.0))
        assert limiter.wait_time() == 0.0
    
    def test_wait_time_needs_wait(self):
        """Test wait_time() returns positive value when limit exceeded."""
        limiter = TokenBucketLimiter(RateLimit(calls=1, period=1.0))
        
        limiter.allow()  # Use token
        wait = limiter.wait_time()
        assert wait > 0
        assert wait <= 1.0
    
    def test_thread_safety(self):
        """Test token bucket is thread-safe."""
        import threading
        
        limiter = TokenBucketLimiter(RateLimit(calls=100, period=1.0))
        results = []
        
        def worker():
            for _ in range(10):
                results.append(limiter.allow())
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have exactly 100 True results
        assert sum(results) == 100
        assert len(results) == 100


class TestSlidingWindowLimiter:
    """Test SlidingWindowLimiter class."""
    
    def test_init(self):
        """Test initialization."""
        rl = RateLimit(calls=10, period=1.0)
        limiter = SlidingWindowLimiter(rl)
        assert limiter.rate_limit == rl
    
    def test_allow_within_limit(self):
        """Test allow() returns True when under limit."""
        limiter = SlidingWindowLimiter(RateLimit(calls=5, period=1.0))
        
        for _ in range(5):
            assert limiter.allow("user1") is True
    
    def test_allow_exceeds_limit(self):
        """Test allow() returns False when over limit."""
        limiter = SlidingWindowLimiter(RateLimit(calls=2, period=1.0))
        
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False
    
    def test_per_user_limits(self):
        """Test limits are per-user."""
        limiter = SlidingWindowLimiter(RateLimit(calls=2, period=1.0))
        
        # User1 uses all tokens
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False
        
        # User2 still has tokens
        assert limiter.allow("user2") is True
        assert limiter.allow("user2") is True
    
    def test_window_expiration(self):
        """Test old requests expire from window."""
        limiter = SlidingWindowLimiter(RateLimit(calls=2, period=0.5))
        
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False
        
        # Wait for window to expire
        time.sleep(0.6)
        
        # Should be allowed again
        assert limiter.allow("user1") is True
    
    def test_reset(self):
        """Test reset() clears window for user."""
        limiter = SlidingWindowLimiter(RateLimit(calls=2, period=1.0))
        
        limiter.allow("user1")
        limiter.allow("user1")
        assert limiter.allow("user1") is False
        
        limiter.reset("user1")
        assert limiter.allow("user1") is True


class TestRateLimitDecorator:
    """Test rate_limit decorator."""
    
    def test_function_allowed(self):
        """Test decorated function executes when allowed."""
        call_count = 0
        
        @rate_limit(calls=5, period=1.0)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        for _ in range(5):
            result = test_func()
            assert result == "success"
        
        assert call_count == 5
    
    def test_function_waits_on_limit(self):
        """Test decorated function waits when limit exceeded."""
        @rate_limit(calls=2, period=0.5, raise_on_limit=False)
        def test_func():
            return "success"
        
        start = time.time()
        
        test_func()  # 1st call - immediate
        test_func()  # 2nd call - immediate
        test_func()  # 3rd call - should wait ~0.25s
        
        duration = time.time() - start
        assert duration >= 0.2  # Should have waited
    
    def test_function_raises_on_limit(self):
        """Test decorated function raises when limit exceeded."""
        @rate_limit(calls=1, period=1.0, raise_on_limit=True)
        def test_func():
            return "success"
        
        test_func()  # OK
        
        with pytest.raises(RateLimitExceeded):
            test_func()  # Should raise


class TestAsyncRateLimitDecorator:
    """Test async_rate_limit decorator."""
    
    @pytest.mark.asyncio
    async def test_async_function_allowed(self):
        """Test decorated async function executes when allowed."""
        call_count = 0
        
        @async_rate_limit(calls=5, period=1.0)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        for _ in range(5):
            result = await test_func()
            assert result == "success"
        
        assert call_count == 5
    
    @pytest.mark.asyncio
    async def test_async_function_waits_on_limit(self):
        """Test decorated async function waits when limit exceeded."""
        @async_rate_limit(calls=2, period=0.5, raise_on_limit=False)
        async def test_func():
            return "success"
        
        start = time.time()
        
        await test_func()
        await test_func()
        await test_func()  # Should wait
        
        duration = time.time() - start
        assert duration >= 0.2
    
    @pytest.mark.asyncio
    async def test_async_function_raises_on_limit(self):
        """Test decorated async function raises when limit exceeded."""
        @async_rate_limit(calls=1, period=1.0, raise_on_limit=True)
        async def test_func():
            return "success"
        
        await test_func()
        
        with pytest.raises(RateLimitExceeded):
            await test_func()
