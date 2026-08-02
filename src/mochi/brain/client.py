from __future__ import annotations

import json
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import Request, urlopen

from mochi.config import CONNECTIONS
from mochi.constants import (
    BRAIN_OPTIONS,
    BRAIN_TIMEOUT,
    CODE_LANG_RE,
    EMOTIONS,
    KEEP_ALIVE,
    MAX_HISTORY,
    SPEECH_JUNK_RE,
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


def clean_speech(text: str) -> str:
    kept = SPEECH_JUNK_RE.sub("", text)
    kept = "".join(ch for ch in kept if ord(ch) < 0x2500)
    kept = " ".join(kept.split())
    return kept if any(ch.isalpha() for ch in kept) else ""


def clean_block(block: str) -> str:
    lines = block.strip("\n").splitlines()
    if lines and CODE_LANG_RE.fullmatch(lines[0].strip()):
        lines = lines[1:]
    return "\n".join(lines).strip()


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
        self.last_blocks: list[str] = []

    def chat_stream(self, text: str) -> Iterator[str]:
        self.history.append({"role": "user", "content": text})
        self.last_emotion = "happy"
        self.last_blocks = []
        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True,
            "keep_alive": KEEP_ALIVE,
            "options": BRAIN_OPTIONS,
        }
        req = Request(self.url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
        raw, pending, speak_buf, fence_buf = "", "", "", ""
        tag_done = in_fence = False
        try:
            with urlopen(req, timeout=BRAIN_TIMEOUT) as resp:
                for line in resp:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    piece = data.get("message", {}).get("content", "")
                    raw += piece
                    pending += piece
                    if not tag_done:
                        pending, tag_done = self.consume_tag(pending)
                        if not tag_done:
                            continue
                    while (marker := pending.find("```")) != -1:
                        if in_fence:
                            fence_buf += pending[:marker]
                            self.last_blocks.append(clean_block(fence_buf))
                            fence_buf = ""
                        else:
                            speak_buf += pending[:marker]
                        pending = pending[marker + 3 :]
                        in_fence = not in_fence
                    if in_fence:
                        fence_buf += pending
                    else:
                        speak_buf += pending
                        sentences, speak_buf = split_sentences(speak_buf)
                        for sentence in sentences:
                            if spoken := clean_speech(sentence):
                                yield spoken
                    pending = ""
                    if data.get("done"):
                        break
        except (URLError, OSError) as err:
            self.history.pop()
            raise BrainOfflineError(f"brain unreachable at {self.url}") from err
        if in_fence and fence_buf.strip():
            self.last_blocks.append(clean_block(fence_buf))
        if tail := clean_speech(speak_buf):
            yield tail
        self.history.append({"role": "assistant", "content": raw})
        self.trim()

    def consume_tag(self, buffer: str) -> tuple[str, bool]:
        closers = {"[": "]", "(": ")", "*": "*"}
        lead = buffer.lstrip()
        if not lead:
            return buffer, False
        closer = closers.get(lead[0])
        if closer is None:
            return buffer, True
        end = lead.find(closer, 1)
        if end == -1:
            return (buffer, False) if len(lead) < 24 else (buffer, True)
        tag = lead[1:end].strip().lower()
        if tag in EMOTIONS:
            self.last_emotion = tag
        return lead[end + 1 :].lstrip(), True

    def trim(self) -> None:
        if len(self.history) > MAX_HISTORY:
            self.history = [self.history[0], *self.history[-(MAX_HISTORY - 1) :]]
