from typing import List, Optional

from app.models import Task, TaskCreate, TaskUpdate
from app.repositories.interface import ItemRepository


class ItemService:
    """
    Business logic lives here. Notice: not one line of this file
    mentions SQL, psycopg, or a Python dict. It only knows about
    ItemRepository, the abstraction — which is exactly why this file
    did not need to change when we swapped storage engines.
    """

    def __init__(self, repository: ItemRepository) -> None:
        self._repo = repository

    async def create_item(self, data: TaskCreate) -> Task:
        return await self._repo.create(data)

    async def get_item(self, task_id: int) -> Optional[Task]:
        return await self._repo.get(task_id)

    async def list_items(self) -> List[Task]:
        return await self._repo.list()

    async def update_item(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        return await self._repo.update(task_id, data)

    async def delete_item(self, task_id: int) -> bool:
        return await self._repo.delete(task_id)
