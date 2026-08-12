from __future__ import annotations

import re
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from mochi.constants import (
    CITY_TZ,
    ENGLISH_ONLY_REPLY,
    LANGUAGE_CUES,
    LANGUAGE_WORDS,
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

def find_zone(text: str) -> tuple[str, str] | None:
    for city, zone in CITY_TZ.items():
        if city in text:
            return city, zone
    return None


def answer_time(text: str) -> str | None:
    low = text.lower()
    if not any(q in low for q in TIME_QUERIES):
        return None
    now = datetime.now()
    where = ""
    if place := find_zone(low):
        city, zone = place
        try:
            now = datetime.now(ZoneInfo(zone))
            where = f" in {city.title()}"
        except Exception:
            return None
    if "date" in low or "day" in low:
        return f"It's {now:%A, %B %d}{where}."
    return f"It's {now:%I:%M %p}{where}.".lstrip("0")


def answer_language(text: str) -> str | None:
    low = text.lower()
    if not any(word in low for word in LANGUAGE_WORDS):
        return None
    return ENGLISH_ONLY_REPLY if any(cue in low for cue in LANGUAGE_CUES) else None

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
        reply = answer_language(text) or answer_time(text) or answer_screen(text)
        if reply:
            print(f"skill -> {reply}")
        return reply
