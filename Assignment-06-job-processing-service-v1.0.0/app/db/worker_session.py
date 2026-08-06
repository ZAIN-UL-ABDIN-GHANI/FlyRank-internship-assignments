"""
Sync database session for Celery workers.

Celery's execution model is fundamentally synchronous - even under the
prefork pool, each worker child process handles one task at a time. Reusing
app/db/session.py's async engine here would mean an asyncio event loop and
connection pool created at import time getting inherited across fork()
boundaries, which is a well-documented source of subtle connection
corruption with asyncpg specifically. A separate sync engine sidesteps the
problem entirely rather than working around it with asyncio.run() calls
inside every task.

The connection details (host, port, credentials, database name) still come
from the single DATABASE_URL in settings - only the driver differs.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _to_sync_url(async_url: str) -> str:
    """postgresql+asyncpg://... -> postgresql+psycopg://... (sync driver, same DSN)."""
    return async_url.replace("+asyncpg", "+psycopg")


sync_engine = create_engine(
    _to_sync_url(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

WorkerSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False, autoflush=False)


@contextmanager
def get_worker_session() -> Generator[Session, None, None]:
    """
    Yields a sync session; rolls back on exception, always closes.

    Deliberately does NOT auto-commit on successful exit - the task needs
    to make incremental commits at each state transition (PENDING ->
    IN_PROGRESS -> SUCCESS/FAILED_TRANSIENT/...) so the status endpoint
    (SDD Section 8.2) sees progress as it happens, not only after the
    entire task function returns.
    """
    session = WorkerSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
