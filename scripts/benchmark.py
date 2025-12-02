#!/usr/bin/env python3
"""Performance benchmarking script for Legion Framework.

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --tasks 10000 --agents 10
"""

import argparse
import asyncio
import time
import statistics
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion.core import LegionCore
from legion.base_agent import LegionAgent


class BenchmarkAgent(LegionAgent):
    """Simple agent for benchmarking."""
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task."""
        # Simulate work
        time.sleep(0.001)
        return {'status': 'completed', 'result': 'success'}
    
    async def execute_async(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task asynchronously."""
        await asyncio.sleep(0.001)
        return {'status': 'completed', 'result': 'success'}


def benchmark_sync_dispatch(core: LegionCore, num_tasks: int) -> Dict[str, float]:
    """Benchmark synchronous task dispatching.
    
    Args:
        core: LegionCore instance
        num_tasks: Number of tasks to dispatch
    
    Returns:
        Dict with timing statistics
    """
    print(f"\n🏃 Running sync benchmark ({num_tasks} tasks)...")
    
    timings = []
    
    for i in range(num_tasks):
        start = time.perf_counter()
        core.dispatch_task(
            f"task_{i}",
            {"type": "test", "data": f"task_{i}"},
            required_capability="benchmark"
        )
        duration = time.perf_counter() - start
        timings.append(duration)
    
    return {
        'mean': statistics.mean(timings),
        'median': statistics.median(timings),
        'min': min(timings),
        'max': max(timings),
        'stdev': statistics.stdev(timings) if len(timings) > 1 else 0
    }


async def benchmark_async_dispatch(core: LegionCore, num_tasks: int) -> Dict[str, float]:
    """Benchmark asynchronous task dispatching.
    
    Args:
        core: LegionCore instance
        num_tasks: Number of tasks to dispatch
    
    Returns:
        Dict with timing statistics
    """
    print(f"\n⚡ Running async benchmark ({num_tasks} tasks)...")
    
    timings = []
    
    for i in range(num_tasks):
        start = time.perf_counter()
        await core.dispatch_task_async(
            f"task_{i}",
            {"type": "test", "data": f"task_{i}"},
            required_capability="benchmark"
        )
        duration = time.perf_counter() - start
        timings.append(duration)
    
    return {
        'mean': statistics.mean(timings),
        'median': statistics.median(timings),
        'min': min(timings),
        'max': max(timings),
        'stdev': statistics.stdev(timings) if len(timings) > 1 else 0
    }


def print_results(label: str, stats: Dict[str, float]) -> None:
    """Print benchmark results.
    
    Args:
        label: Benchmark label
        stats: Timing statistics
    """
    print(f"\n📊 {label} Results:")
    print(f"  Mean:   {stats['mean']*1000:.2f} ms")
    print(f"  Median: {stats['median']*1000:.2f} ms")
    print(f"  Min:    {stats['min']*1000:.2f} ms")
    print(f"  Max:    {stats['max']*1000:.2f} ms")
    print(f"  StdDev: {stats['stdev']*1000:.2f} ms")
    print(f"  Rate:   {1/stats['mean']:.0f} tasks/sec")


async def main():
    """Run benchmarks."""
    parser = argparse.ArgumentParser(description='Benchmark Legion Framework')
    parser.add_argument('--tasks', type=int, default=1000, help='Number of tasks')
    parser.add_argument('--agents', type=int, default=5, help='Number of agents')
    args = parser.parse_args()
    
    print("="*80)
    print("🏁 Legion Framework Benchmarks")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Tasks: {args.tasks}")
    print(f"  Agents: {args.agents}")
    
    # Initialize core
    core = LegionCore()
    
    # Register agents
    print(f"\n🤖 Registering {args.agents} agents...")
    for i in range(args.agents):
        agent = BenchmarkAgent(f"agent_{i}")
        core.register_agent(f"agent_{i}", agent, capabilities=["benchmark"])
    
    core.start()
    
    try:
        # Sync benchmark
        sync_stats = benchmark_sync_dispatch(core, args.tasks)
        print_results("Synchronous Dispatch", sync_stats)
        
        # Async benchmark
        async_stats = await benchmark_async_dispatch(core, args.tasks)
        print_results("Asynchronous Dispatch", async_stats)
        
        # Comparison
        speedup = sync_stats['mean'] / async_stats['mean']
        print(f"\n🚀 Async speedup: {speedup:.2f}x faster")
        
        # Metrics
        metrics = core.get_metrics()
        print(f"\n📊 Final Metrics:")
        print(f"  Total agents: {metrics.get('total_agents', 0)}")
        print(f"  Tasks dispatched: {metrics.get('tasks_dispatched', 0)}")
        print(f"  Tasks completed: {metrics.get('tasks_completed', 0)}")
        
    finally:
        core.stop()
    
    print("\n" + "="*80)
    print("✅ Benchmarks complete!")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(main())
