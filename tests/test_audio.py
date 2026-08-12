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

def test_noise_gate_adapts_and_clamps():
    from mochi.constants import NOISE_GATE_CEILING, SILENCE_RMS

    assert audio.noise_gate(0.0) == SILENCE_RMS
    assert audio.noise_gate(0.02) > SILENCE_RMS
    assert audio.noise_gate(9.9) == SILENCE_RMS * NOISE_GATE_CEILING

def test_normalize_lifts_quiet_speech():
    from mochi.constants import TARGET_PEAK

    quiet = (np.sin(np.linspace(0, 10, 400)) * 0.02).astype(np.float32)
    assert np.max(np.abs(audio.normalize(quiet))) == pytest.approx(TARGET_PEAK, rel=0.01)
    silence = np.zeros(100, dtype=np.float32)
    assert np.array_equal(audio.normalize(silence), silence)

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

def test_whisper_noise_filter():
    from mochi.voice.stt import is_noise

    assert is_noise("Thank you.")
    assert is_noise("  ...  ")
    assert is_noise("you")
    assert not is_noise("what is the time")

def test_yes_words_are_never_filtered_as_noise():
    from mochi.constants import YES_WORDS
    from mochi.voice.stt import is_noise

    assert not any(is_noise(w) for w in YES_WORDS)

def test_blips_muted_while_speaking():
    from mochi.voice.pipeline import State

    s = sounds.RobotSounds.__new__(sounds.RobotSounds)
    played = []
    s.sd = type("SD", (), {"play": lambda self, w, r: played.append(w)})()
    s.prev, s.thinking, s.speaking = State.IDLE, False, False
    s.on_state(State.SPEAKING)
    s.play(sounds.THINK_BLIP)
    assert played == []
    s.on_state(State.LISTENING)
    assert len(played) == 1
