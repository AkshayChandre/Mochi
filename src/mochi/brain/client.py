from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mochi.config import CONNECTIONS
from mochi.constants import (
    BRAIN_OPTIONS,
    BRAIN_TIMEOUT,
    CLAUSE_MIN_CHARS,
    CODE_LANG_RE,
    EMOTION_HINTS,
    EMOTIONS,
    ENGLISH_ONLY_REPLY,
    HISTORY_KEEP,
    KEEP_ALIVE,
    LATIN_MAX,
    MAX_HISTORY,
    MAX_TOOL_ROUNDS,
    NOW_NOTE,
    SPEECH_JUNK_RE,
    SYSTEM_PROMPT,
    TAG_SCAN_MAX,
    TOOL_WAIT_LINES,
    TOOLLESS_MODEL,
)
from mochi.tools import TOOLS


class BrainOfflineError(RuntimeError):
    pass

def explain(err: Exception, url: str, model: str) -> str:
    """HTTPError is a subclass of URLError, so ollama answering 'that model
    does not support tools' used to arrive looking exactly like a dead
    server. Say which one it actually was, and quote ollama."""
    if isinstance(err, HTTPError):
        try:
            detail = json.loads(err.read()).get("error", "")
        except (OSError, ValueError, AttributeError):
            detail = ""
        detail = " ".join(detail.split())[:200] or err.reason
        if "does not support tools" in detail:
            return TOOLLESS_MODEL.format(model=model, detail=detail)
        return f"{model}: ollama said {err.code}, {detail}"
    return f"brain unreachable at {url} ({err})"

def split_sentences(text: str, eager: bool = False) -> tuple[list[str], str]:
    """eager breaks the first chunk at a comma so Mochi starts talking a
    clause earlier; waiting for the full stop is what made it feel slow."""
    out, start = [], 0
    for i, ch in enumerate(text):
        if ch in ".!?" and (i + 1 == len(text) or text[i + 1] in " \n"):
            out.append(text[start : i + 1].strip())
            start = i + 1
    rest = text[start:]
    if eager and not out and (cut := rest.rfind(",")) >= CLAUSE_MIN_CHARS:
        return [rest[: cut + 1].strip()], rest[cut + 1 :]
    return [s for s in out if s], rest

def clean_speech(text: str) -> str:
    # Piper speaks English only: anything past Latin Extended-B (Telugu,
    # Devanagari, CJK, Arabic...) would be voiced as gibberish.
    kept = SPEECH_JUNK_RE.sub("", text)
    kept = "".join(ch for ch in kept if ord(ch) <= LATIN_MAX)
    kept = " ".join(kept.split())
    return kept if any(ch.isalpha() for ch in kept) else ""

def guess_emotion(text: str) -> str:
    """Fallback when the model forgets its emotion tag, which a 3b model
    does often; a flat 'happy' every turn reads as dead."""
    low = text.lower()
    for cues, emotion in EMOTION_HINTS:
        if any(cue in low for cue in cues):
            return emotion
    return "neutral"

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
        self.base = f"http://{host}:{port}"
        self.url = f"{self.base}/api/chat"
        self.model = model or CONNECTIONS.llm_model
        self.history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.last_emotion = "neutral"
        self.tagged = False
        self.last_blocks: list[str] = []
        self.person: str | None = None
        self.store = None
        self.toolbox = None
        self.verbose = True
        self.calls: list[dict] = []
        self.stats: dict = {}
        self.first_word = 0.0
        self.turn_started = 0.0

    def request(self, msgs: list[dict], stream: bool, options: dict | None = None) -> Request:
        payload = {
            "model": self.model,
            "messages": msgs,
            "stream": stream,
            "keep_alive": KEEP_ALIVE,
            "options": options or BRAIN_OPTIONS,
        }
        # The schemas ride along on the answering pass too. Dropping them
        # would change the system block and cost a full prompt re-read for
        # the sake of a few hundred cached tokens.
        if self.toolbox:
            payload["tools"] = TOOLS
        return Request(self.url, json.dumps(payload).encode(), {"Content-Type": "application/json"})

    def apply_tools(self, msgs: list[dict], calls: list[dict]) -> None:
        # history too, or the turn after a look cannot say what it saw
        asked = {"role": "assistant", "content": "", "tool_calls": calls}
        msgs.append(asked)
        self.history.append(asked)
        for call in calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            args = self.toolbox.parse_args(fn.get("arguments"))
            result = self.toolbox.run(name, args)
            if self.verbose:
                print(f"tool {name}({args}) -> {result}")
            answered = {"role": "tool", "name": name, "content": result}
            msgs.append(answered)
            self.history.append(answered)

    def waiting_line(self, calls: list[dict]) -> str:
        for call in calls:
            if line := TOOL_WAIT_LINES.get(call.get("function", {}).get("name", "")):
                return line
        return ""

    def mark_first(self) -> None:
        if not self.first_word:
            self.first_word = time.monotonic() - self.turn_started

    def tally(self, done: dict) -> None:
        """Ollama reports what it actually re-read. A prompt count that stays
        small across a conversation means the cache is holding; one that
        matches the whole prompt every turn means it is not."""
        for key in ("prompt_eval_count", "eval_count"):
            self.stats[key] = self.stats.get(key, 0) + done.get(key, 0)
        for key, into in (("prompt_eval_duration", "prompt"), ("eval_duration", "write")):
            self.stats[into] = self.stats.get(into, 0.0) + done.get(key, 0) / 1e9

    def note(self) -> str:
        """Deliberately the date and not the clock. This line sits inside the
        cached prefix, so anything that changes by the minute would throw the
        whole system prompt and tool schema away on every turn. The clock is
        a tool call away when it is actually wanted."""
        note = NOW_NOTE.format(today=datetime.now().strftime("%A %d %B %Y"))
        if self.person:
            note += f" {self.person} is talking to you right now."
        return note

    def chat_stream(self, text: str) -> Iterator[str]:
        spoken_by = f"{self.person}: {text}" if self.person else text
        self.history.append({"role": "user", "content": spoken_by})
        self.last_emotion = "neutral"
        self.tagged = False
        self.last_blocks = []
        msgs = list(self.history)
        # The note is pinned at index 1 and every later turn appends only at
        # the end, so the whole prompt above the new question stays
        # byte-identical and ollama re-reads none of it. Putting it anywhere
        # further down shifts the messages under it and costs a full re-read
        # of the system prompt and all 17 tool schemas, every single turn.
        msgs.insert(1, {"role": "system", "content": self.note()})
        self.stats = {}
        self.first_word = 0.0
        started = self.turn_started = time.monotonic()
        yield from self.stream(msgs)
        rounds = 0
        # a second round used to be collected and then dropped on the floor
        while self.calls and rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            if line := self.waiting_line(self.calls):
                self.mark_first()
                yield line
            self.apply_tools(msgs, self.calls)
            yield from self.stream(msgs)
        if self.verbose:
            print(self.report(time.monotonic() - started))

    def report(self, seconds: float) -> str:
        read, reading = self.stats.get("prompt_eval_count", 0), self.stats.get("prompt", 0.0)
        wrote, writing = self.stats.get("eval_count", 0), self.stats.get("write", 0.0)
        rate = f"{wrote / writing:.1f} tok/s" if writing else "?"
        # first word is the number that matches what the silence feels like
        first = f"{self.first_word:.1f}s" if self.first_word else "never"
        return (
            f"first word at {first} | reply took {seconds:.1f}s "
            f"| read {read} tok in {reading:.1f}s | wrote {wrote} tok in {writing:.1f}s ({rate})"
        )

    def warm_up(self) -> None:
        """The system prompt and 17 tool schemas cost ~20s to read on a cold
        cache, and the owner pays it on their first question. Send the same
        prefix at startup so ollama has it cached before anyone speaks."""
        msgs = [
            self.history[0],
            {"role": "system", "content": self.note()},
            {"role": "user", "content": "hi"},
        ]
        try:
            with urlopen(
                self.request(msgs, stream=False, options={**BRAIN_OPTIONS, "num_predict": 1}),
                timeout=BRAIN_TIMEOUT,
            ):
                pass
        except OSError:
            pass  # offline is the app's problem to report, not the warmup's

    def stream(self, msgs: list[dict]) -> Iterator[str]:
        self.calls = []
        req = self.request(msgs, stream=True)
        raw, pending, speak_buf, fence_buf = "", "", "", ""
        tag_done = in_fence = said_any = False
        try:
            with urlopen(req, timeout=BRAIN_TIMEOUT) as resp:
                for line in resp:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    message = data.get("message", {})
                    if data.get("done"):  # before the tag guard below, which
                        self.tally(data)  # can skip the rest of the loop
                    if tool_calls := message.get("tool_calls"):
                        self.calls.extend(tool_calls)
                    piece = message.get("content", "")
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
                        sentences, speak_buf = split_sentences(speak_buf, eager=not said_any)
                        for sentence in sentences:
                            if spoken := clean_speech(sentence):
                                said_any = True
                                self.mark_first()
                                yield spoken
                    pending = ""
                    if data.get("done"):
                        break
        except (URLError, OSError) as err:
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            raise BrainOfflineError(explain(err, self.url, self.model)) from err
        if in_fence and fence_buf.strip():
            self.last_blocks.append(clean_block(fence_buf))
        if tail := clean_speech(speak_buf):
            self.mark_first()
            yield tail
            said_any = True
        if not raw.strip():  # a tool-only turn says nothing yet
            return
        if not said_any and not self.calls and not self.last_blocks:
            # every sentence stripped to nothing, so say something
            self.mark_first()
            yield ENGLISH_ONLY_REPLY
        if not self.tagged:
            self.last_emotion = guess_emotion(raw)
        self.history.append({"role": "assistant", "content": raw})
        self.trim()

    def ask_once(self, system: str, user: str, timeout: int = BRAIN_TIMEOUT) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "keep_alive": KEEP_ALIVE,
            "options": BRAIN_OPTIONS,
        }
        req = Request(self.url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            return json.load(resp)["message"]["content"].strip()

    def consume_tag(self, buffer: str) -> tuple[str, bool]:
        closers = {"[": "]", "(": ")", "*": "*"}
        lead = buffer.lstrip()
        if not lead:
            return buffer, False
        closer = closers.get(lead[0])
        if closer is None:
            return self.consume_bare_tag(buffer, lead)
        end = lead.find(closer, 1)
        if end == -1:
            return (buffer, False) if len(lead) < TAG_SCAN_MAX else (buffer, True)
        tag = lead[1:end].strip().lower()
        if tag in EMOTIONS:
            self.last_emotion = tag
            self.tagged = True
        return lead[end + 1 :].lstrip(), True

    def consume_bare_tag(self, buffer: str, lead: str) -> tuple[str, bool]:
        low = lead.lower()
        for emo in EMOTIONS:
            if low.startswith(emo):
                after = lead[len(emo) :].lstrip()
                if not after:
                    return buffer, False
                if after[0] in ":-.\u2013\u2014":
                    self.last_emotion = emo
                    self.tagged = True
                    return after[1:].lstrip(), True
                return buffer, True
            if emo.startswith(low):
                return buffer, False
        return buffer, True

    def trim(self) -> None:
        if len(self.history) <= MAX_HISTORY:
            return
        kept = self.history[-HISTORY_KEEP:]
        # a tool result whose call got cut off above it is a 400 from ollama
        while kept and kept[0]["role"] == "tool":
            kept.pop(0)
        self.history = [self.history[0], *kept]
