from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from mochi.constants import AGENDA_LIMIT, DB_PATH


def speak_when(when: datetime, now: datetime) -> str:
    clock = when.strftime("%I:%M %p").lstrip("0")
    days = (when.date() - now.date()).days
    if days == 0:
        return f"today at {clock}"
    if days == 1:
        return f"tomorrow at {clock}"
    if days < 7:
        return f"{when.strftime('%A')} at {clock}"
    return f"{when.strftime('%d %B')} at {clock}"


class Agenda:
    """Mochi's own calendar, in its own database. No account, no internet,
    nothing to expire."""

    def __init__(self, path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "id INTEGER PRIMARY KEY, title TEXT NOT NULL, at TEXT NOT NULL)"
        )
        self.conn.commit()

    def add(self, title: str, when: datetime) -> None:
        self.conn.execute(
            "INSERT INTO events(title, at) VALUES(?, ?)",
            (title.strip(), when.isoformat(timespec="minutes")),
        )
        self.conn.commit()

    def between(self, start: datetime, end: datetime) -> list[tuple[int, str, datetime]]:
        rows = self.conn.execute(
            "SELECT id, title, at FROM events WHERE at >= ? AND at < ? ORDER BY at LIMIT ?",
            (start.isoformat(timespec="minutes"), end.isoformat(timespec="minutes"), AGENDA_LIMIT),
        ).fetchall()
        return [(i, t, datetime.fromisoformat(a)) for i, t, a in rows]

    def upcoming(self, days: int, now: datetime | None = None):
        now = now or datetime.now()
        return self.between(now, now + timedelta(days=days))

    def drop(self, title: str) -> int:
        cur = self.conn.execute(
            "DELETE FROM events WHERE lower(title) LIKE ? AND at >= ?",
            (f"%{title.strip().lower()}%", datetime.now().isoformat(timespec="minutes")),
        )
        self.conn.commit()
        return cur.rowcount
