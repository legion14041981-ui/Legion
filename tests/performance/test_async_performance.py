"""Performance benchmarks для async optimization."""

import pytest
import asyncio
import time
from legion.core import LegionCore
from legion.agents import LegionAgent


class MockAgent(LegionAgent):
    """Тестовый агент."""
    
    def execute(self, task_data):
        return {'result': 'sync'}
    
    async def execute_async(self, task_data):
        await asyncio.sleep(0.001)  # Simulate I/O
        return {'result': 'async'}


@pytest.mark.asyncio
class TestAsyncPerformance:
    """Async performance benchmarks."""
    
    async def test_async_registration_performance(self):
        """Бенчмарк: async регистрация."""
        core = LegionCore({'num_workers': 4})
        
        agents = [MockAgent(f'agent_{i}') for i in range(100)]
        
        start = time.time()
        tasks = [core.register_agent(agent.agent_id, agent) for agent in agents]
        await asyncio.gather(*tasks)
        duration = time.time() - start
        
        # Должно быть быстрее 100ms для 100 агентов
        assert duration < 0.1, f"Registration too slow: {duration:.3f}s"
        
        await core.stop()
    
    async def test_cache_hit_rate(self):
        """Бенчмарк: cache hit rate."""
        core = LegionCore({'hot_cache_size': 128})
        
        # Зарегистрировать агентов
        agents = [MockAgent(f'agent_{i}') for i in range(50)]
        for agent in agents:
            await core.register_agent(agent.agent_id, agent)
        
        # Доступ к агентам (должно быть из кэша)
        for _ in range(1000):
            await core.get_agent_cached('agent_0')
        
        hit_rate = core.get_cache_hit_rate()
        assert hit_rate > 95, f"Cache hit rate too low: {hit_rate:.1f}%"
        
        await core.stop()
    
    async def test_parallel_task_execution(self):
        """Бенчмарк: параллельное выполнение."""
        core = LegionCore({'num_workers': 4})
        await core.start()
        
        agent = MockAgent('test_agent')
        await core.register_agent('test_agent', agent)
        
        # Создать 100 задач
        tasks = [
            {'task_id': f'task_{i}', 'task_data': {'agent_id': 'test_agent', 'data': i}}
            for i in range(100)
        ]
        
        start = time.time()
        results = await core.dispatch_tasks_parallel(tasks)
        duration = time.time() - start
        
        # Должно завершиться за <1с
        assert duration < 1.0, f"Parallel execution too slow: {duration:.3f}s"
        assert len(results) == 100
        
        await core.stop()
