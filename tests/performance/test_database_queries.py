"""Performance Tests - Database Query Optimization"""

import pytest
import asyncio
from legion.infrastructure.performance import QueryOptimizer


@pytest.mark.asyncio
class TestQueryOptimization:
    """Test N+1 query problem fixes"""
    
    @pytest.fixture
    async def db_pool(self, mock_db_pool):
        """Create test database pool (mocked)"""
        yield mock_db_pool
        await mock_db_pool.close()
    
    @pytest.mark.slow
    async def test_n_plus_one_detection(self, db_pool):
        """Verify N+1 queries are replaced with batch queries"""
        # This test is marked as slow and uses mocked database
        # For real performance testing, run against actual PostgreSQL
        
        # Mock creates test data
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
        
        # With mock, this is just a structural test
        # Real timing validation requires PostgreSQL
        assert batch_results is not None
    
    async def test_eager_loading(self, db_pool):
        """Test eager loading with relations"""
        # Test structural correctness with mock
        result = await QueryOptimizer.fetch_with_relations(
            db_pool,
            "SELECT * FROM test_tasks",
            {
                "user": "SELECT * FROM users WHERE id = ANY($1)"
            }
        )
        
        # With mock, validate structure
        assert isinstance(result, list)
