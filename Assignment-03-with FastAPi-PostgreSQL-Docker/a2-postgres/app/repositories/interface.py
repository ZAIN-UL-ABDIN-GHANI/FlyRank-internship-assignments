from abc import ABC, abstractmethod
from typing import List, Optional

from app.models import Item, ItemCreate


class ItemRepository(ABC):
    """
    The contract every storage implementation must follow.

    The Service Layer only ever talks to THIS class (or rather, to
    whatever concrete class is handed to it that satisfies this shape).
    It never imports MemoryRepository or PostgresRepository directly.
    """

    @abstractmethod
    async def create(self, data: ItemCreate) -> Item: ...

    @abstractmethod
    async def get(self, item_id: int) -> Optional[Item]: ...

    @abstractmethod
    async def list(self) -> List[Item]: ...

    @abstractmethod
    async def update(self, item_id: int, data: ItemCreate) -> Optional[Item]: ...

    @abstractmethod
    async def delete(self, item_id: int) -> bool: ...
