from __future__ import annotations

import re
import threading
from datetime import datetime

from mochi.constants import (
    SCREEN_QUERIES,
    TIME_QUERIES,
    TIMER_ACK,
    TIMER_DONE,
    TIMER_RE,
    TIMER_UNITS,
)
from mochi.desktop import active_window, app_name

def parse_timer(text: str) -> tuple[int, str] | None:
    match = TIMER_RE.search(text.lower())
    if not match:
        return None
    amount, unit = int(match.group(1)), match.group(2)
    seconds = amount * TIMER_UNITS[unit]
    return (seconds, f"{amount} {unit}{'s' if amount != 1 else ''}") if seconds else None

def answer_time(text: str) -> str | None:
    low = text.lower()
    if not any(q in low for q in TIME_QUERIES):
        return None
    now = datetime.now()
    if "date" in low or "day" in low:
        return f"It's {now:%A, %B %d}."
    return f"It's {now:%I:%M %p}.".lstrip("0")

def answer_screen(text: str) -> str | None:
    low = text.lower()
    if not any(q in low for q in SCREEN_QUERIES):
        return None
    title = active_window()
    if not title:
        return "I can't see your screen right now."
    return f"You're in {app_name(title)}."

class Skills:
    """Deterministic local actions, handled without the LLM so they are
    instant and cannot be hallucinated."""

    def __init__(self, speak=None) -> None:
        self.speak = speak
        self.timers: list[threading.Timer] = []

    def start_timer(self, seconds: int, label: str) -> str:
        def fire() -> None:
            if self.speak:
                self.speak(TIMER_DONE.format(label=label))

        timer = threading.Timer(seconds, fire)
        timer.daemon = True
        timer.start()
        self.timers.append(timer)
        return TIMER_ACK.format(label=label)

    def handle(self, text: str) -> str | None:
        if (parsed := parse_timer(text)) and re.search(r"\btimer|remind\b", text.lower()):
            return self.start_timer(*parsed)
        return answer_time(text) or answer_screen(text)
