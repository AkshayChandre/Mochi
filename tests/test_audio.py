import math

import pytest

np = pytest.importorskip("numpy")
audio = pytest.importorskip("mochi.voice.audio")
sounds = pytest.importorskip("mochi.voice.sounds")

from mochi.constants import SILENCE_RMS, SOUND_SAMPLE_RATE  # noqa: E402

def test_rms_discriminates_silence_from_speech():
    silence = np.zeros(480, dtype=np.float32)
    t = np.linspace(0, 0.03, 480)
    speech = (0.1 * np.sin(math.tau * 200 * t)).astype(np.float32)
    assert audio.rms(silence) < SILENCE_RMS <= audio.rms(speech)

def test_tone_shape_and_fades():
    wave = sounds.tone(880, 0.1)
    assert len(wave) == int(SOUND_SAMPLE_RATE * 0.1)
    assert wave.dtype == np.float32
    assert np.max(np.abs(wave)) <= 1.0
    assert abs(wave[0]) < 0.01 and abs(wave[-1]) < 0.01

def test_chirp_has_energy():
    wave = sounds.chirp(500, 1000, 0.1)
    assert float(np.sqrt(np.mean(wave**2))) > 0.05

def test_boot_sound_exists():
    assert len(sounds.BOOT_SOUND) > 0
