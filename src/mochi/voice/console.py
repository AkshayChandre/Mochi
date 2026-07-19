"""Console demo: chat with Mochi's brain from the terminal, no audio hardware needed."""

from __future__ import annotations

import sys
import time

from mochi.brain.client import BrainClient, BrainOfflineError
from mochi.constants import SPEECH_SECONDS_PER_CHAR
from mochi.voice.pipeline import State, VoicePipeline


class EnterWake:
    def wait(self) -> None:
        input("\n[press Enter to wake Mochi]")


class ConsoleIn:
    def listen(self) -> str:
        return input("you> ")


class ConsoleOut:
    def say(self, text: str) -> None:
        print(f"mochi> {text}")
        time.sleep(len(text) * SPEECH_SECONDS_PER_CHAR)


def show_state(state: State) -> None:
    print(f"  [{state.value}]")


def main() -> None:
    pipeline = VoicePipeline(EnterWake(), ConsoleIn(), BrainClient(), ConsoleOut(), show_state)
    print("Mochi console — Ctrl+C to quit. Requires a running Ollama server (see config.yaml).")
    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\nbye")
    except BrainOfflineError as err:
        sys.exit(f"error: {err}\nStart it with: ollama serve  (then: ollama pull <model>)")


if __name__ == "__main__":
    main()
