import pytest

np = pytest.importorskip("numpy")
audio = pytest.importorskip("mochi.voice.audio")

from mochi.constants import CALIBRATION_FRAMES, RECALIBRATE_EVERY  # noqa: E402


class FakeStream:
    """Counts what the recorder actually pulls from the mic."""

    def __init__(self, level=0.0):
        self.level = level
        self.reads = 0
        self.read_available = 0
        self.started = False

    def start(self):
        self.started = True

    def read(self, n):
        self.reads += 1
        if self.read_available:
            self.read_available = max(0, self.read_available - n)
        return (np.full((n, 1), self.level, dtype=np.float32), False)


def recorder(stream):
    rec = audio.Recorder.__new__(audio.Recorder)
    rec.sd = None
    rec.frame_len = 480
    rec.stream = stream
    rec.gate = 0.01
    rec.since_calibration = 0
    return rec


def test_stream_is_opened_once_not_per_utterance():
    made = []

    class FakeSd:
        def InputStream(self, **kw):
            made.append(kw)
            return FakeStream()

    rec = audio.Recorder.__new__(audio.Recorder)
    rec.sd, rec.frame_len, rec.stream = FakeSd(), 480, None
    rec.gate, rec.since_calibration = 0.01, 0
    rec.open()
    first = rec.stream
    rec.open()
    assert len(made) == 1 and rec.stream is first and first.started


def test_opening_calibrates_and_reads_ambient_frames():
    rec = audio.Recorder.__new__(audio.Recorder)
    rec.sd, rec.frame_len, rec.stream = None, 480, FakeStream(level=0.02)
    rec.gate, rec.since_calibration = 0.0, 0
    rec.calibrate()
    assert rec.stream.reads == CALIBRATION_FRAMES
    assert rec.gate > 0.0 and rec.since_calibration == 0


def test_recalibrates_after_enough_turns_so_the_gate_tracks_the_room():
    rec = recorder(FakeStream(level=0.02))
    rec.since_calibration = RECALIBRATE_EVERY
    rec.open()
    assert rec.since_calibration == 0
    assert rec.stream.reads == CALIBRATION_FRAMES


def test_drain_throws_away_mochis_own_voice():
    stream = FakeStream()
    stream.read_available = 480 * 5
    rec = recorder(stream)
    rec.drain()
    assert stream.reads == 5
    assert stream.read_available == 0

def test_voice_is_busy_only_until_the_audio_ends():
    import time

    tts = pytest.importorskip("mochi.voice.tts")
    v = tts.KidRobotVoice.__new__(tts.KidRobotVoice)
    v.until = time.monotonic() + 5
    assert v.busy()
    v.until = time.monotonic() - 0.01
    assert not v.busy()
