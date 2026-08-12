from mochi.app import VisionStt, VisionWake


class Presence:
    def __init__(self, *answers):
        self.answers = list(answers)

    def whos_there(self, tries=6):
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

def test_regreets_after_absence():
    p = Presence(("Akshay", True), (None, False), ("Akshay", True))
    wake = VisionWake(p, Brain())
    assert wake.wait() == "Hi Akshay!"
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
