import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.environ.get("TASKS_DB", str(Path(__file__).with_name("tasks.db")))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    due_at     TEXT,
    done       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL
)
"""


@dataclass
class Task:
    id: int
    title: str
    due_at: str | None
    done: bool
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Task":
        return cls(
            id=row["id"],
            title=row["title"],
            due_at=row["due_at"],
            done=bool(row["done"]),
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect(db_path: str | None = None) -> Iterator[sqlite3.Connection]:
    """Commit on success, roll back on error, and always close.

    sqlite3's own `with conn:` only handles the transaction; it leaves the
    connection (and on Windows, the file lock) open.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(SCHEMA)
