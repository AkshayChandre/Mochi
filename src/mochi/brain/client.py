"""HTTP client for the local Ollama brain server."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from mochi.config import CONNECTIONS
from mochi.constants import BRAIN_TIMEOUT, EMOTION_TAG, EMOTIONS, MAX_HISTORY, SYSTEM_PROMPT


class BrainOfflineError(RuntimeError):
    pass


class BrainClient:
    def __init__(
        self, host: str | None = None, port: int | None = None, model: str | None = None
    ) -> None:
        host = host or CONNECTIONS.brain_host
        port = port or CONNECTIONS.brain_port
        self.url = f"http://{host}:{port}/api/chat"
        self.model = model or CONNECTIONS.llm_model
        self.history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.last_emotion = "happy"

    def chat(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        payload = {"model": self.model, "messages": self.history, "stream": False}
        req = Request(self.url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=BRAIN_TIMEOUT) as resp:
                reply = json.load(resp)["message"]["content"]
        except (URLError, OSError) as err:
            self.history.pop()
            raise BrainOfflineError(f"brain unreachable at {self.url}") from err
        self.history.append({"role": "assistant", "content": reply})
        self.trim()
        return self.extract_emotion(reply)

    def extract_emotion(self, reply: str) -> str:
        match = EMOTION_TAG.match(reply)
        if match and match.group(1).lower() in EMOTIONS:
            self.last_emotion = match.group(1).lower()
            return reply[match.end() :].strip()
        self.last_emotion = "happy"
        return reply.strip()

    def trim(self) -> None:
        if len(self.history) > MAX_HISTORY:
            self.history = [self.history[0], *self.history[-(MAX_HISTORY - 1) :]]
