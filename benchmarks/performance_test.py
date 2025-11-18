"""Performance Benchmarks for Legion AI System v2.1.

Tests async/await optimizations and validates 10-30x speedup claims.
"""

import asyncio
import time
import statistics
import json
from typing import Dict, Any, List
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legion.core import LegionCore


class BenchmarkAgent:
    """Mock agent for benchmarking."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.config = {'type': 'benchmark'}
    
    async def execute_async(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate async I/O operation."""
        await asyncio.sleep(0.01)  # 10ms simulated I/O
        return {
            'status': 'completed',
            'agent_id': self.agent_id,
            'task': task
        }
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous fallback."""
        time.sleep(0.01)
        return {
            'status': 'completed',
            'agent_id': self.agent_id,
            'task': task
        }


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite."""
    
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.results: Dict[str, Any] = {}
    
    async def benchmark_sequential_registration(self) -> float:
        """Benchmark sequential agent registration (old method)."""
        core = LegionCore()
        agents = [BenchmarkAgent(f"seq_agent_{i}") for i in range(self.num_agents)]
        
        start = time.perf_counter()
        for agent in agents:
            await core.register_agent(agent.agent_id, agent)
        duration = time.perf_counter() - start
        
        return duration
    
    async def benchmark_parallel_registration(self) -> float:
        """Benchmark parallel batch registration (new method)."""
        core = LegionCore()
        agents = {f"par_agent_{i}": BenchmarkAgent(f"par_agent_{i}") 
                  for i in range(self.num_agents)}
        
        start = time.perf_counter()
        await core.register_agents_batch(agents)
        duration = time.perf_counter() - start
        
        return duration
    
    async def benchmark_cache_performance(self) -> Dict[str, Any]:
        """Benchmark cache hit rates and access times."""
        core = LegionCore({'hot_cache_size': 128})
        
        # Register agents
        agents = {f"cache_agent_{i}": BenchmarkAgent(f"cache_agent_{i}") 
                  for i in range(self.num_agents)}
        await core.register_agents_batch(agents)
        
        # Benchmark cache access
        total_requests = 1000
        access_times: List[float] = []
        
        for i in range(total_requests):
            agent_id = f"cache_agent_{i % self.num_agents}"
            
            start = time.perf_counter()
            agent = await core.get_agent_cached(agent_id)
            duration = time.perf_counter() - start
            
            access_times.append(duration * 1000)  # Convert to ms
        
        metrics = core.get_metrics()
        
        return {
            'total_requests': total_requests,
            'cache_hits': metrics['cache_hits'],
            'cache_misses': metrics['cache_misses'],
            'cache_hit_rate': float(metrics['cache_hit_rate'].rstrip('%')),
            'avg_access_time_ms': statistics.mean(access_times),
            'min_access_time_ms': min(access_times),
            'max_access_time_ms': max(access_times),
            'p95_access_time_ms': statistics.quantiles(access_times, n=20)[18]
        }
    
    async def benchmark_parallel_dispatch(self) -> float:
        """Benchmark parallel task dispatching."""
        core = LegionCore({'num_workers': 4})
        await core.start()
        
        # Register test agent
        agent = BenchmarkAgent('dispatch_agent')
        await core.register_agent('dispatch_agent', agent)
        
        # Create tasks
        tasks = [
            {
                'task_id': f'task_{i}',
                'task_data': {
                    'agent_id': 'dispatch_agent',
                    'action': 'test',
                    'index': i
                }
            }
            for i in range(50)
        ]
        
        start = time.perf_counter()
        await core.dispatch_tasks_parallel(tasks)
        duration = time.perf_counter() - start
        
        await core.stop()
        
        return duration
    
    async def benchmark_memory_usage(self) -> Dict[str, float]:
        """Benchmark memory usage optimization."""
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        baseline_mb = process.memory_info().rss / 1024 / 1024
        
        # Create core with agents
        core = LegionCore()
        agents = {f"mem_agent_{i}": BenchmarkAgent(f"mem_agent_{i}") 
                  for i in range(200)}
        await core.register_agents_batch(agents)
        
        # Memory with agents
        gc.collect()
        with_agents_mb = process.memory_info().rss / 1024 / 1024
        
        # Trigger cache cleanup
        await core.cache.cleanup_expired()
        gc.collect()
        after_cleanup_mb = process.memory_info().rss / 1024 / 1024
        
        return {
            'baseline_mb': baseline_mb,
            'with_agents_mb': with_agents_mb,
            'after_cleanup_mb': after_cleanup_mb,
            'memory_increase_mb': with_agents_mb - baseline_mb,
            'memory_recovered_mb': with_agents_mb - after_cleanup_mb,
            'per_agent_kb': (with_agents_mb - baseline_mb) * 1024 / 200
        }
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and collect results."""
        print("\n" + "="*60)
        print("Legion AI System v2.1 - Performance Benchmarks")
        print("="*60)
        
        # 1. Registration benchmarks
        print("\n[1/5] Running sequential registration benchmark...")
        seq_time = await self.benchmark_sequential_registration()
        print(f"  ✓ Completed in {seq_time*1000:.2f}ms")
        
        print("\n[2/5] Running parallel registration benchmark...")
        par_time = await self.benchmark_parallel_registration()
        print(f"  ✓ Completed in {par_time*1000:.2f}ms")
        
        speedup = seq_time / par_time if par_time > 0 else 0
        print(f"  ✓ Speedup factor: {speedup:.2f}x")
        
        # 2. Cache performance
        print("\n[3/5] Running cache performance benchmark...")
        cache_results = await self.benchmark_cache_performance()
        print(f"  ✓ Cache hit rate: {cache_results['cache_hit_rate']:.1f}%")
        print(f"  ✓ Average access time: {cache_results['avg_access_time_ms']:.3f}ms")
        
        # 3. Parallel dispatch
        print("\n[4/5] Running parallel dispatch benchmark...")
        dispatch_time = await self.benchmark_parallel_dispatch()
        print(f"  ✓ Completed 50 tasks in {dispatch_time*1000:.2f}ms")
        print(f"  ✓ Average per task: {dispatch_time*1000/50:.2f}ms")
        
        # 4. Memory usage
        print("\n[5/5] Running memory usage benchmark...")
        memory_results = await self.benchmark_memory_usage()
        print(f"  ✓ Memory per agent: {memory_results['per_agent_kb']:.2f}KB")
        print(f"  ✓ Memory recovered: {memory_results['memory_recovered_mb']:.2f}MB")
        
        # Compile results
        self.results = {
            'metadata': {
                'num_agents': self.num_agents,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'python_version': sys.version
            },
            'registration': {
                'sequential_ms': seq_time * 1000,
                'parallel_ms': par_time * 1000,
                'speedup_factor': speedup
            },
            'cache': cache_results,
            'dispatch': {
                'total_tasks': 50,
                'total_time_ms': dispatch_time * 1000,
                'avg_per_task_ms': dispatch_time * 1000 / 50
            },
            'memory': memory_results,
            'summary': {
                'registration_speedup': f"{speedup:.2f}x",
                'cache_hit_rate': f"{cache_results['cache_hit_rate']:.1f}%",
                'avg_access_time': f"{cache_results['avg_access_time_ms']:.3f}ms",
                'memory_per_agent': f"{memory_results['per_agent_kb']:.2f}KB"
            }
        }
        
        return self.results
    
    def save_results(self, filename: str = 'benchmark_results.json'):
        """Save benchmark results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to {filename}")
    
    def print_summary(self):
        """Print formatted summary."""
        print("\n" + "="*60)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*60)
        
        reg = self.results['registration']
        print(f"\n📊 Registration Performance:")
        print(f"  Sequential: {reg['sequential_ms']:.2f}ms")
        print(f"  Parallel: {reg['parallel_ms']:.2f}ms")
        print(f"  Speedup: {reg['speedup_factor']:.2f}x {'✅' if reg['speedup_factor'] >= 10 else '⚠️'}")
        
        cache = self.results['cache']
        print(f"\n💾 Cache Performance:")
        print(f"  Hit rate: {cache['cache_hit_rate']:.1f}% {'✅' if cache['cache_hit_rate'] >= 95 else '⚠️'}")
        print(f"  Avg access: {cache['avg_access_time_ms']:.3f}ms {'✅' if cache['avg_access_time_ms'] < 1 else '⚠️'}")
        print(f"  P95 access: {cache['p95_access_time_ms']:.3f}ms")
        
        dispatch = self.results['dispatch']
        print(f"\n⚡ Parallel Dispatch:")
        print(f"  Total time: {dispatch['total_time_ms']:.2f}ms")
        print(f"  Per task: {dispatch['avg_per_task_ms']:.2f}ms")
        
        memory = self.results['memory']
        print(f"\n🧠 Memory Optimization:")
        print(f"  Per agent: {memory['per_agent_kb']:.2f}KB")
        print(f"  Total increase: {memory['memory_increase_mb']:.2f}MB")
        print(f"  Recovered: {memory['memory_recovered_mb']:.2f}MB")
        
        print("\n" + "="*60)
        print("✅ All benchmarks completed successfully!")
        print("="*60 + "\n")


async def main():
    """Main benchmark execution."""
    benchmark = PerformanceBenchmark(num_agents=100)
    
    try:
        await benchmark.run_all_benchmarks()
        benchmark.print_summary()
        benchmark.save_results()
        
        # Validation
        reg = benchmark.results['registration']
        cache = benchmark.results['cache']
        
        if reg['speedup_factor'] >= 10 and cache['cache_hit_rate'] >= 95:
            print("\n🎉 VALIDATION PASSED: 10-30x speedup confirmed!")
            return 0
        else:
            print("\n⚠️  VALIDATION WARNING: Performance below targets")
            return 1
            
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
