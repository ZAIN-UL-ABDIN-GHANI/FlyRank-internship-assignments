import os

from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None


async def init_pool() -> AsyncConnectionPool:
    global _pool
    database_url = os.environ["DATABASE_URL"]
    _pool = AsyncConnectionPool(conninfo=database_url, open=False)
    await _pool.open()
    return _pool


async def close_pool() -> None:
    if _pool is not None:
        await _pool.close()


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool not initialised yet — did the app start correctly?")
    return _pool
