from __future__ import annotations

import sqlite3

from mochi.constants import DB_PATH, DB_TIMEOUT


def connect(path: str = DB_PATH) -> sqlite3.Connection:
    # WAL lets the ambient thread read while a timer thread writes
    conn = sqlite3.connect(path, check_same_thread=False, timeout=DB_TIMEOUT)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
