from __future__ import annotations

from collections.abc import Callable, Iterator
from enum import Enum
from typing import Protocol

from mochi.constants import MEMORY_ASK, MEMORY_SAVED, NO_REPLY, YES_WORDS


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class WakeSource(Protocol):
    def wait(self) -> str: ...


class Transcriber(Protocol):
    def listen(self) -> str: ...


class Brain(Protocol):
    last_blocks: list[str]

    def chat_stream(self, text: str) -> Iterator[str]: ...


class Speaker(Protocol):
    def say(self, text: str) -> None: ...
    def flush(self) -> None: ...


class VoicePipeline:
    def __init__(
        self,
        wake: WakeSource,
        stt: Transcriber,
        brain: Brain,
        tts: Speaker,
        on_state: Callable[[State], None] | None = None,
        intercept: Callable[[str], str | None] | None = None,
        on_display: Callable[[str], None] | None = None,
        memory=None,
    ) -> None:
        self.wake = wake
        self.stt = stt
        self.brain = brain
        self.tts = tts
        self.on_state = on_state
        self.intercept = intercept
        self.on_display = on_display
        self.memory = memory
        self.state = State.IDLE

    def set_state(self, state: State) -> None:
        self.state = state
        if self.on_state:
            self.on_state(state)

    def converse(self) -> str:
        greeting = self.wake.wait().strip()
        parts: list[str] = []
        if greeting:
            self.set_state(State.SPEAKING)
            self.tts.say(greeting)
            self.tts.flush()
            parts.append(greeting)
        chatted = False
        while True:
            self.set_state(State.LISTENING)
            text = self.stt.listen().strip()
            if not text:
                break
            print(f"heard: {text}")
            if self.intercept and (reply := self.intercept(text)) is not None:
                self.set_state(State.SPEAKING)
                self.tts.say(reply)
                self.tts.flush()
                parts.append(reply)
                continue
            self.set_state(State.THINKING)
            chatted = True
            spoke = False
            for sentence in self.brain.chat_stream(text):
                if not spoke:
                    self.set_state(State.SPEAKING)
                    spoke = True
                self.tts.say(sentence)
                parts.append(sentence)
            if not spoke:
                self.set_state(State.SPEAKING)
                fallback = "It's on my screen." if self.brain.last_blocks else NO_REPLY
                self.tts.say(fallback)
                parts.append(fallback)
            self.tts.flush()
            if self.on_display:
                for block in self.brain.last_blocks:
                    self.on_display(block)
        if chatted and self.memory:
            self.confirm_memory()
        self.set_state(State.IDLE)
        return " ".join(parts)

    def confirm_memory(self) -> None:
        fact = self.memory.extract()
        if not fact:
            return
        self.set_state(State.SPEAKING)
        self.tts.say(MEMORY_ASK.format(fact=fact))
        self.tts.flush()
        self.set_state(State.LISTENING)
        answer = self.stt.listen().lower()
        if any(word in answer for word in YES_WORDS):
            self.memory.save(fact)
            self.set_state(State.SPEAKING)
            self.tts.say(MEMORY_SAVED)
            self.tts.flush()

    def run(self) -> None:
        while True:
            self.converse()
