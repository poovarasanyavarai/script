"""
Optimized Database connection management module with enhanced connection pooling,
health checks, and automatic recovery mechanisms.

Features:
- Intelligent connection pooling with health checks
- Automatic retry logic for transient failures
- Connection validation and recycling
- Metrics and monitoring
- Graceful degradation under load
"""

import logging
import os
import time
import threading
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
from functools import wraps

import psycopg2
from psycopg2 import pool, sql, OperationalError
from psycopg2.extras import DictCursor, RealDictCursor

logger = logging.getLogger(__name__)

# Global connection pool and monitoring
_connection_pool: Optional[pool.ThreadedConnectionPool] = None
_pool_stats = {
    'total_requests': 0,
    'pool_hits': 0,
    'pool_misses': 0,
    'connection_errors': 0,
    'reconnections': 0
}
_stats_lock = threading.Lock()


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying database operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, psycopg2.Error) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_attempts}): {e}")
                        time.sleep(delay * (backoff ** attempt))
                    else:
                        logger.error(f"Database operation failed after {max_attempts} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


class HealthAwareConnectionPool(pool.ThreadedConnectionPool):
    """Enhanced connection pool with health checks and automatic recovery."""

    def __init__(self, minconn, maxconn, *args, **kwargs):
        super().__init__(minconn, maxconn, *args, **kwargs)
        self._last_health_check = 0
        self._health_check_interval = 60  # seconds

    def _validate_connection(self, conn):
        """Validate that a connection is healthy."""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except (psycopg2.Error, psycopg2.OperationalError):
            return False

    def getconn(self, key=None):
        """Get connection with health check."""
        with _stats_lock:
            _pool_stats['total_requests'] += 1

        # Perform periodic health check
        current_time = time.time()
        if current_time - self._last_health_check > self._health_check_interval:
            self._perform_health_check()
            self._last_health_check = current_time

        try:
            # Try to get connection from pool
            conn = super().getconn(key)
            if self._validate_connection(conn):
                with _stats_lock:
                    _pool_stats['pool_hits'] += 1
                return conn
            else:
                # Connection is bad, close it and try again
                self.putconn(conn, key, close=True)
                logger.warning("Removed unhealthy connection from pool")
        except Exception:
            pass

        # If we couldn't get a good connection from pool, create a new one
        with _stats_lock:
            _pool_stats['pool_misses'] += 1
        return self._create_new_connection()

    def _create_new_connection(self):
        """Create a new connection with retry logic."""
        for attempt in range(3):
            try:
                conn = psycopg2.connect(
                    host=self._host,
                    port=self._port,
                    user=self._user,
                    password=self._password,
                    database=self._dbname
                )
                with _stats_lock:
                    _pool_stats['reconnections'] += 1
                return conn
            except Exception as e:
                if attempt < 2:
                    logger.warning(f"Failed to create connection (attempt {attempt + 1}): {e}")
                    time.sleep(1 ** (attempt + 1))
                else:
                    with _stats_lock:
                        _pool_stats['connection_errors'] += 1
                    raise

    def _perform_health_check(self):
        """Perform health check on pooled connections."""
        try:
            # Try to get a connection and validate it
            conn = self.getconn()
            if self._validate_connection(conn):
                self.putconn(conn)
            else:
                self.putconn(conn, close=True)
        except Exception as e:
            logger.warning(f"Health check failed: {e}")


def initialize_connection_pool(
    min_connections: int = 5,
    max_connections: int = 50,
    connection_timeout: int = 30,
    idle_timeout: int = 300,
) -> None:
    """
    Initialize the PostgreSQL connection pool with optimized settings.

    Args:
        min_connections: Minimum number of connections in the pool
        max_connections: Maximum number of connections in the pool
        connection_timeout: Connection timeout in seconds
        idle_timeout: Idle timeout for connections
    """
    global _connection_pool

    try:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://z_agent_user:z_agent_password@localhost:5554/z_agent"
        )

        # Parse connection string for pool configuration
        # This is simplified - you might want to use urllib.parse for full implementation
        conn_params = {
            'database_url': database_url,
            'minconn': min_connections,
            'maxconn': max_connections,
        }

        _connection_pool = HealthAwareConnectionPool(**conn_params)

        # Store connection parameters for health checks
        if hasattr(_connection_pool, '_set_kwargs'):
            # psycopg2 specific attributes
            _connection_pool._host = 'localhost'
            _connection_pool._port = 5554
            _connection_pool._user = 'z_agent_user'
            _connection_pool._password = 'z_agent_password'
            _connection_pool._dbname = 'z_agent'

        logger.info(f"✅ Database connection pool initialized successfully")
        logger.info(f"   Pool size: {min_connections}-{max_connections} connections")
        logger.info(f"   Connection timeout: {connection_timeout}s")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database connection pool: {e}")
        raise


@with_retry(max_attempts=3)
def get_connection():
    """
    Get a database connection from the pool or create a new one if pool is not initialized.

    Returns:
        psycopg2 database connection with optimized settings
    """
    global _connection_pool

    if _connection_pool:
        try:
            return _connection_pool.getconn()
        except Exception as e:
            logger.warning(f"Failed to get connection from pool: {e}, creating new connection")

    # Fallback to direct connection
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://z_agent_user:z_agent_password@localhost:5554/z_agent"
    )

    # Configure connection for better performance
    conn = psycopg2.connect(database_url)
    conn.set_session(isolation_level='READ COMMITTED', autocommit=False)

    # Optimize connection settings
    with conn.cursor() as cursor:
        cursor.execute("SET statement_timeout = '30s'")
        cursor.execute("SET lock_timeout = '10s'")

    return conn


def release_connection(conn) -> None:
    """
    Release a connection back to the pool with validation.

    Args:
        conn: Database connection to release
    """
    global _connection_pool

    if not conn:
        return

    if _connection_pool:
        try:
            # Validate connection before returning to pool
            if _connection_pool._validate_connection(conn):
                _connection_pool.putconn(conn)
            else:
                _connection_pool.putconn(conn, close=True)
                logger.debug("Closed unhealthy connection")
        except Exception as e:
            logger.warning(f"Failed to release connection to pool: {e}")
            conn.close()
    else:
        conn.close()


@contextmanager
def get_cursor(cursor_type=DictCursor):
    """
    Context manager for getting a database cursor with automatic connection management
    and optimized performance settings.

    Args:
        cursor_type: Type of cursor (DictCursor or RealDictCursor)

    Yields:
        psycopg2 cursor with optimized settings
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=cursor_type)

        # Performance optimizations
        with cursor:
            cursor.execute("SET work_mem = '16MB'")
            cursor.execute("SET maintenance_work_mem = '64MB'")
            cursor.execute("SET effective_cache_size = '256MB'")

        yield cursor
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)


@contextmanager
def get_connection_context():
    """
    Context manager for getting a database connection with automatic cleanup.

    Yields:
        psycopg2 connection
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if conn:
            release_connection(conn)


def get_pool_stats() -> Dict[str, Any]:
    """Get connection pool statistics for monitoring."""
    with _stats_lock:
        stats = _pool_stats.copy()
        if stats['total_requests'] > 0:
            stats['pool_hit_rate'] = (stats['pool_hits'] / stats['total_requests']) * 100
        else:
            stats['pool_hit_rate'] = 0

        if _connection_pool:
            stats['pool_size'] = _connection_pool.minconn
            stats['max_connections'] = _connection_pool.maxconn
            stats['available_connections'] = _connection_pool._maxconn - len(_connection_pool._pool)

        return stats


def close_connection_pool() -> None:
    """Close all connections in the pool and clean up resources."""
    global _connection_pool

    if _connection_pool:
        try:
            _connection_pool.closeall()
            logger.info("✅ Database connection pool closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing database connection pool: {e}")
        finally:
            _connection_pool = None


def monitor_pool_health():
    """Monitor connection pool health and log statistics."""
    stats = get_pool_stats()
    logger.info("📊 Connection Pool Statistics:")
    logger.info(f"   Total requests: {stats['total_requests']}")
    logger.info(f"   Pool hit rate: {stats.get('pool_hit_rate', 0):.1f}%")
    logger.info(f"   Connection errors: {stats['connection_errors']}")
    logger.info(f"   Reconnections: {stats['reconnections']}")


# Initialize pool on module import with error handling
try:
    initialize_connection_pool()
except Exception as e:
    logger.warning(f"Could not initialize connection pool on import: {e}")
    logger.info("Will use direct connections until pool is initialized")


# Register cleanup on exit
import atexit
atexit.register(close_connection_pool)