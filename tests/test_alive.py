from mochi.alive import Ambient
from mochi.constants import AWAY_SECONDS, QUIET_SECONDS, STARE_SECONDS


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def build():
    said = []
    clock = Clock()
    amb = Ambient(lambda line, emotion: said.append((line, emotion)), now=clock)
    return amb, said, clock


def test_staring_triggers_shy_remark():
    amb, said, clock = build()
    amb.tick(True)
    clock.advance(STARE_SECONDS + 1)
    amb.tick(True)
    assert said, "expected a remark after a long stare"
    assert said[0][1] in ("shy", "smug")


def test_staring_does_not_repeat_immediately():
    amb, said, clock = build()
    amb.tick(True)
    clock.advance(STARE_SECONDS + 1)
    amb.tick(True)
    clock.advance(STARE_SECONDS + 1)
    amb.tick(True)
    assert len(said) == 1


def test_talking_resets_the_stare():
    amb, said, clock = build()
    amb.tick(True)
    clock.advance(STARE_SECONDS - 2)
    amb.noticed_speech()
    clock.advance(3)
    amb.tick(True)
    assert said == []


def test_welcome_back_after_long_absence():
    amb, said, clock = build()
    amb.tick(True)
    clock.advance(AWAY_SECONDS + 10)
    amb.tick(False)
    amb.tick(True)
    assert said and "back" in said[0][0].lower() or "there you are" in said[0][0].lower()


def test_quiet_check_in():
    amb, said, clock = build()
    amb.tick(True)
    clock.advance(QUIET_SECONDS + 1)
    amb.noticed_speech()
    amb.last_spoke -= QUIET_SECONDS + 1
    amb.fired["stare"] = clock()
    amb.tick(True)
    assert said


def test_nothing_happens_when_nobody_is_there():
    amb, said, clock = build()
    for _ in range(5):
        clock.advance(STARE_SECONDS)
        amb.tick(False)
    assert said == []
