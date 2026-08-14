from __future__ import annotations

import json
from datetime import datetime

from mochi import world
from mochi.agenda import speak_when
from mochi.constants import (
    AGENDA_ADDED,
    AGENDA_BAD_TIME,
    AGENDA_DAYS,
    AGENDA_DROPPED,
    AGENDA_EMPTY,
    AGENDA_NOT_FOUND,
    COUNTDOWN_MAX,
    DEGREES_RE,
    OWNER_CITY,
)


def spec(tool: str, about: str, /, **params) -> dict:
    required = [k for k, v in params.items() if v.pop("required", False)]
    return {
        "type": "function",
        "function": {
            "name": tool,
            "description": about,
            "parameters": {"type": "object", "properties": params, "required": required},
        },
    }


TOOLS = [
    spec(
        "get_time",
        "Current date and time. Give a place only if the user asked about another city or country.",
        place={"type": "string", "description": "city or country, empty for local"},
    ),
    spec(
        "what_is_on_screen",
        "Which app and file or page the owner is looking at right now.",
    ),
    spec(
        "set_reminder",
        "Remind the owner about something after a delay. Ask first if you do not know when.",
        task={"type": "string", "description": "what to remind about", "required": True},
        minutes={"type": "number", "description": "delay in minutes", "required": True},
    ),
    spec("list_reminders", "What reminders are pending."),
    spec("cancel_reminders", "Cancel every pending reminder."),
    spec(
        "count_down",
        "Count down out loud from a number, one number per second, showing each on the face.",
        start={"type": "number", "description": "number to count down from", "required": True},
    ),
    spec(
        "remember",
        "Save a fact about the person for future conversations.",
        fact={"type": "string", "description": "the fact, in a short sentence", "required": True},
    ),
    spec(
        "recall",
        "Look up what you already know about the person. Use before claiming you know nothing.",
        topic={"type": "string", "description": "optional subject to filter by"},
    ),
    spec(
        "show_expression",
        "Play an expression on your face when it adds to what you are saying.",
        name={"type": "string", "description": "happy, sad, angry, love, shy", "required": True},
    ),
    spec("go_to_sleep", "Close your eyes and sleep, when the owner says goodbye or goodnight."),
    spec(
        "gesture",
        "Nod or shake your head. Use it when you agree, disagree, or answer yes or no.",
        kind={"type": "string", "description": "nod or shake", "required": True},
    ),
    spec(
        "add_event",
        "Put something on the owner's calendar. Work out the exact date and time "
        "yourself from what they said and the current time you were given.",
        title={"type": "string", "description": "what the event is", "required": True},
        when={
            "type": "string",
            "description": "exact start, ISO format, e.g. 2026-08-14T15:00",
            "required": True,
        },
    ),
    spec(
        "list_events",
        "What is coming up on the owner's calendar.",
        days={"type": "number", "description": "how many days ahead to look, default 7"},
    ),
    spec(
        "cancel_event",
        "Remove an upcoming event from the calendar.",
        title={"type": "string", "description": "words from the event title", "required": True},
    ),
    spec(
        "weather",
        "Real current weather. Leave the place empty for where the owner lives.",
        place={"type": "string", "description": "city or country, empty for home"},
    ),
    spec("news", "Today's real headlines, when asked what is happening in the world."),
    spec(
        "look_up",
        "Look up a real fact about a person, place, thing or event. Use this instead "
        "of guessing whenever you are not certain.",
        topic={"type": "string", "description": "what to look up", "required": True},
    ),
]


class Toolbox:
    """Executes what the model decides to do. No intent parsing lives here:
    the model picks the tool, this just runs it."""

    def __init__(self, skills, sensors, memory=None, face=None, agenda=None) -> None:
        self.skills = skills
        self.sensors = sensors
        self.memory = memory
        self.face = face
        self.agenda = agenda

    def get_time(self, place: str = "") -> str:
        when, where = self.sensors.clock(place)
        return f"{when} in {where}" if where else when

    def what_is_on_screen(self) -> str:
        app, doc = self.sensors.screen()
        if not app:
            return "screen not visible"
        return f"app: {app}, showing: {doc}" if doc else f"app: {app}"

    def set_reminder(self, task: str, minutes: float = 1) -> str:
        seconds = max(1, int(float(minutes) * 60))
        label = f"{minutes:g} minute{'s' if float(minutes) != 1 else ''}"
        return self.skills.start_timer(seconds, label, task=task)

    def list_reminders(self) -> str:
        return self.skills.list_pending()

    def cancel_reminders(self) -> str:
        return self.skills.cancel_all()

    def count_down(self, start: float = 5) -> str:
        return self.skills.count_down(min(COUNTDOWN_MAX, max(1, int(start))))

    def remember(self, fact: str) -> str:
        if self.memory:
            self.memory.save(fact)
        return f"saved: {fact}"

    def recall(self, topic: str = "") -> str:
        if not self.memory:
            return "nothing stored"
        facts = self.memory.store.recall(getattr(self.memory.brain, "person", None))
        hits = [f for f in facts if not topic or topic.lower() in f.lower()]
        return "; ".join(hits) if hits else "nothing stored about that"

    def show_expression(self, name: str) -> str:
        if self.face:
            try:
                self.face.set_emotion(name.lower().strip())
            except ValueError:
                return f"no expression called {name}"
        return f"showing {name}"

    def go_to_sleep(self) -> str:
        if self.face:
            self.face.set_emotion("sleeping")
        return "eyes closed"

    def gesture(self, kind: str) -> str:
        kind = kind.lower().strip()
        if self.face:
            try:
                self.face.play_gesture(kind)
            except ValueError:
                return f"I can't do a {kind}"
        return f"did a {kind}"

    def add_event(self, title: str, when: str) -> str:
        try:
            at = datetime.fromisoformat(str(when).strip())
        except ValueError:
            return AGENDA_BAD_TIME
        self.agenda.add(title, at)
        if self.face:
            self.face.show_banner(title)
        return AGENDA_ADDED.format(title=title, when=speak_when(at, datetime.now()))

    def list_events(self, days: float = AGENDA_DAYS) -> str:
        span = max(1, int(days))
        events = self.agenda.upcoming(span)
        if not events:
            return AGENDA_EMPTY.format(days=span)
        now = datetime.now()
        return "; ".join(f"{title} {speak_when(at, now)}" for _, title, at in events)

    def cancel_event(self, title: str) -> str:
        gone = self.agenda.drop(title)
        if not gone:
            return AGENDA_NOT_FOUND
        return AGENDA_DROPPED.format(count=gone, s="" if gone == 1 else "s")

    def weather(self, place: str = "") -> str:
        report = world.weather(place.strip() or OWNER_CITY)
        if self.face and (hit := DEGREES_RE.search(report)):
            self.face.show_banner(hit.group(1) + "°")
        return report

    def news(self) -> str:
        return world.headlines()

    def look_up(self, topic: str) -> str:
        return world.look_up(topic)

    def run(self, name: str, args: dict) -> str:
        handler = getattr(self, name, None)
        if handler is None:
            return f"no tool called {name}"
        try:
            return str(handler(**args))
        except Exception as err:
            return f"tool {name} failed: {err}"

    @staticmethod
    def parse_args(raw) -> dict:
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {}
