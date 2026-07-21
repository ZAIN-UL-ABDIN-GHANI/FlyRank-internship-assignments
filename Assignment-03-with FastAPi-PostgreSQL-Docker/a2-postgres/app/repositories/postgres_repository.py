from typing import List, Optional

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.models import Task, TaskCreate, TaskUpdate
from app.repositories.interface import ItemRepository


class PostgresRepository(ItemRepository):
    """
    Same interface as MemoryRepository. The Service Layer cannot tell
    the difference between this class and the in-memory one — that's
    the whole point of coding against an abstraction.
    """

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def create(self, data: TaskCreate) -> Task:
        query = """
            INSERT INTO tasks (title, done)
            VALUES (%s, %s)
            RETURNING id, title, done, created_at
        """
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (data.title, False))
                row = await cur.fetchone()
        return Task(**row)

    async def get(self, task_id: int) -> Optional[Task]:
        query = "SELECT id, title, done, created_at FROM tasks WHERE id = %s"
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (task_id,))
                row = await cur.fetchone()
        return Task(**row) if row else None

    async def list(self) -> List[Task]:
        query = "SELECT id, title, done, created_at FROM tasks ORDER BY id"
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                rows = await cur.fetchall()
        return [Task(**row) for row in rows]

    async def update(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        query = """
            UPDATE tasks
            SET title = %s, done = %s
            WHERE id = %s
            RETURNING id, title, done, created_at
        """
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (data.title, data.done, task_id))
                row = await cur.fetchone()
        return Task(**row) if row else None

    async def delete(self, task_id: int) -> bool:
        query = "DELETE FROM tasks WHERE id = %s"
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (task_id,))
                deleted = cur.rowcount
        return deleted > 0
