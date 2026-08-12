import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame as pg
import pytest

from mochi.face.engine import EMOTIONS, SIZE, MochiFace


@pytest.fixture(scope="module")
def screen():
    pg.init()
    yield pg.display.set_mode((SIZE, SIZE))
    pg.quit()

def _settle(face: MochiFace, frames: int = 180) -> None:
    for _ in range(frames):
        face.update(1 / 60, None)

@pytest.mark.parametrize("name", list(EMOTIONS))
def test_emotion_converges_and_renders(screen, name):
    """Every emotion's eased state reaches its spec and draws without error."""
    face = MochiFace()
    face.set_emotion(name)
    _settle(face)
    spec = EMOTIONS[name]
    assert face.state["h"] == pytest.approx(spec.h, rel=0.05)
    assert face.state["crescent"] == pytest.approx(spec.crescent, abs=0.03)
    face.blink = 1.0
    face.draw(screen)

def test_unknown_emotion_rejected():
    with pytest.raises(ValueError):
        MochiFace().set_emotion("nonsense")

def test_blink_cycle_completes():
    random.seed(0)  # deterministic double-blink rolls
    face = MochiFace()
    face.next_blink = 0.0
    face.update(1 / 60, None)
    assert face.blink_phase == "closing"
    _settle(face, 120)
    assert face.blink == 1.0
    assert face.blink_phase == "idle"

def test_sleeping_suppresses_blink():
    face = MochiFace()
    face.set_emotion("sleeping")
    face.next_blink = 0.0
    _settle(face, 30)
    assert face.blink_phase == "idle"

def test_parade_cycles_all_emotions_then_neutral(screen):
    face = MochiFace()
    face.play_parade()
    for _ in range(60 * (len(EMOTIONS) + 2)):
        face.update(1 / 60)
    assert face.parade == []
    assert face.emotion == "neutral"

def test_idle_sleeps_then_wakes(screen):
    from mochi.constants import IDLE_SLEEP_SECONDS

    face = MochiFace()
    face.t = IDLE_SLEEP_SECONDS + 1
    face.update(1 / 60)
    assert face.emotion == "sleeping"
    face.set_emotion("happy")
    face.update(1 / 60)
    assert face.emotion == "happy"

def test_no_idle_sleep_while_showing_a_card(screen):
    from mochi.constants import IDLE_SLEEP_SECONDS

    face = MochiFace()
    face.show_card("print(1)")
    face.t = IDLE_SLEEP_SECONDS + 1
    face.card_until = face.t + 10
    face.update(1 / 60)
    assert face.emotion == "neutral"

def test_card_shows_and_renders(screen):
    face = MochiFace()
    face.show_card("line1\nline2")
    face.update(1 / 60)
    face.draw(screen)
    assert face.card_lines == ["line1", "line2"]

def test_long_card_scrolls(screen):
    face = MochiFace()
    face.show_card("\n".join(f"line {i}" for i in range(60)))
    for _ in range(300):
        face.update(1 / 60)
    face.draw(screen)
    assert face.card_scroll > 0

def test_emotion_colors_cover_all_emotions():
    from mochi.constants import EMOTION_COLORS

    assert set(EMOTION_COLORS) == set(EMOTIONS)

def test_speaking_mode_renders(screen):
    face = MochiFace()
    face.set_speaking(True)
    _settle(face, 30)
    face.draw(screen)
    face.set_speaking(False)
    assert not face.speaking

def test_mouse_gaze_tracks_target(screen):
    face = MochiFace()
    target = pg.Vector2(0.8, -0.4)
    for _ in range(120):
        face.update(1 / 60, target)
    assert face.gaze.distance_to(target) < 0.05
