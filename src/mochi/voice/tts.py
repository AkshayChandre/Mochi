from __future__ import annotations

import math
import threading
import time
from pathlib import Path

import numpy as np

from mochi.constants import PITCH_FACTOR, TREMOLO_DEPTH, TREMOLO_HZ, VOICE_NAME, VOICES_DIR


class KidRobotVoice:
    def __init__(self) -> None:
        import sounddevice as sd
        from piper import PiperVoice

        self.sd = sd
        model = Path(VOICES_DIR) / f"{VOICE_NAME}.onnx"
        if not model.is_file():
            raise FileNotFoundError(
                f"voice model missing: {model} - run: "
                f"python -m piper.download_voices {VOICE_NAME} --data-dir {VOICES_DIR}"
            )
        self.voice = PiperVoice.load(str(model))
        self.lock = threading.Lock()
        self.until = 0.0

    def say(self, text: str) -> None:
        with self.lock:
            self.render(text)

    def render(self, text: str) -> None:
        chunks = [
            np.frombuffer(c.audio_int16_bytes, dtype=np.int16) for c in self.voice.synthesize(text)
        ]
        if not chunks:
            return
        audio = np.concatenate(chunks).astype(np.float32) / 32768.0
        rate = int(self.voice.config.sample_rate * PITCH_FACTOR)
        t = np.arange(len(audio)) / rate
        audio *= 1.0 - TREMOLO_DEPTH * (0.5 + 0.5 * np.sin(math.tau * TREMOLO_HZ * t))
        self.sd.wait()
        self.sd.play(audio, rate)
        # play() returns immediately, so remember when the sound actually
        # stops; the face reads this to move its mouth only while there is
        # audio, instead of flapping through the gaps between sentences
        self.until = time.monotonic() + len(audio) / rate

    def busy(self) -> bool:
        return time.monotonic() < self.until

    def flush(self) -> None:
        self.sd.wait()
