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
        # paired: two lists let an out-of-order timer shift every label along
        self.timers: list[tuple[threading.Timer, str]] = []

    def emote(self) -> None:
        if self.set_emotion:
            self.set_emotion("excited")

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
        self.timers.append((timer, task or label))
        self.emote()
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
        self.emote()
        return f"counting down from {start}"

    def pending(self) -> list[str]:
        self.timers = [pair for pair in self.timers if pair[0].is_alive()]
        return [label for _, label in self.timers]

    def cancel_all(self) -> str:
        live = self.pending()
        if not live:
            return CANCEL_NONE
        for timer, _ in self.timers:
            timer.cancel()
        count = len(live)
        self.timers = []
        return CANCEL_DONE.format(count=count, word="reminder" if count == 1 else "reminders")

    def list_pending(self) -> str:
        live = self.pending()
        if not live:
            return NO_TIMERS
        if len(live) == 1:
            return PENDING_ONE.format(task=live[0])
        return PENDING_MANY.format(count=len(live), tasks=", ".join(live))
