from __future__ import annotations

import sys

from mochi.brain.client import BrainClient, BrainOfflineError
from mochi.config import CONNECTIONS
from mochi.constants import BENCH_PROMPTS, BENCH_RESULTS
from mochi.tools import Toolbox


class Spy:
    """Stands in for the real toolbox: records what the model reached for and
    hands back a plausible answer. The benchmark then measures the brain, not
    the webcam, the network or the speakers."""

    parse_args = staticmethod(Toolbox.parse_args)

    def __init__(self) -> None:
        self.used: list[str] = []

    def run(self, name: str, args: dict) -> str:
        self.used.append(name)
        return BENCH_RESULTS.get(name, "done")


def measure(model: str) -> dict:
    brain = BrainClient(model=model)
    brain.verbose = False
    brain.toolbox = spy = Spy()
    brain.warm_up()  # pay the cold prompt once, outside the numbers

    waits, wrote, writing, correct = [], 0, 0.0, 0
    for asked, wanted in BENCH_PROMPTS:
        spy.used.clear()
        said = " ".join(brain.chat_stream(asked))
        waits.append(brain.first_word)
        wrote += brain.stats.get("eval_count", 0)
        writing += brain.stats.get("write", 0.0)
        correct += (wanted in spy.used) if wanted else (not spy.used and bool(said))
        print(f"  {asked[:44]:46} {brain.first_word:4.1f}s  {','.join(spy.used) or '-'}")
    return {
        "model": model,
        "first": sum(waits) / len(waits),
        "rate": wrote / writing if writing else 0.0,
        "words": wrote / len(BENCH_PROMPTS),
        "tools": f"{correct}/{len(BENCH_PROMPTS)}",
    }


def main() -> None:
    models = sys.argv[1:] or [CONNECTIONS.llm_model]
    print(f"benchmarking {len(models)} model(s) against {len(BENCH_PROMPTS)} prompts\n")
    rows = []
    for model in models:
        print(f"{model}:")
        try:
            rows.append(measure(model))
        except BrainOfflineError as err:
            print(f"  skipped: {err} (is it pulled? ollama pull {model})")
        except Exception as err:  # a missing model comes back as a plain HTTP error
            print(f"  skipped: {err!r}")
        print()

    if not rows:
        return
    print(f"{'model':22}{'first word':>12}{'tok/s':>9}{'tokens/reply':>15}{'tools':>8}")
    for r in sorted(rows, key=lambda r: -r["rate"]):
        print(
            f"{r['model']:22}{r['first']:>11.1f}s{r['rate']:>9.1f}"
            f"{r['words']:>15.0f}{r['tools']:>8}"
        )
    best = max(rows, key=lambda r: r["rate"])
    print(f"\nfastest: {best['model']} - set it in config.yaml under brain.model")
    print("check tools scored full marks before switching; speed is no good if it stops acting")


if __name__ == "__main__":
    main()
