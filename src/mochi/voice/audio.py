from __future__ import annotations

import numpy as np

from mochi.constants import (
    CALIBRATION_FRAMES,
    CONVERSATION_WAIT_SECONDS,
    FRAME_SECONDS,
    MAX_UTTERANCE_SECONDS,
    MIN_SPEECH_SECONDS,
    NOISE_GATE_CEILING,
    NOISE_MULT,
    SAMPLE_RATE,
    SILENCE_END_SECONDS,
    SILENCE_RMS,
    TARGET_PEAK,
)

def rms(frame: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(frame))))

def noise_gate(ambient: float) -> float:
    return max(SILENCE_RMS, min(ambient * NOISE_MULT, SILENCE_RMS * NOISE_GATE_CEILING))

def normalize(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-4:
        return audio
    return (audio / peak * TARGET_PEAK).astype(np.float32)

class Recorder:
    def __init__(self) -> None:
        import sounddevice as sd

        self.sd = sd

    def record_utterance(self) -> np.ndarray | None:
        frame_len = int(SAMPLE_RATE * FRAME_SECONDS)
        frames: list[np.ndarray] = []
        started = False
        quiet = 0.0
        waited = 0.0
        with self.sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
            ambient = [rms(stream.read(frame_len)[0][:, 0]) for _ in range(CALIBRATION_FRAMES)]
            gate = noise_gate(float(np.median(ambient)))
            while True:
                frame = stream.read(frame_len)[0][:, 0]
                if rms(frame) >= gate:
                    started = True
                    quiet = 0.0
                    frames.append(frame)
                elif started:
                    quiet += FRAME_SECONDS
                    frames.append(frame)
                    if quiet >= SILENCE_END_SECONDS:
                        break
                else:
                    waited += FRAME_SECONDS
                    if waited >= CONVERSATION_WAIT_SECONDS:
                        return None
                if len(frames) * FRAME_SECONDS >= MAX_UTTERANCE_SECONDS:
                    break
        if len(frames) * FRAME_SECONDS - quiet < MIN_SPEECH_SECONDS:
            return None
        return normalize(np.concatenate(frames))
