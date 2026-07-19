"""Integrated app: face window with the voice pipeline running beside it."""

from __future__ import annotations

import threading

import pygame as pg

from mochi.brain.client import BrainClient, BrainOfflineError
from mochi.constants import FPS, SIZE, STATE_EMOTION
from mochi.face.engine import MochiFace
from mochi.voice.console import ConsoleIn, ConsoleOut, EnterWake
from mochi.voice.pipeline import State, VoicePipeline


def start_voice(face: MochiFace) -> None:
    def apply(state: State) -> None:
        face.set_emotion(STATE_EMOTION[state.value])

    pipeline = VoicePipeline(EnterWake(), ConsoleIn(), BrainClient(), ConsoleOut(), apply)

    def loop() -> None:
        try:
            pipeline.run()
        except BrainOfflineError as err:
            print(f"error: {err}")
            face.set_emotion("sad")

    threading.Thread(target=loop, daemon=True).start()


def main() -> None:
    pg.init()
    screen = pg.display.set_mode((SIZE, SIZE))
    clock = pg.time.Clock()
    face = MochiFace()
    start_voice(face)

    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for e in pg.event.get():
            if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                pg.quit()
                return
        face.update(dt)
        face.draw(screen)
        pg.display.set_caption(f"Mochi — {face.emotion}")
        pg.display.flip()


if __name__ == "__main__":
    main()
