from __future__ import annotations

import re
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from mochi.constants import (
    CITY_TZ,
    ENGLISH_ONLY_REPLY,
    FAREWELL_WORDS,
    GOODBYE_REPLY,
    LANGUAGE_CUES,
    LANGUAGE_WORDS,
    SCREEN_WORDS,
    SELF_WORDS,
    SKILL_EMOTIONS,
    TIME_QUERIES,
    TIMER_ACK,
    TIMER_DONE,
    TIMER_RE,
    TIMER_UNITS,
)
from mochi.desktop import active_window, app_name, document_name


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
    if not (any(w in low for w in SCREEN_WORDS) and any(s in low for s in SELF_WORDS)):
        return None
    title = active_window()
    print(f"window title: {title!r}")
    if not title:
        return "I can't see your screen right now."
    doc = document_name(title)
    return f"You're in {app_name(title)}, on {doc}." if doc else f"You're in {app_name(title)}."


def answer_farewell(text: str) -> str | None:
    low = text.lower().strip(" .!?")
    words = low.split()
    if any(low.startswith(w) or low.endswith(w) for w in FAREWELL_WORDS) and len(words) <= 6:
        return GOODBYE_REPLY
    return None

class Skills:
    """Deterministic local actions, handled without the LLM so they are
    instant and cannot be hallucinated."""

    def __init__(self, speak=None, set_emotion=None) -> None:
        self.speak = speak
        self.set_emotion = set_emotion
        self.timers: list[threading.Timer] = []

    def emote(self, kind: str) -> None:
        if self.set_emotion:
            self.set_emotion(SKILL_EMOTIONS[kind])

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
            self.emote("timer")
            return self.start_timer(*parsed)
        for kind, reply in (
            ("bye", answer_farewell(text)),
            ("time", answer_language(text)),
            ("time", answer_time(text)),
            ("screen", answer_screen(text)),
        ):
            if reply:
                self.emote(kind)
                print(f"skill -> {reply}")
                return reply
        return None
