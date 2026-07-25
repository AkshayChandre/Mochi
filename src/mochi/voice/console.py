from __future__ import annotations

import sys
import time

from mochi.brain.client import BrainClient, BrainOfflineError
from mochi.constants import SPEECH_SECONDS_PER_CHAR
from mochi.voice.pipeline import State, VoicePipeline


class EnterWake:
    def wait(self) -> str:
        input("\n[press Enter to wake Mochi]")
        return ""


class ConsoleIn:
    def listen(self) -> str:
        return input("you> ")


class ConsoleOut:
    def say(self, text: str) -> None:
        print(f"mochi> {text}")
        time.sleep(len(text) * SPEECH_SECONDS_PER_CHAR)

    def flush(self) -> None:
        pass


def show_state(state: State) -> None:
    print(f"  [{state.value}]")


def show_block(block: str) -> None:
    print(f"--- mochi's screen ---\n{block}\n----------------------")


def main() -> None:
    pipeline = VoicePipeline(
        EnterWake(), ConsoleIn(), BrainClient(), ConsoleOut(), show_state, None, show_block
    )
    print("Mochi console — Ctrl+C to quit. Requires a running Ollama server (see config.yaml).")
    print("After Mochi replies it keeps listening; press Enter alone to end the conversation.")
    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\nbye")
    except BrainOfflineError as err:
        sys.exit(f"error: {err}\nStart it with: ollama serve  (then: ollama pull <model>)")


if __name__ == "__main__":
    main()
