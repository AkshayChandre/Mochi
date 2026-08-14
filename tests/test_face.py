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

def _render(screen, frames, setup=None):
    """Blinks and gaze wander are random, so seed to make two runs comparable."""
    random.seed(7)
    face = MochiFace()
    if setup:
        setup(face)
    for _ in range(frames):
        face.update(1 / 60)
    face.draw(screen)
    return pg.image.tostring(screen, "RGB")

def test_render_is_deterministic_when_seeded(screen):
    assert _render(screen, 12) == _render(screen, 12)

def test_gesture_moves_the_eyes_then_settles(screen):
    mid = _render(screen, 12, lambda f: f.play_gesture("nod"))
    assert mid != _render(screen, 12), "nod never moved anything"
    after = _render(screen, 70, lambda f: f.play_gesture("nod"))
    assert after == _render(screen, 70), "nod outlasted its window"

def test_unknown_gesture_is_rejected():
    with pytest.raises(ValueError):
        MochiFace().play_gesture("backflip")

def test_banner_shows_then_expires(screen):
    from mochi.constants import BANNER_SECONDS

    show = lambda f: f.show_banner("28°")  # noqa: E731
    assert _render(screen, 12, show) != _render(screen, 12)
    gone = int((BANNER_SECONDS + 0.5) * 60)
    assert _render(screen, gone, show) == _render(screen, gone)

def test_banner_keeps_the_eyes_on_screen(screen):
    """A banner is not a takeover: the face stays a face underneath it."""
    face = MochiFace()
    face.show_banner("28°")
    face.update(1 / 60)
    face.draw(screen)
    top_half = pg.Surface((SIZE, SIZE // 2))
    top_half.blit(screen, (0, 0))
    assert pg.transform.average_color(top_half)[:3] != (0, 0, 0)

def test_long_banner_is_shrunk_to_fit(screen):
    face = MochiFace()
    short = face.fit_font("28°", SIZE * 0.82, 74)
    long = face.fit_font("Dentist appointment tomorrow afternoon", SIZE * 0.82, 74)
    assert long.size("Dentist appointment tomorrow afternoon")[0] <= SIZE * 0.82
    assert long.get_height() < short.get_height()

def test_mouth_only_moves_while_audio_is_actually_playing():
    """The bug: the mouth was driven by pipeline state, so it mimed through
    the several seconds between one spoken sentence and the next."""
    audible = [False]
    face = MochiFace()
    face.voice = lambda: audible[0]
    face.set_speaking(True)
    face.update(1 / 60)
    assert not face.speaking, "mouth moved before any sound"
    audible[0] = True
    face.update(1 / 60)
    assert face.speaking
    audible[0] = False
    face.update(1 / 60)
    assert not face.speaking, "mouth kept going through the gap"

def test_mouth_ignores_audio_when_not_allowed_to_speak():
    face = MochiFace()
    face.voice = lambda: True
    face.set_speaking(False)
    face.update(1 / 60)
    assert not face.speaking

def test_mouth_still_works_with_no_voice_attached():
    face = MochiFace()
    face.set_speaking(True)
    face.update(1 / 60)
    assert face.speaking

def test_talking_mouth_is_irregular_not_a_metronome():
    from mochi.face.engine import talk_openness

    vals = [talk_openness(i / 60) for i in range(600)]
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert min(vals) < 0.1 and max(vals) > 0.8, "mouth never fully opens or closes"
    peaks = [
        i
        for i in range(1, len(vals) - 1)
        if vals[i] > vals[i - 1] and vals[i] >= vals[i + 1]
    ]
    gaps = {peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)}
    assert len(gaps) > 1, "mouth opens on a perfectly fixed beat"
