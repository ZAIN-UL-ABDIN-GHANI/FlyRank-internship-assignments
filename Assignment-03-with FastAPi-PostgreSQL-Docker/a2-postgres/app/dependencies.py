import os

from app.db import get_pool
from app.repositories.interface import ItemRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.postgres_repository import PostgresRepository
from app.services.item_service import ItemService

# One shared instance so "memory mode" actually persists across requests
# within a single running process (it still won't survive a restart —
# that's the whole point of the assignment).
_memory_repo_singleton = MemoryRepository()


def get_repository() -> ItemRepository:
    """
    This is the ONE function that decides which storage engine backs
    the app. Everything above it (service, routes) is unaffected by
    whatever this function returns, as long as it satisfies
    ItemRepository. Flip REPOSITORY_TYPE in .env to switch.
    """
    repo_type = os.environ.get("REPOSITORY_TYPE", "postgres").lower()
    if repo_type == "memory":
        return _memory_repo_singleton
    return PostgresRepository(get_pool())


def get_item_service() -> ItemService:
    return ItemService(get_repository())
