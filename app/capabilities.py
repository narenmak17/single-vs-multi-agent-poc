"""The three capabilities from SPEC.md, as plain functions the Flask app calls directly."""
import sqlite3
from datetime import date, datetime, time, timedelta

import models

REMINDER_WINDOW = timedelta(hours=24)


def parse_due_at(value: str) -> datetime:
    """ISO date or datetime -> datetime. A bare date means the end of that day.

    Naive values are local time; aware values are converted to local time.
    """
    try:
        return datetime.combine(date.fromisoformat(value), time.max)
    except ValueError:
        parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def create_task(conn: sqlite3.Connection, title, due_at=None) -> models.Task:
    """Capability 1. Raises ValueError on a missing title or unparseable due_at."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required")
    if due_at is not None:
        if not isinstance(due_at, str):
            raise ValueError("due_at must be an ISO date string or null")
        try:
            parse_due_at(due_at)
        except ValueError:
            raise ValueError("due_at must be an ISO date (YYYY-MM-DD) or datetime") from None
    cur = conn.execute(
        "INSERT INTO tasks (title, due_at, created_at) VALUES (?, ?, ?)",
        (title.strip(), due_at, models.utc_now_iso()),
    )
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return models.Task.from_row(row)


def mark_done(conn: sqlite3.Connection, task_id: int, done: bool) -> models.Task | None:
    """Capability 2. Returns None when the task doesn't exist."""
    cur = conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(done), task_id))
    if cur.rowcount == 0:
        return None
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return models.Task.from_row(row)


def due_soon_reminder(task: models.Task, now: datetime | None = None) -> bool:
    """Capability 3. True if not done and due within 24h — overdue tasks included."""
    if task.done or task.due_at is None:
        return False
    now = now or datetime.now()
    return parse_due_at(task.due_at) <= now + REMINDER_WINDOW
