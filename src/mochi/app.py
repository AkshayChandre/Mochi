from __future__ import annotations

import threading

import pygame as pg

from mochi.brain.client import BrainClient, BrainOfflineError
from mochi.constants import FPS, SIZE, STATE_EMOTION
from mochi.face.engine import MochiFace
from mochi.voice.pipeline import State, VoicePipeline


class InstantWake:
    def wait(self) -> str:
        return ""


class VisionWake:
    def __init__(self, brain: BrainClient) -> None:
        from mochi.vision.recognition import FaceDB, Recognizer

        self.brain = brain
        self.db = FaceDB()
        self.rec = Recognizer()

    def wait(self) -> str:
        emb = self.rec.embedding()
        self.brain.person = self.db.identify(emb)[0] if emb is not None else None
        return ""


def make_apply(face: MochiFace, brain: BrainClient, sounds=None):
    def apply(state: State) -> None:
        if sounds is not None:
            sounds.on_state(state)
        face.set_speaking(state == State.SPEAKING)
        emotion = brain.last_emotion if state == State.SPEAKING else STATE_EMOTION[state.value]
        face.set_emotion(emotion)

    return apply


def make_intercept(face: MochiFace):
    def intercept(text: str) -> str | None:
        low = text.lower()
        if "expression" in low or "emotion" in low:
            face.play_parade()
            return "Watch my face!"
        return None

    return intercept


def build_pipeline(face: MochiFace, brain: BrainClient) -> VoicePipeline:
    try:
        from mochi.voice.sounds import BOOT_SOUND, RobotSounds
        from mochi.voice.stt import WhisperTranscriber
        from mochi.voice.tts import KidRobotVoice

        sounds = RobotSounds()
        wake, stt, tts = InstantWake(), WhisperTranscriber(), KidRobotVoice()
        try:
            wake = VisionWake(brain)
            print("vision: face recognition active")
        except Exception as verr:
            print(f"vision unavailable: {verr} — running without recognition")
        sounds.play(BOOT_SOUND)
    except Exception as err:
        print(f"audio unavailable: {err}")
        print("enable it with: pip install -e .[audio]  (see README) — using console mode")
        from mochi.voice.console import ConsoleIn, ConsoleOut, EnterWake

        sounds, wake, stt, tts = None, EnterWake(), ConsoleIn(), ConsoleOut()
    return VoicePipeline(
        wake,
        stt,
        brain,
        tts,
        make_apply(face, brain, sounds),
        make_intercept(face),
        face.show_card,
    )


def start_voice(face: MochiFace) -> None:
    brain = BrainClient()

    def loop() -> None:
        try:
            build_pipeline(face, brain).run()
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
