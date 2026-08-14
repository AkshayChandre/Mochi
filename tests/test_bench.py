import json

from mochi.bench import Spy, measure
from mochi.brain import client as brain_client
from mochi.constants import BENCH_PROMPTS


def reply(text, tool=None, wrote=20, secs=1.0):
    done = {"done": True, "eval_count": wrote, "eval_duration": int(secs * 1e9)}
    if tool:
        msg = {"content": "", "tool_calls": [{"function": {"name": tool, "arguments": {}}}]}
    else:
        msg = {"content": text}
    return json.dumps({"message": msg, **done}).encode()


class Resp:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        return iter([self.body])

    def read(self):
        return self.body


def test_spy_records_without_touching_the_real_world():
    spy = Spy()
    assert "Turing" in spy.run("look_up", {"topic": "Alan Turing"})
    assert spy.used == ["look_up"]


def test_measure_scores_a_model_that_calls_every_tool(monkeypatch):
    """A perfect model: no tool for chat, the right tool for everything else."""
    plan = [reply("[happy] hi")]  # measure() warms the cache before timing
    for _, tool in BENCH_PROMPTS:
        if tool:
            plan.append(reply("", tool=tool))
        plan.append(reply("[happy] There you go."))

    monkeypatch.setattr(brain_client, "urlopen", lambda *a, **k: Resp(plan.pop(0)))
    result = measure("fake-model")
    assert result["tools"] == f"{len(BENCH_PROMPTS)}/{len(BENCH_PROMPTS)}"
    assert result["rate"] > 0


def test_measure_marks_down_a_model_that_never_calls_tools(monkeypatch):
    monkeypatch.setattr(
        brain_client, "urlopen", lambda *a, **k: Resp(reply("[happy] I think so, probably."))
    )
    result = measure("lazy-model")
    hits, total = result["tools"].split("/")
    assert int(hits) == 1, "only the chat prompt should score"
    assert int(total) == len(BENCH_PROMPTS)
