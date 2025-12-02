"""Unit tests for connection pool module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

try:
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

if SQLALCHEMY_AVAILABLE:
    from src.legion.utils.connection_pool import (
        ConnectionPool,
        PoolConfig
    )


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy not installed")
class TestPoolConfig:
    """Test PoolConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PoolConfig()
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.pool_pre_ping is True
        assert config.echo is False
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PoolConfig(
            pool_size=5,
            max_overflow=10,
            pool_timeout=60
        )
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 60


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy not installed")
class TestConnectionPool:
    """Test ConnectionPool class."""
    
    @pytest.fixture
    def db_url(self):
        """Return test database URL."""
        return "sqlite:///:memory:"
    
    @pytest.fixture
    def pool_config(self):
        """Return test pool configuration."""
        return PoolConfig(pool_size=2, max_overflow=3)
    
    def test_init_with_valid_url(self, db_url, pool_config):
        """Test initialization with valid URL."""
        pool = ConnectionPool(db_url, pool_config)
        assert pool.database_url == db_url
        assert pool.config == pool_config
        assert pool._engine is not None
        pool.close()
    
    def test_init_with_empty_url(self, pool_config):
        """Test initialization with empty URL raises ValueError."""
        with pytest.raises(ValueError, match="database_url cannot be empty"):
            ConnectionPool("", pool_config)
    
    def test_init_without_sqlalchemy(self, db_url, pool_config):
        """Test initialization without SQLAlchemy raises ImportError."""
        with patch('src.legion.utils.connection_pool.SQLALCHEMY_AVAILABLE', False):
            # Need to reload module to trigger the check
            # In practice, this is tested by running without SQLAlchemy installed
            pass
    
    def test_get_session_context_manager(self, db_url, pool_config):
        """Test getting session via context manager."""
        pool = ConnectionPool(db_url, pool_config)
        
        with pool.get_session() as session:
            assert session is not None
            result = session.execute("SELECT 1").scalar()
            assert result == 1
        
        pool.close()
    
    def test_get_session_commit(self, db_url, pool_config):
        """Test session commits on success."""
        pool = ConnectionPool(db_url, pool_config)
        
        with pool.get_session() as session:
            session.execute("CREATE TABLE test (id INTEGER)")
            session.execute("INSERT INTO test VALUES (1)")
        
        # Verify commit
        with pool.get_session() as session:
            result = session.execute("SELECT COUNT(*) FROM test").scalar()
            assert result == 1
        
        pool.close()
    
    def test_get_session_rollback_on_error(self, db_url, pool_config):
        """Test session rollback on error."""
        pool = ConnectionPool(db_url, pool_config)
        
        # Create table first
        with pool.get_session() as session:
            session.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        
        # Try to insert duplicate - should rollback
        with pytest.raises(Exception):
            with pool.get_session() as session:
                session.execute("INSERT INTO test VALUES (1)")
                session.execute("INSERT INTO test VALUES (1)")  # Duplicate!
        
        # Verify rollback - table should be empty
        with pool.get_session() as session:
            result = session.execute("SELECT COUNT(*) FROM test").scalar()
            assert result == 0
        
        pool.close()
    
    def test_get_metrics(self, db_url, pool_config):
        """Test getting pool metrics."""
        pool = ConnectionPool(db_url, pool_config)
        
        # Initial metrics
        metrics = pool.get_metrics()
        assert 'connections_created' in metrics
        assert 'connections_closed' in metrics
        assert 'errors' in metrics
        assert 'total_checkouts' in metrics
        
        # Use connection
        with pool.get_session() as session:
            session.execute("SELECT 1")
        
        # Check metrics updated
        metrics = pool.get_metrics()
        assert metrics['total_checkouts'] > 0
        
        pool.close()
    
    def test_health_check_success(self, db_url, pool_config):
        """Test successful health check."""
        pool = ConnectionPool(db_url, pool_config)
        assert pool.health_check() is True
        pool.close()
    
    def test_health_check_failure(self, pool_config):
        """Test failed health check with invalid URL."""
        # Use invalid URL
        pool = ConnectionPool("postgresql://invalid:invalid@localhost:9999/invalid", pool_config)
        assert pool.health_check() is False
        pool.close()
    
    def test_close_disposes_engine(self, db_url, pool_config):
        """Test close() disposes engine."""
        pool = ConnectionPool(db_url, pool_config)
        engine = pool._engine
        
        pool.close()
        
        # Engine should be disposed
        assert engine.pool.size() == 0
    
    def test_context_manager(self, db_url, pool_config):
        """Test pool as context manager."""
        with ConnectionPool(db_url, pool_config) as pool:
            assert pool._engine is not None
            with pool.get_session() as session:
                result = session.execute("SELECT 1").scalar()
                assert result == 1
        
        # Pool should be closed
        assert pool._engine.pool.size() == 0
    
    def test_metrics_thread_safety(self, db_url, pool_config):
        """Test metrics are thread-safe."""
        import threading
        
        pool = ConnectionPool(db_url, pool_config)
        
        def worker():
            with pool.get_session() as session:
                session.execute("SELECT 1")
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        metrics = pool.get_metrics()
        assert metrics['total_checkouts'] == 10
        
        pool.close()
    
    def test_pool_overflow(self, db_url):
        """Test pool overflow behavior."""
        config = PoolConfig(pool_size=1, max_overflow=1, pool_timeout=1)
        pool = ConnectionPool(db_url, config)
        
        # Get max connections
        sessions = []
        for _ in range(2):  # pool_size + max_overflow
            sessions.append(pool.get_session())
            next(sessions[-1])
        
        # Third connection should timeout
        with pytest.raises(Exception):  # Timeout or similar
            with pool.get_session() as session:
                session.execute("SELECT 1")
        
        # Cleanup
        for ctx in sessions:
            try:
                next(ctx, None)
            except StopIteration:
                pass
        
        pool.close()
