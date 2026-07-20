from __future__ import annotations

import math
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
                f"voice model missing: {model} — run: "
                f"python -m piper.download_voices {VOICE_NAME} --data-dir {VOICES_DIR}"
            )
        self.voice = PiperVoice.load(str(model))

    def say(self, text: str) -> None:
        chunks = [
            np.frombuffer(c.audio_int16_bytes, dtype=np.int16) for c in self.voice.synthesize(text)
        ]
        if not chunks:
            return
        audio = np.concatenate(chunks).astype(np.float32) / 32768.0
        rate = int(self.voice.config.sample_rate * PITCH_FACTOR)
        t = np.arange(len(audio)) / rate
        audio *= 1.0 - TREMOLO_DEPTH * (0.5 + 0.5 * np.sin(math.tau * TREMOLO_HZ * t))
        self.sd.play(audio, rate)
        self.sd.wait()
