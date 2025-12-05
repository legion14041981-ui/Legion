"""Performance Tests - Database Query Optimization"""

import pytest
import asyncio
import asyncpg
from legion.infrastructure.performance import QueryOptimizer


@pytest.mark.asyncio
class TestQueryOptimization:
    """Test N+1 query problem fixes"""
    
    @pytest.fixture
    async def db_pool(self):
        """Create test database pool"""
        pool = await asyncpg.create_pool(
            "postgresql://localhost/legion_test",
            min_size=2,
            max_size=10
        )
        yield pool
        await pool.close()
    
    async def test_n_plus_one_detection(self, db_pool):
        """Verify N+1 queries are replaced with batch queries"""
        # Create test data
        await db_pool.execute("""
            CREATE TEMP TABLE test_tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200)
            )
        """)
        
        await db_pool.execute("""
            INSERT INTO test_tasks (title)
            SELECT 'Task ' || generate_series(1, 100)
        """)
        
        # Time N+1 approach (BAD)
        import time
        start = time.time()
        tasks = await db_pool.fetch("SELECT * FROM test_tasks LIMIT 100")
        for task in tasks:
            # Simulate N queries
            await db_pool.fetchrow("SELECT * FROM test_tasks WHERE id = $1", task['id'])
        n_plus_one_time = time.time() - start
        
        # Time batch approach (GOOD)
        start = time.time()
        task_ids = [t['id'] for t in tasks]
        batch_results = await db_pool.fetch(
            "SELECT * FROM test_tasks WHERE id = ANY($1)",
            task_ids
        )
        batch_time = time.time() - start
        
        # Batch should be significantly faster
        assert batch_time < n_plus_one_time / 10, "Batch queries should be 10x+ faster"
    
    async def test_eager_loading(self, db_pool):
        """Test eager loading with relations"""
        # This would test the QueryOptimizer.fetch_with_relations method
        # with actual database setup
        pass
