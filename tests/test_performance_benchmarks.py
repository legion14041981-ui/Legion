"""
Performance benchmarks for Legion framework.

Measures:
- Agent initialization time
- Task execution throughput
- Concurrent agent performance
- Memory usage
- Circuit breaker overhead
- Retry mechanism performance
"""

import pytest
import asyncio
import time
import psutil
import os
from typing import List

from legion.core import LegionCore
from legion.agents import DataAgent, EmailAgent
from legion.utils.circuit_breaker import CircuitBreaker
from legion.utils.retry import retry


class TestAgentPerformance:
    """Performance benchmarks for agent operations."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_agent_initialization_speed(self, benchmark):
        """Benchmark agent initialization time."""

        def create_agents():
            agents = []
            for i in range(100):
                agent = DataAgent(
                    agent_id=f"agent_{i}",
                    name=f"DataAgent{i}",
                    description="Benchmark agent",
                )
                agents.append(agent)
            return agents

        result = benchmark(create_agents)
        assert len(result) == 100

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_data_agent_throughput(self):
        """Measure data processing throughput."""
        agent = DataAgent(agent_id="throughput_test", name="ThroughputAgent", description="Test")

        # Generate test data
        test_data = [{"id": i, "value": i * 2} for i in range(1000)]

        start_time = time.time()

        # Process data
        result = await agent.execute(
            {
                "capability": "data_filter",
                "data": test_data,
                "options": {"filters": {}},  # No filtering, just processing
            }
        )

        end_time = time.time()
        duration = end_time - start_time

        assert result["success"] is True
        assert len(result["result"]) == 1000

        # Calculate throughput
        throughput = 1000 / duration
        print(f"\nData processing throughput: {throughput:.2f} items/sec")
        print(f"Total duration: {duration:.4f} sec")

        # Expect at least 10,000 items/sec (very conservative)
        assert throughput > 10000

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self):
        """Benchmark concurrent task execution."""
        num_agents = 10
        tasks_per_agent = 100

        # Create agents
        agents = [
            DataAgent(agent_id=f"concurrent_{i}", name=f"Agent{i}", description="Concurrent")
            for i in range(num_agents)
        ]

        test_data = [{"id": i} for i in range(100)]

        async def execute_tasks(agent):
            tasks = []
            for _ in range(tasks_per_agent):
                task = agent.execute({"capability": "data_filter", "data": test_data, "options": {"filters": {}}})
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            return results

        start_time = time.time()

        # Execute all agents concurrently
        all_results = await asyncio.gather(*[execute_tasks(agent) for agent in agents])

        end_time = time.time()
        duration = end_time - start_time

        total_tasks = num_agents * tasks_per_agent
        throughput = total_tasks / duration

        print(f"\nConcurrent execution:")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Duration: {duration:.2f} sec")
        print(f"  Throughput: {throughput:.2f} tasks/sec")

        # Verify all tasks succeeded
        for agent_results in all_results:
            assert all(r["success"] for r in agent_results)

        # Expect reasonable throughput
        assert throughput > 100


class TestCircuitBreakerPerformance:
    """Performance benchmarks for Circuit Breaker."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_circuit_breaker_overhead(self):
        """Measure Circuit Breaker overhead on successful operations."""
        iterations = 10000

        # Baseline: without circuit breaker
        async def baseline_operation():
            return "success"

        start_baseline = time.time()
        for _ in range(iterations):
            await baseline_operation()
        baseline_duration = time.time() - start_baseline

        # With circuit breaker
        cb = CircuitBreaker(failure_threshold=5, timeout=60)

        @cb
        async def protected_operation():
            return "success"

        start_protected = time.time()
        for _ in range(iterations):
            await protected_operation()
        protected_duration = time.time() - start_protected

        overhead = protected_duration - baseline_duration
        overhead_percent = (overhead / baseline_duration) * 100

        print(f"\nCircuit Breaker overhead:")
        print(f"  Baseline: {baseline_duration:.4f} sec")
        print(f"  Protected: {protected_duration:.4f} sec")
        print(f"  Overhead: {overhead:.4f} sec ({overhead_percent:.2f}%)")

        # Overhead should be less than 50%
        assert overhead_percent < 50

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_handling_speed(self):
        """Measure how quickly circuit breaker opens on failures."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        @cb
        async def failing_operation():
            raise ValueError("Error")

        start_time = time.time()

        # Trigger failures to open circuit
        for _ in range(3):
            try:
                await failing_operation()
            except ValueError:
                pass

        # Time to open circuit
        open_time = time.time() - start_time

        print(f"\nCircuit opened in: {open_time:.4f} sec")

        # Should open very quickly
        assert open_time < 0.1


class TestRetryPerformance:
    """Performance benchmarks for Retry mechanism."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_retry_successful_operations(self):
        """Measure retry overhead on successful operations."""
        iterations = 1000

        # Without retry
        async def baseline():
            return "success"

        start_baseline = time.time()
        for _ in range(iterations):
            await baseline()
        baseline_duration = time.time() - start_baseline

        # With retry
        @retry(max_attempts=3, delay=0.001)
        async def with_retry():
            return "success"

        start_retry = time.time()
        for _ in range(iterations):
            await with_retry()
        retry_duration = time.time() - start_retry

        overhead = retry_duration - baseline_duration
        overhead_percent = (overhead / baseline_duration) * 100

        print(f"\nRetry mechanism overhead:")
        print(f"  Baseline: {baseline_duration:.4f} sec")
        print(f"  With retry: {retry_duration:.4f} sec")
        print(f"  Overhead: {overhead:.4f} sec ({overhead_percent:.2f}%)")

        # Overhead should be minimal
        assert overhead_percent < 100


class TestMemoryUsage:
    """Memory usage benchmarks."""

    @pytest.mark.performance
    def test_agent_memory_footprint(self):
        """Measure memory footprint of agents."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create many agents
        agents: List[DataAgent] = []
        for i in range(100):
            agent = DataAgent(agent_id=f"mem_{i}", name=f"MemAgent{i}", description="Memory test")
            agents.append(agent)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_per_agent = (final_memory - initial_memory) / 100

        print(f"\nMemory usage:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Per agent: {memory_per_agent:.2f} MB")

        # Each agent should use less than 1MB
        assert memory_per_agent < 1.0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_core_memory_under_load(self):
        """Measure LegionCore memory usage under load."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        core = LegionCore()

        # Register many agents
        for i in range(50):
            agent = DataAgent(agent_id=f"load_{i}", name=f"LoadAgent{i}", description="Load test")
            agent.start = lambda: None  # Mock start
            await core.register_agent_async(f"load_{i}", agent)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"\nLegionCore memory under load:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  After 50 agents: {final_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")

        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB for 50 agents


class TestScalability:
    """Scalability benchmarks."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_scale_agent_registration(self):
        """Test registration of large number of agents."""
        core = LegionCore()
        num_agents = 1000

        start_time = time.time()

        for i in range(num_agents):
            agent = DataAgent(agent_id=f"scale_{i}", name=f"ScaleAgent{i}", description="Scale test")
            agent.start = lambda: None  # Mock
            await core.register_agent_async(f"scale_{i}", agent)

        duration = time.time() - start_time
        rate = num_agents / duration

        print(f"\nAgent registration scalability:")
        print(f"  Agents: {num_agents}")
        print(f"  Duration: {duration:.2f} sec")
        print(f"  Rate: {rate:.2f} agents/sec")

        # Should register at least 100 agents per second
        assert rate > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance", "-s"])
