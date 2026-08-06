import os
import sqlite3
from contextlib import contextmanager
from typing import List

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
"""


@contextmanager
def _connect(db_path: str = None):
    db_path = db_path or settings.session_db_path
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def append(session_id: str, role: str, content: str, db_path: str = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_history(session_id: str, db_path: str = None) -> List[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def reset(session_id: str, db_path: str = None) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
