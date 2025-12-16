"""
Database connection management module with connection pooling and context managers.
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[pool.ThreadedConnectionPool] = None


def initialize_connection_pool(
    min_connections: int = 5,
    max_connections: int = 50
) -> None:
    """
    Initialize the PostgreSQL connection pool.

    Args:
        min_connections: Minimum number of connections in the pool
        max_connections: Maximum number of connections in the pool
    """
    global _connection_pool

    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://z_agent_user:z_agent_password@localhost:5554/z_agent")
        _connection_pool = pool.ThreadedConnectionPool(
            min_connections,
            max_connections,
            database_url
        )
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        raise


def get_connection():
    """
    Get a database connection from the pool or create a new one if pool is not initialized.

    Returns:
        psycopg2 database connection
    """
    global _connection_pool

    if _connection_pool:
        try:
            return _connection_pool.getconn()
        except Exception as e:
            logger.warning(f"Failed to get connection from pool: {e}, creating new connection")

    # Fallback to direct connection
    database_url = os.getenv("DATABASE_URL", "postgresql://z_agent_user:z_agent_password@localhost:5554/z_agent")
    return psycopg2.connect(database_url)


def release_connection(conn) -> None:
    """
    Release a connection back to the pool if it exists.

    Args:
        conn: Database connection to release
    """
    global _connection_pool

    if _connection_pool and conn:
        try:
            _connection_pool.putconn(conn)
        except Exception as e:
            logger.warning(f"Failed to release connection to pool: {e}")
            # Close connection directly if it can't be returned to pool
            try:
                conn.close()
            except Exception:
                pass


@contextmanager
def get_cursor() -> Generator:
    """
    Context manager for getting a database cursor with automatic connection management.

    Yields:
        psycopg2 cursor with DictCursor for better row handling
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
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
def get_connection_context() -> Generator:
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


def close_connection_pool() -> None:
    """Close all connections in the pool and clean up resources."""
    global _connection_pool

    if _connection_pool:
        try:
            _connection_pool.closeall()
            logger.info("Database connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection pool: {e}")
        finally:
            _connection_pool = None


# Initialize pool on module import
try:
    initialize_connection_pool()
except Exception as e:
    logger.warning(f"Could not initialize connection pool on import: {e}")
