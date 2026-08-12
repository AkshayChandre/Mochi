from __future__ import annotations

import threading
import time

import pygame as pg

from mochi.brain.client import BrainClient, BrainOfflineError
from mochi.constants import (
    FPS,
    GREETING,
    IDENTITY_CACHE_SECONDS,
    MEMORY_SAVED,
    RETRY_SECONDS,
    SIZE,
    STATE_EMOTION,
    STRANGER_GREETING,
)
from mochi.desktop import context_note
from mochi.face.engine import MochiFace
from mochi.skills import Skills
from mochi.voice.pipeline import State, VoicePipeline


class InstantWake:
    def wait(self) -> str:
        return ""

class VisionWake:
    def __init__(self, presence, brain: BrainClient) -> None:
        self.presence = presence
        self.brain = brain
        self.greeted: str | None = None

    def wait(self) -> str:
        name, seen = self.presence.whos_there()
        self.brain.person = name
        if not seen:
            self.greeted = None
            return ""
        if name:
            if name != self.greeted:
                self.greeted = name
                return GREETING.format(name=name)
            return ""
        if self.greeted != "?":
            self.greeted = "?"
            return STRANGER_GREETING
        return ""

class VisionStt:
    def __init__(self, stt, presence, brain: BrainClient) -> None:
        self.stt = stt
        self.presence = presence
        self.brain = brain

    def listen(self) -> str:
        text = self.stt.listen()
        if text.strip():
            name, seen = self.presence.whos_there(tries=1, max_age=IDENTITY_CACHE_SECONDS)
            if seen:
                self.brain.person = name
        return text

def make_apply(face: MochiFace, brain: BrainClient, sounds=None):
    def apply(state: State) -> None:
        if sounds is not None:
            sounds.on_state(state)
        face.set_speaking(state == State.SPEAKING and brain.last_emotion != "sleeping")
        if state == State.SPEAKING or (state == State.IDLE and brain.last_emotion == "sleeping"):
            emotion = brain.last_emotion
        else:
            emotion = STATE_EMOTION[state.value]
        face.set_emotion(emotion)

    return apply

def make_intercept(face: MochiFace, memory, skills):
    def intercept(text: str) -> str | None:
        low = text.lower()
        if "expression" in low or "emotion" in low:
            face.play_parade()
            return "Watch my face!"
        if fact := memory.explicit(text):
            memory.save(fact)
            return MEMORY_SAVED
        return skills.handle(text)

    return intercept

def build_pipeline(face: MochiFace, brain: BrainClient) -> VoicePipeline:
    from mochi.brain.memory import Memory, MemoryStore

    store = MemoryStore()
    brain.store = store
    memory = Memory(brain, store)
    try:
        from mochi.voice.sounds import BOOT_SOUND, RobotSounds
        from mochi.voice.stt import WhisperTranscriber
        from mochi.voice.tts import KidRobotVoice

        sounds = RobotSounds()
        wake, stt, tts = InstantWake(), WhisperTranscriber(), KidRobotVoice()
        try:
            from mochi.vision.recognition import Presence

            presence = Presence()
            wake = VisionWake(presence, brain)
            stt = VisionStt(stt, presence, brain)
            print("vision: face recognition active")
        except Exception as verr:
            print(f"vision unavailable: {verr} - running without recognition")
        sounds.play(BOOT_SOUND)
    except Exception as err:
        print(f"audio unavailable: {err}")
        print("enable it with: pip install -e .[audio]  (see README) - using console mode")
        from mochi.voice.console import ConsoleIn, ConsoleOut, EnterWake

        sounds, wake, stt, tts = None, EnterWake(), ConsoleIn(), ConsoleOut()
    def announce(text: str) -> None:
        face.set_emotion("excited")
        face.set_speaking(True)
        tts.say(text)
        tts.flush()
        face.set_speaking(False)
        face.set_emotion("neutral")

    def set_mood(emotion: str) -> None:
        brain.last_emotion = emotion

    skills = Skills(announce, set_mood)
    print(f"desktop: {context_note()}")
    return VoicePipeline(
        wake,
        stt,
        brain,
        tts,
        make_apply(face, brain, sounds),
        make_intercept(face, memory, skills),
        face.show_card,
        memory,
    )

def start_voice(face: MochiFace) -> None:
    brain = BrainClient()

    def loop() -> None:
        pipeline = build_pipeline(face, brain)
        while True:
            try:
                pipeline.run()
            except BrainOfflineError as err:
                print(f"brain offline, retrying: {err}")
                face.set_emotion("error")
                time.sleep(RETRY_SECONDS)
            except Exception as err:
                print(f"recovered from: {err!r}")
                time.sleep(RETRY_SECONDS)

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
        pg.display.set_caption(f"Mochi - {face.emotion}")
        pg.display.flip()

if __name__ == "__main__":
    main()
