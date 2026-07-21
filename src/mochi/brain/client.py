from __future__ import annotations

import json
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import Request, urlopen

from mochi.config import CONNECTIONS
from mochi.constants import (
    BRAIN_TIMEOUT,
    EMOTION_TAG,
    EMOTIONS,
    KEEP_ALIVE,
    MAX_HISTORY,
    SYSTEM_PROMPT,
)


class BrainOfflineError(RuntimeError):
    pass


def split_sentences(text: str) -> tuple[list[str], str]:
    out, start = [], 0
    for i, ch in enumerate(text):
        if ch in ".!?" and (i + 1 == len(text) or text[i + 1] in " \n"):
            out.append(text[start : i + 1].strip())
            start = i + 1
    return [s for s in out if s], text[start:]


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

    def request(self, stream: bool) -> Request:
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": stream,
            "keep_alive": KEEP_ALIVE,
        }
        return Request(self.url, json.dumps(payload).encode(), {"Content-Type": "application/json"})

    def chat(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        try:
            with urlopen(self.request(False), timeout=BRAIN_TIMEOUT) as resp:
                reply = json.load(resp)["message"]["content"]
        except (URLError, OSError) as err:
            self.history.pop()
            raise BrainOfflineError(f"brain unreachable at {self.url}") from err
        self.history.append({"role": "assistant", "content": reply})
        self.trim()
        return self.extract_emotion(reply)

    def chat_stream(self, text: str) -> Iterator[str]:
        self.history.append({"role": "user", "content": text})
        self.last_emotion = "happy"
        raw, buffer, tag_done = "", "", False
        try:
            with urlopen(self.request(True), timeout=BRAIN_TIMEOUT) as resp:
                for line in resp:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    piece = data.get("message", {}).get("content", "")
                    raw += piece
                    buffer += piece
                    if not tag_done:
                        buffer, tag_done = self.consume_tag(buffer)
                    if tag_done:
                        sentences, buffer = split_sentences(buffer)
                        yield from sentences
                    if data.get("done"):
                        break
        except (URLError, OSError) as err:
            self.history.pop()
            raise BrainOfflineError(f"brain unreachable at {self.url}") from err
        if tail := buffer.strip():
            yield tail
        self.history.append({"role": "assistant", "content": raw})
        self.trim()

    def consume_tag(self, buffer: str) -> tuple[str, bool]:
        lead = buffer.lstrip()
        if not lead:
            return buffer, False
        if not lead.startswith("["):
            return buffer, True
        end = lead.find("]")
        if end == -1:
            return (buffer, False) if len(lead) < 24 else (buffer, True)
        tag = lead[1:end].lower()
        if tag in EMOTIONS:
            self.last_emotion = tag
        return lead[end + 1 :].lstrip(), True

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
