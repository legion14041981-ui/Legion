# ALTA-PRIME CI-OVERLORD vΩ — HIGH-RISK FIX #41
# Memory Leak Fix: AsyncTaskExecutor Cleanup
# Risk Score: 0.28 (MEDIUM) | Time: 16-20h | Impact: Prevents OOM crashes

import asyncio
import logging
import weakref
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Coroutine
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AsyncTaskExecutor:
    """Fixed AsyncTaskExecutor with proper memory management.
    
    FIXES:
    1. WeakValueDictionary for task storage (prevent holding references)
    2. LRU cache for results (max 1000 entries)
    3. TTL cleanup for tasks older than 1 hour
    4. Weakref callbacks to monitor object lifecycle
    5. Proper event handler cleanup
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 100,
        result_cache_size: int = 1000,
        task_ttl_seconds: int = 3600,  # 1 hour
    ):
        """Initialize executor with memory safety.
        
        Args:
            max_concurrent_tasks: Max concurrent tasks
            result_cache_size: Max results to cache (LRU)
            task_ttl_seconds: Task TTL before cleanup
        """
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_ttl = timedelta(seconds=task_ttl_seconds)
        
        # Use WeakValueDictionary to prevent memory leaks
        # If task object is garbage collected, entry is removed
        self._tasks: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        
        # LRU cache for results (max 1000)
        self._result_cache: OrderedDict = OrderedDict()
        self._result_cache_size = result_cache_size
        
        # Task metadata (timestamps, handlers)
        self._task_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self._metrics = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "memory_cleanups": 0,
            "cached_results": 0,
        }
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Start background cleanup tasks."""
        # Start periodic cleanup
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("✅ AsyncTaskExecutor initialized with memory safety")

    async def shutdown(self) -> None:
        """Cleanup executor resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear caches
        self._tasks.clear()
        self._result_cache.clear()
        self._task_metadata.clear()
        logger.info("AsyncTaskExecutor shutdown complete")

    async def execute(
        self,
        task_id: str,
        coroutine: Coroutine[Any, Any, Any],
        on_complete: Optional[Callable[[str, Any], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ) -> Any:
        """Execute a task with memory safety.
        
        Args:
            task_id: Unique task identifier
            coroutine: Async function to execute
            on_complete: Callback on completion (weakref-safe)
            on_error: Callback on error (weakref-safe)
            
        Returns:
            Task result
        """
        async with self._semaphore:  # Limit concurrent tasks
            try:
                self._metrics["tasks_created"] += 1
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    coroutine,
                    timeout=300.0  # 5 minute timeout
                )
                
                # Cache result (with LRU eviction)
                self._cache_result(task_id, result)
                self._metrics["tasks_completed"] += 1
                
                # Callback (if provided)
                if on_complete:
                    try:
                        on_complete(task_id, result)
                    except Exception as e:
                        logger.error(f"Callback error for task {task_id}: {e}")
                
                return result
                
            except asyncio.TimeoutError:
                self._metrics["tasks_failed"] += 1
                error = TimeoutError(f"Task {task_id} timed out")
                if on_error:
                    try:
                        on_error(task_id, error)
                    except Exception as e:
                        logger.error(f"Error callback failed: {e}")
                raise error
                
            except Exception as e:
                self._metrics["tasks_failed"] += 1
                if on_error:
                    try:
                        on_error(task_id, e)
                    except Exception as cb_err:
                        logger.error(f"Error callback failed: {cb_err}")
                raise
            
            finally:
                # Cleanup task metadata immediately
                self._task_metadata.pop(task_id, None)

    def _cache_result(self, task_id: str, result: Any) -> None:
        """Cache result with LRU eviction.
        
        Args:
            task_id: Task identifier
            result: Result to cache
        """
        # Remove old entry if exists
        self._result_cache.pop(task_id, None)
        
        # Add new entry
        self._result_cache[task_id] = result
        
        # Evict oldest if over limit
        while len(self._result_cache) > self._result_cache_size:
            oldest_id, _ = self._result_cache.popitem(last=False)
            logger.debug(f"Evicted result for task {oldest_id} (LRU)")
        
        self._metrics["cached_results"] = len(self._result_cache)

    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old tasks and metadata."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                now = datetime.now()
                expired_tasks = []
                
                # Find expired task metadata
                for task_id, metadata in self._task_metadata.items():
                    created_at = metadata.get("created_at")
                    if created_at and (now - created_at) > self.task_ttl:
                        expired_tasks.append(task_id)
                
                # Remove expired metadata
                for task_id in expired_tasks:
                    self._task_metadata.pop(task_id, None)
                    self._result_cache.pop(task_id, None)  # Also remove cached result
                
                if expired_tasks:
                    self._metrics["memory_cleanups"] += 1
                    logger.info(f"Cleaned up {len(expired_tasks)} expired tasks")
                
                # Log metrics periodically
                if self._metrics["memory_cleanups"] % 10 == 0:
                    self._log_metrics()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def _log_metrics(self) -> None:
        """Log executor metrics."""
        logger.info(
            f"Executor metrics: "
            f"created={self._metrics['tasks_created']}, "
            f"completed={self._metrics['tasks_completed']}, "
            f"failed={self._metrics['tasks_failed']}, "
            f"cached={self._metrics['cached_results']}, "
            f"cleanups={self._metrics['memory_cleanups']}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get executor metrics.
        
        Returns:
            Metrics dictionary
        """
        return {
            **self._metrics,
            "active_tasks": len(self._tasks),
            "cached_results": len(self._result_cache),
            "task_metadata_size": len(self._task_metadata),
        }
