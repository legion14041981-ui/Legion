"""Database connection pooling for Legion Framework.

Provides thread-safe connection pool management with:
- Automatic connection lifecycle management
- Health checking and stale connection removal
- Configurable pool size and timeouts
- Metrics for monitoring
"""

import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
import time
from dataclasses import dataclass
from threading import Lock

try:
    from sqlalchemy import create_engine, event, pool
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import sessionmaker, Session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Engine = Any  # type: ignore
    Session = Any  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for connection pool."""
    
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo: bool = False


class ConnectionPool:
    """Thread-safe database connection pool.
    
    Example:
        >>> config = PoolConfig(pool_size=20)
        >>> pool = ConnectionPool("postgresql://user:pass@localhost/db", config)
        >>> with pool.get_session() as session:
        ...     result = session.execute("SELECT 1")
    """
    
    def __init__(self, database_url: str, config: Optional[PoolConfig] = None):
        """Initialize connection pool.
        
        Args:
            database_url: Database connection URL
            config: Pool configuration (uses defaults if None)
        
        Raises:
            ImportError: If SQLAlchemy is not installed
            ValueError: If database_url is invalid
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy is required for connection pooling. "
                "Install with: pip install sqlalchemy"
            )
        
        if not database_url:
            raise ValueError("database_url cannot be empty")
        
        self.config = config or PoolConfig()
        self.database_url = database_url
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._lock = Lock()
        self._metrics: Dict[str, Any] = {
            'connections_created': 0,
            'connections_closed': 0,
            'errors': 0,
            'total_checkouts': 0
        }
        
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize SQLAlchemy engine and session factory."""
        try:
            self._engine = create_engine(
                self.database_url,
                poolclass=pool.QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=self.config.echo
            )
            
            # Register event listeners for metrics
            event.listen(self._engine, 'connect', self._on_connect)
            event.listen(self._engine, 'close', self._on_close)
            event.listen(self._engine, 'checkout', self._on_checkout)
            
            self._session_factory = sessionmaker(bind=self._engine)
            
            logger.info(
                f"Connection pool initialized: size={self.config.pool_size}, "
                f"max_overflow={self.config.max_overflow}"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def _on_connect(self, dbapi_conn, connection_record) -> None:
        """Called when new connection is created."""
        with self._lock:
            self._metrics['connections_created'] += 1
        logger.debug("New database connection created")
    
    def _on_close(self, dbapi_conn, connection_record) -> None:
        """Called when connection is closed."""
        with self._lock:
            self._metrics['connections_closed'] += 1
        logger.debug("Database connection closed")
    
    def _on_checkout(self, dbapi_conn, connection_record, connection_proxy) -> None:
        """Called when connection is checked out from pool."""
        with self._lock:
            self._metrics['total_checkouts'] += 1
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session from the pool.
        
        Yields:
            Session: Database session
        
        Example:
            >>> with pool.get_session() as session:
            ...     session.execute("SELECT 1")
        """
        if not self._session_factory:
            raise RuntimeError("Connection pool not initialized")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            with self._lock:
                self._metrics['errors'] += 1
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics.
        
        Returns:
            Dict with metrics (connections created/closed, errors, etc.)
        """
        with self._lock:
            metrics = self._metrics.copy()
        
        if self._engine:
            pool_status = self._engine.pool.status()
            metrics['pool_status'] = pool_status
        
        return metrics
    
    def health_check(self) -> bool:
        """Check if connection pool is healthy.
        
        Returns:
            True if pool is healthy, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self) -> None:
        """Close all connections in the pool."""
        if self._engine:
            self._engine.dispose()
            logger.info("Connection pool closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
