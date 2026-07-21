from abc import ABC, abstractmethod
from typing import List, Optional

from app.models import Task, TaskCreate, TaskUpdate


class ItemRepository(ABC):
    """
    The contract every storage implementation must follow.

    The Service Layer only ever talks to THIS class (or rather, to
    whatever concrete class is handed to it that satisfies this shape).
    It never imports MemoryRepository or PostgresRepository directly.
    """

    @abstractmethod
    async def create(self, data: TaskCreate) -> Task: ...

    @abstractmethod
    async def get(self, task_id: int) -> Optional[Task]: ...

    @abstractmethod
    async def list(self) -> List[Task]: ...

    @abstractmethod
    async def update(self, task_id: int, data: TaskUpdate) -> Optional[Task]: ...

    @abstractmethod
    async def delete(self, task_id: int) -> bool: ...
