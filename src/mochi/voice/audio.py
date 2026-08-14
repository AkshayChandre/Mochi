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
    RECALIBRATE_EVERY,
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
    """Holds one mic stream open for the robot's whole life. Opening a stream
    and re-measuring room noise cost about half a second, and that was paid
    before every single utterance."""

    def __init__(self) -> None:
        import sounddevice as sd

        self.sd = sd
        self.frame_len = int(SAMPLE_RATE * FRAME_SECONDS)
        self.stream = None
        self.gate = SILENCE_RMS
        self.since_calibration = 0

    def frame(self) -> np.ndarray:
        return self.stream.read(self.frame_len)[0][:, 0]

    def calibrate(self) -> None:
        ambient = [rms(self.frame()) for _ in range(CALIBRATION_FRAMES)]
        self.gate = noise_gate(float(np.median(ambient)))
        self.since_calibration = 0

    def open(self) -> None:
        if self.stream is None:
            self.stream = self.sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32"
            )
            self.stream.start()
            self.calibrate()
        elif self.since_calibration >= RECALIBRATE_EVERY:
            self.calibrate()  # rooms get louder as the day goes on

    def drain(self) -> None:
        """Mochi's own voice is still sitting in the mic buffer after it
        speaks; without this it transcribes itself and answers itself."""
        while self.stream.read_available >= self.frame_len:
            self.frame()

    def record_utterance(self) -> np.ndarray | None:
        self.open()
        self.drain()
        self.since_calibration += 1
        frames: list[np.ndarray] = []
        started = False
        quiet = 0.0
        waited = 0.0
        while True:
            frame = self.frame()
            if rms(frame) >= self.gate:
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
