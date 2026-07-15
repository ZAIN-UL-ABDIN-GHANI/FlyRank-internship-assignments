from datetime import datetime, timezone
from itertools import count
from typing import Dict, List, Optional

from app.models import Item, ItemCreate
from app.repositories.interface import ItemRepository


class MemoryRepository(ItemRepository):
    """Original A2 storage. Kept so you can flip back to it with one
    environment variable and prove the rest of the app doesn't care."""

    def __init__(self) -> None:
        self._items: Dict[int, Item] = {}
        self._ids = count(1)

    async def create(self, data: ItemCreate) -> Item:
        item_id = next(self._ids)
        item = Item(id=item_id, created_at=datetime.now(timezone.utc), **data.model_dump())
        self._items[item_id] = item
        return item

    async def get(self, item_id: int) -> Optional[Item]:
        return self._items.get(item_id)

    async def list(self) -> List[Item]:
        return list(self._items.values())

    async def update(self, item_id: int, data: ItemCreate) -> Optional[Item]:
        existing = self._items.get(item_id)
        if not existing:
            return None
        updated = existing.model_copy(update=data.model_dump())
        self._items[item_id] = updated
        return updated

    async def delete(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None
