"""Prometheus Metrics Exporter for Legion AI System.

Provides real-time performance monitoring via Prometheus protocol.
"""

import asyncio
import logging
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY
import psutil
import os

logger = logging.getLogger(__name__)


class LegionPrometheusExporter:
    """
    Prometheus metrics exporter for Legion AI System.
    
    Exports performance metrics on HTTP endpoint for Prometheus scraping.
    
    Metrics:
    - legion_tasks_total: Total tasks processed (Counter)
    - legion_execution_duration_seconds: Task execution time (Histogram)
    - legion_cache_hit_rate: Cache hit rate percentage (Gauge)
    - legion_active_agents: Number of active agents (Gauge)
    - legion_async_tasks_total: Total async tasks processed (Counter)
    - legion_memory_usage_bytes: Memory usage in bytes (Gauge)
    
    Args:
        core: LegionCore instance
        port: HTTP port for metrics endpoint (default: 8000)
        update_interval: Metrics update interval in seconds (default: 15)
    """
    
    def __init__(self, core, port: int = 8000, update_interval: int = 15):
        self.core = core
        self.port = port
        self.update_interval = update_interval
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        self._process = psutil.Process(os.getpid())
        
        # Initialize metrics
        self._init_metrics()
        
        logger.info(f"PrometheusExporter initialized on port {port}")
    
    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        
        # Counter: Total tasks processed
        self.task_counter = Counter(
            'legion_tasks_total',
            'Total number of tasks processed',
            ['agent_type', 'status']
        )
        
        # Histogram: Task execution duration
        self.execution_time = Histogram(
            'legion_execution_duration_seconds',
            'Task execution duration in seconds',
            ['agent_type'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        # Gauge: Cache hit rate
        self.cache_hit_rate = Gauge(
            'legion_cache_hit_rate',
            'Cache hit rate as percentage'
        )
        
        # Gauge: Active agents count
        self.active_agents = Gauge(
            'legion_active_agents',
            'Number of currently active agents'
        )
        
        # Counter: Async tasks processed
        self.async_tasks_counter = Counter(
            'legion_async_tasks_total',
            'Total number of async tasks processed',
            ['agent_type']
        )
        
        # Gauge: Memory usage
        self.memory_usage = Gauge(
            'legion_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        # Gauge: Cache size
        self.hot_cache_size = Gauge(
            'legion_hot_cache_size',
            'Number of items in hot cache'
        )
        
        self.cold_cache_size = Gauge(
            'legion_cold_cache_size',
            'Number of items in cold cache'
        )
        
        # Gauge: Worker pool status
        self.worker_count = Gauge(
            'legion_worker_count',
            'Number of active worker tasks'
        )
        
        self.queue_size = Gauge(
            'legion_task_queue_size',
            'Current task queue size'
        )
        
        logger.info("Prometheus metrics initialized")
    
    async def start(self):
        """Start metrics exporter HTTP server and update loop."""
        if self._running:
            logger.warning("PrometheusExporter already running")
            return
        
        try:
            # Start HTTP server
            start_http_server(self.port)
            logger.info(f"✅ Prometheus metrics server started on http://0.0.0.0:{self.port}/metrics")
            
            self._running = True
            
            # Start update loop
            self._update_task = asyncio.create_task(self._update_loop())
            
        except Exception as e:
            logger.error(f"Failed to start Prometheus exporter: {e}")
            raise
    
    async def stop(self):
        """Stop metrics exporter."""
        if not self._running:
            return
        
        logger.info("Stopping PrometheusExporter...")
        self._running = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("PrometheusExporter stopped")
    
    async def _update_loop(self):
        """Continuously update metrics from LegionCore."""
        logger.info(f"Metrics update loop started (interval: {self.update_interval}s)")
        
        while self._running:
            try:
                await self._update_metrics()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _update_metrics(self):
        """Update all metrics from current core state."""
        try:
            # Get metrics from core
            core_metrics = self.core.get_metrics()
            
            # Update cache hit rate
            cache_hits = core_metrics.get('cache_hits', 0)
            cache_misses = core_metrics.get('cache_misses', 0)
            total_cache_requests = cache_hits + cache_misses
            
            if total_cache_requests > 0:
                hit_rate = (cache_hits / total_cache_requests) * 100
                self.cache_hit_rate.set(hit_rate)
            
            # Update active agents
            agent_calls = core_metrics.get('agent_calls', {})
            self.active_agents.set(len(agent_calls))
            
            # Update memory usage
            memory_info = self._process.memory_info()
            self.memory_usage.set(memory_info.rss)
            
            # Update cache sizes
            if hasattr(self.core, 'cache'):
                self.hot_cache_size.set(len(self.core.cache.hot_cache))
                self.cold_cache_size.set(len(self.core.cache.cold_cache))
            
            # Update worker pool stats
            if hasattr(self.core, '_worker_tasks'):
                self.worker_count.set(len(self.core._worker_tasks))
            
            if hasattr(self.core, '_task_queue'):
                self.queue_size.set(self.core._task_queue.qsize())
            
            # Log periodic summary
            logger.debug(
                f"Metrics updated - Agents: {len(agent_calls)}, "
                f"Cache hit rate: {hit_rate:.1f}%, "
                f"Memory: {memory_info.rss / 1024 / 1024:.1f}MB"
            )
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def record_task_completion(self, agent_type: str, duration: float, status: str = 'success'):
        """Record task completion metrics.
        
        Args:
            agent_type: Type of agent that executed the task
            duration: Execution duration in seconds
            status: Task status (success/failed)
        """
        self.task_counter.labels(agent_type=agent_type, status=status).inc()
        self.execution_time.labels(agent_type=agent_type).observe(duration)
    
    def record_async_task(self, agent_type: str):
        """Record async task execution.
        
        Args:
            agent_type: Type of agent that executed the task
        """
        self.async_tasks_counter.labels(agent_type=agent_type).inc()
    
    def get_metrics_summary(self) -> dict:
        """Get current metrics summary.
        
        Returns:
            Dictionary with current metric values
        """
        core_metrics = self.core.get_metrics()
        memory_info = self._process.memory_info()
        
        cache_hits = core_metrics.get('cache_hits', 0)
        cache_misses = core_metrics.get('cache_misses', 0)
        total = cache_hits + cache_misses
        hit_rate = (cache_hits / total * 100) if total > 0 else 0
        
        return {
            'active_agents': len(core_metrics.get('agent_calls', {})),
            'cache_hit_rate_percent': hit_rate,
            'memory_usage_mb': memory_info.rss / 1024 / 1024,
            'hot_cache_size': len(self.core.cache.hot_cache) if hasattr(self.core, 'cache') else 0,
            'cold_cache_size': len(self.core.cache.cold_cache) if hasattr(self.core, 'cache') else 0,
            'worker_count': len(self.core._worker_tasks) if hasattr(self.core, '_worker_tasks') else 0,
            'queue_size': self.core._task_queue.qsize() if hasattr(self.core, '_task_queue') else 0
        }


async def main():
    """Test Prometheus exporter standalone."""
    from legion.core import LegionCore
    
    print("Starting Legion Prometheus Exporter Test...")
    
    # Create core
    core = LegionCore({'num_workers': 4})
    await core.start()
    
    # Start exporter
    exporter = LegionPrometheusExporter(core, port=8000, update_interval=5)
    await exporter.start()
    
    print(f"\n✅ Metrics available at: http://localhost:8000/metrics")
    print("\nPress Ctrl+C to stop...\n")
    
    try:
        # Run for 60 seconds
        for i in range(12):
            await asyncio.sleep(5)
            summary = exporter.get_metrics_summary()
            print(f"[{i*5}s] Agents: {summary['active_agents']}, "
                  f"Cache hit rate: {summary['cache_hit_rate_percent']:.1f}%, "
                  f"Memory: {summary['memory_usage_mb']:.1f}MB")
    
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        await exporter.stop()
        await core.stop()
        print("✅ Stopped successfully")


if __name__ == '__main__':
    asyncio.run(main())
