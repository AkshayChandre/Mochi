from __future__ import annotations

import sqlite3

from mochi.constants import (
    DB_PATH,
    MEMORY_EXTRACT_PROMPT,
    MEMORY_MAX_LEN,
    MEMORY_RECALL_LIMIT,
    MEMORY_TIMEOUT,
    NOTE_TO_SELF,
    QUESTION_STARTS,
    REMEMBER_TRIGGERS,
)


class MemoryStore:
    def __init__(self, path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "id INTEGER PRIMARY KEY, person TEXT, fact TEXT, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )

    def add(self, person: str | None, fact: str) -> None:
        self.conn.execute("INSERT INTO memories(person, fact) VALUES(?, ?)", (person or "", fact))
        self.conn.commit()

    def recall(self, person: str | None, limit: int = MEMORY_RECALL_LIMIT) -> list[str]:
        rows = self.conn.execute(
            "SELECT person, fact FROM memories WHERE person IN (?, '') ORDER BY id DESC LIMIT ?",
            (person or "", limit),
        ).fetchall()
        return [f"{p}: {f}" if p else f for p, f in reversed(rows)]

class Memory:
    def __init__(self, brain, store: MemoryStore) -> None:
        self.brain = brain
        self.store = store

    def explicit(self, text: str) -> str | None:
        low = text.lower().strip()
        if low.endswith("?") or low.startswith(QUESTION_STARTS):
            return None
        for trigger in (*REMEMBER_TRIGGERS, NOTE_TO_SELF):
            if (i := low.find(trigger)) != -1:
                fact = text[i + len(trigger) :].strip(" .!?")
                return fact or None
        return None

    def extract(self) -> str | None:
        turns = [m["content"] for m in self.brain.history[1:] if m["role"] == "user"][-6:]
        if not turns:
            return None
        try:
            fact = self.brain.ask_once(MEMORY_EXTRACT_PROMPT, "\n".join(turns), MEMORY_TIMEOUT)
        except Exception:
            return None
        fact = fact.strip().strip('"')
        if not fact or fact.lower().startswith("none") or len(fact) > MEMORY_MAX_LEN:
            return None
        known = " ".join(self.store.recall(self.brain.person)).lower()
        return None if fact.lower() in known else fact

    def save(self, fact: str) -> None:
        self.store.add(self.brain.person, fact)
