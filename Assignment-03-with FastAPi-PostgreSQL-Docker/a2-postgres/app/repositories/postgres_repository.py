from typing import List, Optional

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.models import Item, ItemCreate
from app.repositories.interface import ItemRepository


class PostgresRepository(ItemRepository):
    """
    Same interface as MemoryRepository. The Service Layer cannot tell
    the difference between this class and the in-memory one — that's
    the whole point of coding against an abstraction.
    """

    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def create(self, data: ItemCreate) -> Item:
        query = """
            INSERT INTO items (name, description, price)
            VALUES (%s, %s, %s)
            RETURNING id, name, description, price, created_at
        """
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (data.name, data.description, data.price))
                row = await cur.fetchone()
        return Item(**row)

    async def get(self, item_id: int) -> Optional[Item]:
        query = "SELECT id, name, description, price, created_at FROM items WHERE id = %s"
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (item_id,))
                row = await cur.fetchone()
        return Item(**row) if row else None

    async def list(self) -> List[Item]:
        query = "SELECT id, name, description, price, created_at FROM items ORDER BY id"
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                rows = await cur.fetchall()
        return [Item(**row) for row in rows]

    async def update(self, item_id: int, data: ItemCreate) -> Optional[Item]:
        query = """
            UPDATE items
            SET name = %s, description = %s, price = %s
            WHERE id = %s
            RETURNING id, name, description, price, created_at
        """
        async with self._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (data.name, data.description, data.price, item_id))
                row = await cur.fetchone()
        return Item(**row) if row else None

    async def delete(self, item_id: int) -> bool:
        query = "DELETE FROM items WHERE id = %s"
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (item_id,))
                deleted = cur.rowcount
        return deleted > 0
