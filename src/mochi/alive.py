from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable

from mochi.constants import (
    AMBIENT_TICK,
    AWAY_SECONDS,
    BREAK_LINES,
    QUIET_COOLDOWN,
    QUIET_LINES,
    QUIET_SECONDS,
    STARE_COOLDOWN,
    STARE_LINES,
    STARE_SECONDS,
    WELCOME_BACK_LINES,
    WORK_COOLDOWN,
    WORK_SESSION_SECONDS,
)


class Ambient:
    def __init__(
        self,
        speak: Callable[[str, str], None],
        presence=None,
        busy: Callable[[], bool] = lambda: False,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.speak = speak
        self.presence = presence
        self.busy = busy
        self.now = now
        start = now()
        self.seen_since = 0.0
        self.last_seen = start  # no "welcome back" on the very first sighting
        self.last_spoke = start
        self.session_start = start
        self.fired: dict[str, float] = {}

    def ready(self, key: str, cooldown: float) -> bool:
        return self.now() - self.fired.get(key, -cooldown) >= cooldown

    def fire(self, key: str, lines) -> None:
        line, emotion = random.choice(lines)
        self.fired[key] = self.now()
        self.speak(line, emotion)

    def noticed_speech(self) -> None:
        self.last_spoke = self.now()

    def tick(self, present: bool) -> None:
        now = self.now()
        if present:
            away = now - self.last_seen
            if self.seen_since == 0.0:
                self.seen_since = now
                if away > AWAY_SECONDS and self.ready("welcome", AWAY_SECONDS):
                    self.fire("welcome", WELCOME_BACK_LINES)
                    return
            self.last_seen = now
        else:
            self.seen_since = 0.0
            return

        staring = now - self.seen_since
        quiet = now - self.last_spoke
        if staring >= STARE_SECONDS and quiet >= STARE_SECONDS and self.ready(
            "stare", STARE_COOLDOWN
        ):
            self.fire("stare", STARE_LINES)
        elif quiet >= QUIET_SECONDS and self.ready("quiet", QUIET_COOLDOWN):
            self.fire("quiet", QUIET_LINES)
        elif now - self.session_start >= WORK_SESSION_SECONDS and self.ready(
            "break", WORK_COOLDOWN
        ):
            self.fire("break", BREAK_LINES)

    def loop(self) -> None:
        while True:
            time.sleep(AMBIENT_TICK)
            try:
                if self.presence is None or self.busy():
                    continue
                self.tick(self.presence.whos_there(tries=1)[1])
            except Exception as err:
                print(f"ambient skipped: {err!r}")

    def start(self) -> None:
        threading.Thread(target=self.loop, daemon=True).start()
