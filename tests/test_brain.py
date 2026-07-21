import io
import json

import pytest

from mochi.brain import client as brain_client
from mochi.brain.client import BrainClient, BrainOfflineError, split_sentences


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def stream_lines(*pieces):
    lines = [
        json.dumps({"message": {"content": p}, "done": i == len(pieces) - 1})
        for i, p in enumerate(pieces)
    ]
    return FakeResponse("\n".join(lines).encode())


def test_clean_speech_drops_non_latin():
    assert brain_client.clean_speech("你好世界") == ""
    assert "Hello" in brain_client.clean_speech("Hello 你好 there")
    assert brain_client.clean_speech("Bonjour!") == "Bonjour!"


def test_split_sentences():
    done, rest = split_sentences("One. Two! Thr")
    assert done == ["One.", "Two!"]
    assert rest == " Thr"


def test_chat_sends_history_and_stores_reply(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data)
        return FakeResponse(json.dumps({"message": {"content": "hi there"}}).encode())

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1, model="test-model")
    assert bc.chat("hello") == "hi there"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["keep_alive"] == brain_client.KEEP_ALIVE
    assert captured["payload"]["messages"][-1] == {"role": "user", "content": "hello"}
    assert bc.history[-1] == {"role": "assistant", "content": "hi there"}


def test_stream_yields_sentences_and_parses_tag(monkeypatch):
    resp = stream_lines("[excited] Hel", "lo there. How", " are you?")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("hi")) == ["Hello there.", "How are you?"]
    assert bc.last_emotion == "excited"
    assert bc.history[-1]["content"] == "[excited] Hello there. How are you?"


def test_stream_routes_code_to_screen_not_speech(monkeypatch):
    resp = stream_lines("[happy] On my screen. ", "```python\nprint(1)\n``` Done.")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("code")) == ["On my screen.", "Done."]
    assert bc.last_blocks == ["print(1)"]


def test_stream_without_tag_defaults_happy(monkeypatch):
    resp = stream_lines("no tag here")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    bc.last_emotion = "sad"
    assert list(bc.chat_stream("hi")) == ["no tag here"]
    assert bc.last_emotion == "happy"


def test_stream_offline_raises_and_rolls_back(monkeypatch):
    def fake_urlopen(req, timeout):
        raise OSError("refused")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    with pytest.raises(BrainOfflineError):
        list(bc.chat_stream("hello"))
    assert len(bc.history) == 1


def test_emotion_tag_parsed_and_stripped(monkeypatch):
    def fake_urlopen(req, timeout):
        return FakeResponse(json.dumps({"message": {"content": "[excited] Let's go!"}}).encode())

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    assert bc.chat("hi") == "Let's go!"
    assert bc.last_emotion == "excited"


def test_history_trim_keeps_system_and_newest(monkeypatch):
    monkeypatch.setattr(brain_client, "MAX_HISTORY", 5)
    bc = BrainClient(host="test", port=1)
    bc.history += [{"role": "user", "content": str(i)} for i in range(10)]
    bc.trim()
    assert len(bc.history) == 5
    assert bc.history[0]["role"] == "system"
    assert bc.history[-1]["content"] == "9"
