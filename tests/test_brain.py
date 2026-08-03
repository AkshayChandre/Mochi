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


def test_split_sentences():
    done, rest = split_sentences("One. Two! Thr")
    assert done == ["One.", "Two!"]
    assert rest == " Thr"


def test_clean_speech_drops_non_latin():
    assert brain_client.clean_speech("你好世界") == ""
    assert "Hello" in brain_client.clean_speech("Hello 你好 there")
    assert brain_client.clean_speech("Bonjour!") == "Bonjour!"


def test_clean_speech_strips_stray_emotion_tags():
    assert brain_client.clean_speech("Sure [neutral] thing") == "Sure thing"
    assert brain_client.clean_speech("*thinking* Let me see") == "Let me see"


def test_stream_yields_sentences_parses_tag_and_payload(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data)
        return stream_lines("[excited] Hel", "lo there. How", " are you?")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1, model="test-model")
    assert list(bc.chat_stream("hi")) == ["Hello there.", "How are you?"]
    assert bc.last_emotion == "excited"
    assert bc.history[-1]["content"] == "[excited] Hello there. How are you?"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["keep_alive"] == brain_client.KEEP_ALIVE
    assert captured["payload"]["options"]["num_ctx"] == 8192
    assert captured["payload"]["messages"][-1] == {"role": "user", "content": "hi"}


def test_stream_routes_code_to_screen_not_speech(monkeypatch):
    resp = stream_lines("[happy] On my screen. ", "```python\nprint(1)\n``` Done.")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("code")) == ["On my screen.", "Done."]
    assert bc.last_blocks == ["print(1)"]


def test_paren_style_tag_consumed(monkeypatch):
    resp = stream_lines("(excited) Hi there.")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("hi")) == ["Hi there."]
    assert bc.last_emotion == "excited"


def test_bare_dash_tag_consumed_even_split_across_chunks(monkeypatch):
    resp = stream_lines("neutral", " - Hi there.")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("hi")) == ["Hi there."]
    assert bc.last_emotion == "neutral"


def test_person_note_injected_transiently(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data)
        return stream_lines("[happy] Hi Ravi.")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    bc.person = "Ravi"
    list(bc.chat_stream("yo"))
    msgs = captured["payload"]["messages"]
    assert msgs[1] == {"role": "system", "content": "Ravi is talking to you right now."}
    assert len(bc.history) == 3
    assert bc.history[1]["content"] == "Ravi: yo"


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


def test_history_trim_keeps_system_and_newest(monkeypatch):
    monkeypatch.setattr(brain_client, "MAX_HISTORY", 5)
    bc = BrainClient(host="test", port=1)
    bc.history += [{"role": "user", "content": str(i)} for i in range(10)]
    bc.trim()
    assert len(bc.history) == 5
    assert bc.history[0]["role"] == "system"
    assert bc.history[-1]["content"] == "9"
