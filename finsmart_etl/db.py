"""
Database connection helpers using psycopg 3.

Provides:
- Lazy-initialized connection pool
- Context manager for connections
- Simple execute/fetchall helpers
- Health check CLI
"""

import os
import sys
from contextlib import contextmanager
from typing import Any, Generator, Optional

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import get_config


# Module-level pool (lazily initialized)
_pool: Optional[ConnectionPool] = None


def _get_dsn() -> str:
    """Build DSN from environment variables."""
    config = get_config()
    return config.dsn


def _get_pool_size() -> int:
    """Get pool size from config."""
    config = get_config()
    return config.db_pool_size


def get_pool() -> ConnectionPool:
    """
    Get or create the connection pool (lazy initialization).
    
    Returns:
        ConnectionPool: The psycopg connection pool.
    """
    global _pool
    if _pool is None:
        dsn = _get_dsn()
        pool_size = _get_pool_size()
        _pool = ConnectionPool(
            dsn,
            min_size=1,
            max_size=pool_size,
            open=True,
        )
    return _pool


@contextmanager
def get_conn() -> Generator[psycopg.Connection, None, None]:
    """
    Context manager that yields a connection from the pool.
    
    Usage:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    
    Yields:
        psycopg.Connection: A database connection.
    """
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


@contextmanager
def get_dict_conn() -> Generator[psycopg.Connection, None, None]:
    """
    Context manager that yields a connection configured for dict rows.
    
    Yields:
        psycopg.Connection: A database connection with dict row factory.
    """
    pool = get_pool()
    with pool.connection() as conn:
        conn.row_factory = dict_row
        yield conn


def execute(query: str, params: Optional[tuple] = None) -> None:
    """
    Execute a query without returning results.
    
    Args:
        query: SQL query string.
        params: Optional query parameters.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()


def fetchall(query: str, params: Optional[tuple] = None) -> list[tuple]:
    """
    Execute a query and return all results as tuples.
    
    Args:
        query: SQL query string.
        params: Optional query parameters.
    
    Returns:
        List of result tuples.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def fetchall_dict(query: str, params: Optional[tuple] = None) -> list[dict]:
    """
    Execute a query and return all results as dictionaries.
    
    Args:
        query: SQL query string.
        params: Optional query parameters.
    
    Returns:
        List of result dictionaries.
    """
    with get_dict_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def fetchone(query: str, params: Optional[tuple] = None) -> Optional[tuple]:
    """
    Execute a query and return a single result.
    
    Args:
        query: SQL query string.
        params: Optional query parameters.
    
    Returns:
        Single result tuple or None.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetchone_dict(query: str, params: Optional[tuple] = None) -> Optional[dict]:
    """
    Execute a query and return a single result as dictionary.
    
    Args:
        query: SQL query string.
        params: Optional query parameters.
    
    Returns:
        Single result dictionary or None.
    """
    with get_dict_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def ping() -> bool:
    """
    Test database connectivity.
    
    Returns:
        True if connection successful, False otherwise.
    """
    try:
        result = fetchone("SELECT 1")
        return result is not None and result[0] == 1
    except Exception as e:
        print(f"Database ping failed: {e}", file=sys.stderr)
        return False


def close_pool() -> None:
    """Close the connection pool (for cleanup)."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


# CLI health check
if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Database utilities")
    parser.add_argument("--ping", action="store_true", help="Test database connectivity")
    args = parser.parse_args()
    
    if args.ping:
        if ping():
            print("ok")
            sys.exit(0)
        else:
            print("failed")
            sys.exit(1)
    else:
        parser.print_help()
