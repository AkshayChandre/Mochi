"""Procedural robot sounds — synthesized beeps and chirps, no audio assets."""

from __future__ import annotations

import math
import threading
import time

import numpy as np

from mochi.constants import SOUND_SAMPLE_RATE, THINK_BLIP_INTERVAL
from mochi.voice.pipeline import State


def fade(wave: np.ndarray, seconds: float = 0.008) -> np.ndarray:
    n = min(len(wave) // 2, int(SOUND_SAMPLE_RATE * seconds))
    env = np.ones(len(wave), dtype=np.float32)
    env[:n] = np.linspace(0.0, 1.0, n)
    env[-n:] = np.linspace(1.0, 0.0, n)
    return (wave * env).astype(np.float32)


def tone(freq: float, seconds: float, volume: float = 0.4) -> np.ndarray:
    t = np.linspace(0.0, seconds, int(SOUND_SAMPLE_RATE * seconds), False)
    return fade(volume * np.sin(math.tau * freq * t))


def chirp(f0: float, f1: float, seconds: float, volume: float = 0.4) -> np.ndarray:
    t = np.linspace(0.0, seconds, int(SOUND_SAMPLE_RATE * seconds), False)
    phase = math.tau * (f0 * t + (f1 - f0) * t**2 / (2.0 * seconds))
    return fade(volume * np.sin(phase))


BOOT_SOUND = np.concatenate([chirp(500, 1100, 0.09), tone(1300, 0.07)])
ACK_BLIP = tone(1250, 0.05, 0.25)
THINK_BLIP = chirp(720, 900, 0.05, 0.15)


class RobotSounds:
    def __init__(self) -> None:
        import sounddevice as sd

        self.sd = sd
        self.prev = State.IDLE
        self.thinking = False

    def play(self, wave: np.ndarray) -> None:
        self.sd.play(wave, SOUND_SAMPLE_RATE)

    def think_loop(self) -> None:
        while self.thinking:
            self.play(THINK_BLIP)
            time.sleep(THINK_BLIP_INTERVAL)

    def on_state(self, state: State) -> None:
        if state == State.THINKING and not self.thinking:
            self.thinking = True
            threading.Thread(target=self.think_loop, daemon=True).start()
        elif state != State.THINKING:
            self.thinking = False
        if state == State.LISTENING and self.prev == State.SPEAKING:
            self.play(ACK_BLIP)
        self.prev = state
