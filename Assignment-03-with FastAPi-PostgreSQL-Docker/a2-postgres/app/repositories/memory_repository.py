from datetime import datetime, timezone
from itertools import count
from typing import Dict, List, Optional

from app.models import Task, TaskCreate, TaskUpdate
from app.repositories.interface import ItemRepository


class MemoryRepository(ItemRepository):
    """Original A2 storage. Kept so you can flip back to it with one
    environment variable and prove the rest of the app doesn't care."""

    def __init__(self) -> None:
        self._tasks: Dict[int, Task] = {}
        self._ids = count(1)

    async def create(self, data: TaskCreate) -> Task:
        task_id = next(self._ids)
        task = Task(id=task_id, title=data.title, done=False, created_at=datetime.now(timezone.utc))
        self._tasks[task_id] = task
        return task

    async def get(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def list(self) -> List[Task]:
        return list(self._tasks.values())

    async def update(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        existing = self._tasks.get(task_id)
        if not existing:
            return None
        updated = existing.model_copy(update=data.model_dump())
        self._tasks[task_id] = updated
        return updated

    async def delete(self, task_id: int) -> bool:
        return self._tasks.pop(task_id, None) is not None
