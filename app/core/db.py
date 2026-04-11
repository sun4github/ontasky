"""Shared async connection pool (psycopg3 + psycopg_pool). No ORM."""

from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

_pool: AsyncConnectionPool | None = None


async def open_pool() -> None:
    """Create and open the shared async connection pool."""
    global _pool
    if _pool is not None:
        return
    _pool = AsyncConnectionPool(
        conninfo=settings.db_conninfo,
        min_size=2,
        max_size=10,
        open=False,
    )
    await _pool.open()


async def close_pool() -> None:
    """Close the shared pool gracefully."""
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None


def get_pool() -> AsyncConnectionPool:
    """Return the pool. Raises RuntimeError if not initialized."""
    if _pool is None:
        raise RuntimeError("Connection pool is not initialized. Call open_pool() first.")
    return _pool
