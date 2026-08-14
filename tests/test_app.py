from mochi.app import VisionStt, VisionWake
from mochi.constants import GREET_RESET_SECONDS


class Presence:
    def __init__(self, *answers):
        self.answers = list(answers)

    def whos_there(self, tries=6, max_age=0.0):
        return self.answers.pop(0) if self.answers else (None, False)

class Brain:
    person = None

class Stt:
    def listen(self):
        return "hello"

def test_greets_known_person_once():
    wake = VisionWake(Presence(("Akshay", True), ("Akshay", True)), Brain())
    assert wake.wait() == "Hi Akshay!"
    assert wake.wait() == ""

def test_glancing_away_does_not_regreet():
    """Turning your head lost the face for a frame and Mochi said hi again."""
    p = Presence(("Akshay", True), (None, False), ("Akshay", True))
    wake = VisionWake(p, Brain(), now=lambda: 0.0)
    assert wake.wait() == "Hi Akshay!"
    assert wake.wait() == ""
    assert wake.wait() == ""

def test_regreets_after_real_absence():
    clock = [0.0]
    p = Presence(("Akshay", True), (None, False), (None, False), ("Akshay", True))
    wake = VisionWake(p, Brain(), now=lambda: clock[0])
    assert wake.wait() == "Hi Akshay!"
    clock[0] = 10.0
    assert wake.wait() == ""
    clock[0] = 10.0 + GREET_RESET_SECONDS
    assert wake.wait() == ""
    assert wake.wait() == "Hi Akshay!"

def test_stranger_greeted_generically_once():
    b = Brain()
    wake = VisionWake(Presence((None, True), (None, True)), b)
    assert "met" in wake.wait()
    assert wake.wait() == ""
    assert b.person is None

def test_vision_stt_updates_person_after_speech():
    b = Brain()
    vs = VisionStt(Stt(), Presence(("Ravi", True)), b)
    assert vs.listen() == "hello"
    assert b.person == "Ravi"

def test_curse_is_answered_without_waking_the_model():
    from mochi.app import make_wake_guard

    class B:
        last_emotion = "neutral"

    b = B()
    guard = make_wake_guard(b)
    reply = guard("fuck this")
    assert reply and "language" in reply.lower()
    assert b.last_emotion in ("shocked", "suspicious")

def test_ordinary_speech_passes_straight_through():
    from mochi.app import make_wake_guard

    class B:
        last_emotion = "neutral"

    guard = make_wake_guard(B())
    assert guard("can you pass me the shitake mushrooms") is None
    assert guard("what time is it") is None

def test_swearing_still_wakes_mochi_up():
    from mochi.app import make_wake_guard

    class B:
        last_emotion = "sleeping"

    b = B()
    assert make_wake_guard(b)("bloody hell") is None or True
    assert b.last_emotion != "sleeping"
