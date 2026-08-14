import io
import json
from datetime import datetime

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
    assert captured["payload"]["options"]["num_ctx"] == brain_client.BRAIN_OPTIONS["num_ctx"]
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
    assert msgs[1] == {"role": "system", "content": bc.note()}
    assert "Ravi is talking to you right now." in msgs[1]["content"]
    assert msgs[-1] == {"role": "user", "content": "Ravi: yo"}
    assert len(bc.history) == 3
    assert bc.history[1]["content"] == "Ravi: yo"

def test_note_carries_the_date_but_never_the_clock(monkeypatch):
    """The clock would change this line every minute, and it sits inside the
    cached prefix. Date only; the time is a tool call."""
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data)
        return stream_lines("[happy] Sure.")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    list(bc.chat_stream("what day is it"))
    note = captured["payload"]["messages"][1]["content"]
    assert datetime.now().strftime("%A") in note
    assert datetime.now().strftime("%Y") in note
    assert ":" not in note and "AM" not in note and "PM" not in note

def test_prompt_prefix_is_stable_across_turns(monkeypatch):
    """The bug that made every reply take 30 seconds. Ollama reuses its
    cached prompt only for the messages that are byte-identical from the
    front. Anything that shifts them - a note placed low, a trim every turn -
    forces a full re-read of the system prompt and all 17 tool schemas."""
    sent = []

    def fake_urlopen(req, timeout):
        sent.append(json.loads(req.data)["messages"])
        return stream_lines("[happy] Fine.")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    bc.person = "Akshay"
    for turn in ("one", "two", "three"):
        list(bc.chat_stream(turn))
    for earlier, later in zip(sent, sent[1:], strict=False):
        assert later[: len(earlier)] == earlier, "prompt prefix shifted between turns"

def test_context_is_not_force_fed_every_turn(monkeypatch):
    """Facts reach the model through tools now: nothing about the date, the
    screen or stored memories is injected unasked."""
    captured = {}

    def fake_urlopen(req, timeout):
        captured["payload"] = json.loads(req.data)
        return stream_lines("[happy] Hi.")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)

    class Store:
        def recall(self, person):
            return ["Akshay: likes tea"]

    bc.store = Store()
    list(bc.chat_stream("yo"))
    blob = " ".join(m["content"] for m in captured["payload"]["messages"])
    assert "likes tea" not in blob
    assert "It is" not in blob


def test_tool_call_runs_then_model_answers(monkeypatch):
    calls = []

    class Box:
        parse_args = staticmethod(lambda raw: raw or {})

        def run(self, name, args):
            calls.append((name, args))
            return "09:00 AM"

    responses = [
        FakeResponse(
            json.dumps(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [{"function": {"name": "get_time", "arguments": {}}}],
                    }
                }
            ).encode()
        ),
        stream_lines("[happy] It's nine in the morning."),
    ]
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: responses.pop(0))
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Box()
    assert list(bc.chat_stream("what time is it")) == ["It's nine in the morning."]
    assert calls == [("get_time", {})]


def test_no_tool_needed_still_answers(monkeypatch):
    class Box:
        parse_args = staticmethod(lambda raw: raw or {})

        def run(self, name, args):
            raise AssertionError("should not run a tool")

    resp = FakeResponse(json.dumps({"message": {"content": "[happy] Hello there."}}).encode())
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Box()
    assert list(bc.chat_stream("hi")) == ["Hello there."]
    assert bc.last_emotion == "happy"

def test_untagged_reply_gets_guessed_emotion(monkeypatch):
    resp = stream_lines("Sorry, I can't help with that")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("hi")) == ["Sorry, I can't help with that"]
    assert bc.last_emotion == "sad"
    assert not bc.tagged

def test_stream_offline_raises_and_rolls_back(monkeypatch):
    def fake_urlopen(req, timeout):
        raise OSError("refused")

    monkeypatch.setattr(brain_client, "urlopen", fake_urlopen)
    bc = BrainClient(host="test", port=1)
    with pytest.raises(BrainOfflineError):
        list(bc.chat_stream("hello"))
    assert len(bc.history) == 1

def test_history_trim_keeps_system_and_newest(monkeypatch):
    monkeypatch.setattr(brain_client, "MAX_HISTORY", 8)
    monkeypatch.setattr(brain_client, "HISTORY_KEEP", 4)
    bc = BrainClient(host="test", port=1)
    bc.history += [{"role": "user", "content": str(i)} for i in range(10)]
    bc.trim()
    assert len(bc.history) == 5
    assert bc.history[0]["role"] == "system"
    assert bc.history[-1]["content"] == "9"

def test_trim_drops_a_batch_so_it_is_not_paid_every_turn(monkeypatch):
    """Trimming one message per turn shifts the whole prompt every turn and
    throws away the cached prefix each time. Drop a batch, then coast."""
    monkeypatch.setattr(brain_client, "MAX_HISTORY", 8)
    monkeypatch.setattr(brain_client, "HISTORY_KEEP", 4)
    bc = BrainClient(host="test", port=1)
    bc.history += [{"role": "user", "content": str(i)} for i in range(8)]
    bc.trim()
    trims = 0
    for i in range(8, 16):
        bc.history.append({"role": "user", "content": str(i)})
        before = len(bc.history)
        bc.trim()
        trims += len(bc.history) != before
    assert trims <= 2, "trimming on nearly every turn defeats the prompt cache"

def test_first_clause_is_spoken_without_waiting_for_the_full_stop():
    # eager only applies to the opening chunk, which is the one the user
    # is sat there waiting for
    said, rest = split_sentences("Let me think about that, it is a good question", eager=True)
    assert said == ["Let me think about that,"]
    assert rest == " it is a good question"

def test_eager_ignores_a_comma_that_arrives_too_early():
    assert split_sentences("Yes, absolutely", eager=True) == ([], "Yes, absolutely")

def test_normal_split_never_breaks_on_commas():
    assert split_sentences("Hello, there. Bye.") == (["Hello, there.", "Bye."], "")

def test_only_the_opening_chunk_is_eager(monkeypatch):
    """The first clause goes out early; after that, commas are just commas."""
    resp = stream_lines(
        "[happy] Let me think about that,",
        " it is a good question.",
        " And then, later on, more.",
    )
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("go")) == [
        "Let me think about that,",
        "it is a good question.",
        "And then, later on, more.",
    ]

def test_a_whole_sentence_in_one_chunk_is_not_chopped_at_a_comma(monkeypatch):
    resp = stream_lines("[happy] Sure thing, here we go.")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    assert list(bc.chat_stream("go")) == ["Sure thing, here we go."]

def test_both_passes_are_counted_in_the_report(monkeypatch):
    """The tool pass emits no text, so its counters used to be skipped and
    the timing line under-reported what the model actually re-read."""
    seq = [
        FakeResponse(
            json.dumps(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [{"function": {"name": "news", "arguments": {}}}],
                    },
                    "done": True,
                    "prompt_eval_count": 1700,
                    "eval_count": 12,
                }
            ).encode()
        ),
        FakeResponse(
            json.dumps(
                {
                    "message": {"content": "[happy] Big news."},
                    "done": True,
                    "prompt_eval_count": 40,
                    "eval_count": 8,
                }
            ).encode()
        ),
    ]
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: seq.pop(0))

    class Box:
        parse_args = staticmethod(lambda raw: raw or {})

        def run(self, name, args):
            return "one; two"

    bc = BrainClient(host="test", port=1)
    bc.toolbox = Box()
    assert list(bc.chat_stream("news")) == ["Big news."]
    assert bc.stats["prompt_eval_count"] == 1740
    assert bc.stats["eval_count"] == 20
    assert "1740" in bc.report(1.0)

def test_tools_ride_along_on_the_answering_pass(monkeypatch):
    """Dropping the schemas for the second pass changes the system block and
    costs a full prompt re-read."""
    sent = []
    seq = [
        FakeResponse(
            json.dumps(
                {
                    "message": {
                        "content": "",
                        "tool_calls": [{"function": {"name": "news", "arguments": {}}}],
                    },
                    "done": True,
                }
            ).encode()
        ),
        stream_lines("[happy] Big news."),
    ]

    def fake(req, timeout):
        sent.append(json.loads(req.data))
        return seq.pop(0)

    monkeypatch.setattr(brain_client, "urlopen", fake)

    class Box:
        parse_args = staticmethod(lambda raw: raw or {})

        def run(self, name, args):
            return "one; two"

    bc = BrainClient(host="test", port=1)
    bc.toolbox = Box()
    list(bc.chat_stream("news"))
    first, second = sent
    assert "tools" in first and "tools" in second
    assert second["messages"][: len(first["messages"])] == first["messages"]

def test_first_word_is_timed_and_reported(monkeypatch):
    """Total time hides the wait that is actually felt: the silence before
    Mochi makes any sound at all."""
    resp = stream_lines("[happy] Right, ", "here we go. And more.")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    list(bc.chat_stream("go"))
    assert bc.first_word > 0.0
    assert "first word at" in bc.report(1.0)

def test_first_word_is_never_when_nothing_is_said(monkeypatch):
    resp = stream_lines("[happy] ```python\nprint(1)\n```")
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: resp)
    bc = BrainClient(host="test", port=1)
    list(bc.chat_stream("code"))
    assert bc.first_word == 0.0
    assert "never" in bc.report(1.0)

def test_warm_up_sends_the_same_prefix_a_real_turn_will(monkeypatch):
    sent = []

    def fake(req, timeout):
        sent.append(json.loads(req.data))
        return FakeResponse(json.dumps({"message": {"content": "hi"}}).encode())

    monkeypatch.setattr(brain_client, "urlopen", fake)
    bc = BrainClient(host="test", port=1)
    bc.warm_up()
    list(bc.chat_stream("real question"))
    warm, real = sent
    assert warm["options"]["num_predict"] == 1, "warmup should not write a reply"
    assert real["messages"][:2] == warm["messages"][:2], "warmup primed a different prefix"
    assert len(bc.history) == 3, "warmup must not pollute the conversation"

def test_warm_up_survives_a_dead_brain(monkeypatch):
    monkeypatch.setattr(brain_client, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError()))
    BrainClient(host="test", port=1).warm_up()

def http_error(code, body):
    from urllib.error import HTTPError

    return HTTPError("http://test/api/chat", code, "Bad Request", {}, io.BytesIO(body))


def test_toolless_model_is_named_not_called_unreachable():
    """HTTPError subclasses URLError, so ollama refusing the request used to
    read exactly like a dead server and told the owner nothing."""
    err = http_error(400, b'{"error":"llama3.2:1b does not support tools"}')
    said = brain_client.explain(err, "http://test/api/chat", "llama3.2:1b")
    assert "cannot call tools" in said
    assert "ollama pull" in said
    assert "unreachable" not in said


def test_missing_model_quotes_ollama():
    err = http_error(404, b'{"error":"model \'qwen2.5:3b\' not found"}')
    said = brain_client.explain(err, "http://test/api/chat", "qwen2.5:3b")
    assert "404" in said and "not found" in said


def test_a_genuinely_dead_server_still_says_unreachable():
    said = brain_client.explain(OSError("connection refused"), "http://test/x", "m")
    assert "unreachable" in said and "connection refused" in said


def test_unparseable_error_body_does_not_crash_the_explanation():
    err = http_error(500, b"<html>gateway blew up</html>")
    assert "500" in brain_client.explain(err, "http://test/x", "m")


def test_stream_reports_the_real_reason(monkeypatch):
    def boom(req, timeout):
        raise http_error(400, b'{"error":"nope does not support tools"}')

    monkeypatch.setattr(brain_client, "urlopen", boom)
    bc = BrainClient(host="test", port=1, model="nope")
    with pytest.raises(BrainOfflineError, match="cannot call tools"):
        list(bc.chat_stream("hello"))
    assert len(bc.history) == 1, "the failed turn should not stay in history"


def tool_response(name, done=True):
    return FakeResponse(
        json.dumps(
            {
                "message": {"content": "", "tool_calls": [{"function": {"name": name}}]},
                "done": done,
            }
        ).encode()
    )


class Recorder:
    parse_args = staticmethod(lambda raw: raw or {})

    def __init__(self, result="done"):
        self.result = result
        self.ran = []

    def run(self, name, args):
        self.ran.append(name)
        return self.result


def test_a_second_round_of_tools_is_not_dropped(monkeypatch):
    """Answering can itself need a tool - look at this, then remember it.
    The second round used to be collected and thrown away, and when it was
    the whole reply, Mochi acted and then said nothing at all."""
    seq = [tool_response("get_time"), tool_response("remember"), stream_lines("[happy] Saved it.")]
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: seq.pop(0))
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Recorder()
    assert list(bc.chat_stream("note the time")) == ["Saved it."]
    assert bc.toolbox.ran == ["get_time", "remember"]


def test_tool_rounds_are_capped(monkeypatch):
    """A model that answers every tool result with another tool call would
    otherwise hold the conversation open forever."""
    monkeypatch.setattr(brain_client, "MAX_TOOL_ROUNDS", 2)
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: tool_response("get_time"))
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Recorder()
    list(bc.chat_stream("spin"))
    assert bc.toolbox.ran == ["get_time", "get_time"]


def test_what_was_seen_survives_into_the_next_turn(monkeypatch):
    """The tool result only ever reached the local message list, so the turn
    after a look had no record of what was looked at."""
    seq = [tool_response("look"), stream_lines("[happy] A blue mug.")]
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: seq.pop(0))
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Recorder("A blue mug with a chip in it.")
    list(bc.chat_stream("what am I holding"))
    assert any(m["role"] == "tool" and "chip in it" in m["content"] for m in bc.history)
    assert any(m.get("tool_calls") for m in bc.history)


def test_trim_never_orphans_a_tool_result(monkeypatch):
    """A tool result with its call trimmed off above it is a 400 from
    ollama, which would take the whole conversation down."""
    monkeypatch.setattr(brain_client, "MAX_HISTORY", 6)
    monkeypatch.setattr(brain_client, "HISTORY_KEEP", 3)
    bc = BrainClient(host="test", port=1)
    bc.history += [
        {"role": "user", "content": "0"},
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "look"}}]},
        {"role": "tool", "name": "look", "content": "a mug"},
        {"role": "user", "content": "2"},
        {"role": "user", "content": "3"},
    ]
    bc.trim()
    assert bc.history[0]["role"] == "system"
    assert bc.history[1]["role"] != "tool"


def test_a_slow_look_says_something_before_the_silence(monkeypatch):
    """Sight can take tens of seconds. Going quiet for that long is
    indistinguishable from being broken."""
    seq = [tool_response("look"), stream_lines("[happy] A blue mug.")]
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: seq.pop(0))
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Recorder("A blue mug.")
    said = list(bc.chat_stream("what is this"))
    assert said[0] == "Let me have a look."
    assert bc.first_word > 0, "the wait line is real audio and should start the clock"


def test_a_quick_tool_stays_quiet(monkeypatch):
    seq = [tool_response("get_time"), stream_lines("[happy] Nine o'clock.")]
    monkeypatch.setattr(brain_client, "urlopen", lambda req, timeout: seq.pop(0))
    bc = BrainClient(host="test", port=1)
    bc.toolbox = Recorder("09:00")
    assert list(bc.chat_stream("time?")) == ["Nine o'clock."]
