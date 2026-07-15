from typing import List, Optional

from app.models import Item, ItemCreate
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

    async def create_item(self, data: ItemCreate) -> Item:
        return await self._repo.create(data)

    async def get_item(self, item_id: int) -> Optional[Item]:
        return await self._repo.get(item_id)

    async def list_items(self) -> List[Item]:
        return await self._repo.list()

    async def update_item(self, item_id: int, data: ItemCreate) -> Optional[Item]:
        return await self._repo.update(item_id, data)

    async def delete_item(self, item_id: int) -> bool:
        return await self._repo.delete(item_id)
