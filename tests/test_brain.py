import io
import json
import pytest

from mochi.brain import client as brain_client
from mochi.brain.client import BrainClient, BrainOfflineError

class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

def test_chat_sends_history_and_stores_reply(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data)
        return FakeResponse(json.dumps({"message": {"content": "hi there"}}).encode())

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1, model="test-model")
    assert bc.chat("hello") == "hi there"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert captured["payload"]["messages"][-1] == {"role": "user", "content": "hello"}
    assert bc.history[-1] == {"role": "assistant", "content": "hi there"}

def test_emotion_tag_parsed_and_stripped(monkeypatch):
    def fake_urlopen(req, timeout):
        return FakeResponse(json.dumps({"message": {"content": "[excited] Let's go!"}}).encode())

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    assert bc.chat("hi") == "Let's go!"
    assert bc.last_emotion == "excited"
    assert bc.history[-1]["content"] == "[excited] Let's go!"

def test_missing_tag_defaults_to_happy(monkeypatch):
    def fake_urlopen(req, timeout):
        return FakeResponse(json.dumps({"message": {"content": "plain reply"}}).encode())

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    bc.last_emotion = "sad"
    assert bc.chat("hi") == "plain reply"
    assert bc.last_emotion == "happy"

def test_offline_raises_and_rolls_back_history(monkeypatch):
    def fake_urlopen(req, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    with pytest.raises(BrainOfflineError):
        bc.chat("hello")
    assert len(bc.history) == 1

def test_history_trim_keeps_system_and_newest(monkeypatch):
    monkeypatch.setattr(brain_client, "MAX_HISTORY", 5)
    bc = BrainClient(host="test", port=1)
    bc.history += [{"role": "user", "content": str(i)} for i in range(10)]
    bc.trim()
    assert len(bc.history) == 5
    assert bc.history[0]["role"] == "system"
    assert bc.history[-1]["content"] == "9"
