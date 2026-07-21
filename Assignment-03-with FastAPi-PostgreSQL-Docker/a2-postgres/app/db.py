import os

from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None

_SEED_TASKS = [
    "Learn FastAPI",
    "Learn PostgreSQL",
    "Finish Assignment",
]


async def init_pool() -> AsyncConnectionPool:
    global _pool
    database_url = os.environ["DATABASE_URL"]
    _pool = AsyncConnectionPool(conninfo=database_url, open=False)
    await _pool.open()
    async with _pool.connection() as conn:
        await conn.execute("SELECT 1")
    return _pool


async def close_pool() -> None:
    if _pool is not None:
        await _pool.close()


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool not initialised yet — did the app start correctly?")
    return _pool


async def initialize_database() -> None:
    """Create schema if needed and seed sample tasks only when empty."""
    pool = get_pool()
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """
    count_sql = "SELECT COUNT(*) FROM tasks"
    seed_sql = "INSERT INTO tasks (title, done) VALUES (%s, %s)"

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(create_table_sql)
            await cur.execute(count_sql)
            row = await cur.fetchone()
            task_count = int(row[0]) if row else 0
            if task_count == 0:
                for title in _SEED_TASKS:
                    await cur.execute(seed_sql, (title, False))
