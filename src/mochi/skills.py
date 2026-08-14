from __future__ import annotations

import threading
import time

from mochi.constants import (
    CANCEL_DONE,
    CANCEL_NONE,
    COUNTDOWN_DONE,
    COUNTDOWN_GAP,
    NO_TIMERS,
    OWNER_NAME,
    PENDING_MANY,
    PENDING_ONE,
    REMINDER_ACK,
    REMINDER_DONE,
    SKILL_EMOTIONS,
    TIMER_ACK,
    TIMER_DONE,
)


class Skills:
    """Actions Mochi can perform. Intent detection lives in the model now;
    these only execute and report back."""

    def __init__(self, speak=None, set_emotion=None, show=None) -> None:
        self.speak = speak
        self.set_emotion = set_emotion
        self.show = show
        self.timers: list[threading.Timer] = []
        self.tasks: list[str] = []

    def emote(self, kind: str) -> None:
        if self.set_emotion:
            self.set_emotion(SKILL_EMOTIONS[kind])

    def start_timer(self, seconds: int, label: str, task: str = "") -> str:
        message = (
            REMINDER_DONE.format(owner=OWNER_NAME, task=task)
            if task
            else TIMER_DONE.format(label=label)
        )

        def fire() -> None:
            if self.speak:
                self.speak(message)

        timer = threading.Timer(seconds, fire)
        timer.daemon = True
        timer.start()
        self.timers.append(timer)
        self.tasks.append(task or label)
        self.emote("timer")
        if task:
            return REMINDER_ACK.format(task=task, label=label)
        return TIMER_ACK.format(label=label)

    def count_down(self, start: int) -> str:
        def run() -> None:
            for n in range(start, 0, -1):
                if self.show:
                    self.show(str(n))
                if self.speak:
                    self.speak(str(n))
                time.sleep(COUNTDOWN_GAP)
            if self.show:
                self.show("0")
            if self.speak:
                self.speak(COUNTDOWN_DONE)

        threading.Thread(target=run, daemon=True).start()
        self.emote("timer")
        return f"counting down from {start}"

    def pending(self) -> list[str]:
        self.timers = [t for t in self.timers if t.is_alive()]
        self.tasks = self.tasks[-len(self.timers) :] if self.timers else []
        return self.tasks

    def cancel_all(self) -> str:
        live = self.pending()
        if not live:
            return CANCEL_NONE
        for timer in self.timers:
            timer.cancel()
        count = len(live)
        self.timers, self.tasks = [], []
        return CANCEL_DONE.format(count=count, word="reminder" if count == 1 else "reminders")

    def list_pending(self) -> str:
        live = self.pending()
        if not live:
            return NO_TIMERS
        if len(live) == 1:
            return PENDING_ONE.format(task=live[0])
        return PENDING_MANY.format(count=len(live), tasks=", ".join(live))
