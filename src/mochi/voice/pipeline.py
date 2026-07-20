from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Protocol

from mochi.constants import STATE_EMOTION

class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"

class WakeSource(Protocol):
    def wait(self) -> None: ...

class Transcriber(Protocol):
    def listen(self) -> str: ...

class Brain(Protocol):
    def chat(self, text: str) -> str: ...

class Speaker(Protocol):
    def say(self, text: str) -> None: ...

class VoicePipeline:
    def __init__(
        self,
        wake: WakeSource,
        stt: Transcriber,
        brain: Brain,
        tts: Speaker,
        on_state: Callable[[State], None] | None = None,
    ) -> None:
        self.wake = wake
        self.stt = stt
        self.brain = brain
        self.tts = tts
        self.on_state = on_state
        self.state = State.IDLE

    def set_state(self, state: State) -> None:
        self.state = state
        if self.on_state:
            self.on_state(state)

    def emotion(self) -> str:
        return STATE_EMOTION[self.state.value]

    def converse(self) -> str:
        self.wake.wait()
        last = ""
        while True:
            self.set_state(State.LISTENING)
            text = self.stt.listen().strip()
            if not text:
                break
            self.set_state(State.THINKING)
            reply = self.brain.chat(text)
            self.set_state(State.SPEAKING)
            self.tts.say(reply)
            last = reply
        self.set_state(State.IDLE)
        return last

    def run(self) -> None:
        while True:
            self.converse()
