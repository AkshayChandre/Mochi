import json

from mochi.context import LocalSensors
from mochi.skills import Skills
from mochi.tools import TOOLS, Toolbox


class FakeSensors:
    def screen(self):
        return ("Visual Studio Code", "README.md")

    def clock(self, place=""):
        return ("Monday 01 January, 09:00 AM", place.title())

def box(**kw):
    return Toolbox(Skills(lambda *_: None, lambda _: None), FakeSensors(), **kw)

def test_every_tool_has_a_handler():
    for tool in TOOLS:
        assert hasattr(Toolbox, tool["function"]["name"]), tool["function"]["name"]

def test_tool_schemas_are_valid_json():
    json.dumps(TOOLS)
    for tool in TOOLS:
        fn = tool["function"]
        assert fn["description"] and isinstance(fn["parameters"]["required"], list)

def test_screen_and_time_tools():
    tb = box()
    assert "README.md" in tb.run("what_is_on_screen", {})
    assert "India" in tb.run("get_time", {"place": "india"})

def test_reminder_tool_takes_structured_args():
    tb = box()
    reply = tb.run("set_reminder", {"task": "drink water", "minutes": 1})
    assert "drink water" in reply
    assert "drink water" in tb.run("list_reminders", {})
    assert "Cleared" in tb.run("cancel_reminders", {})

def test_unknown_tool_and_bad_args_are_survivable():
    tb = box()
    assert "no tool" in tb.run("make_coffee", {})
    assert "failed" in tb.run("set_reminder", {"wrong": 1})

def test_arguments_parse_from_json_string():
    assert Toolbox.parse_args('{"place": "tokyo"}') == {"place": "tokyo"}
    assert Toolbox.parse_args("not json") == {}
    assert Toolbox.parse_args({"a": 1}) == {"a": 1}

def test_local_sensors_shape():
    app, doc = LocalSensors().screen()
    assert isinstance(app, str) and isinstance(doc, str)
    when, where = LocalSensors().clock("india")
    assert "," in when and where == "India"

class FakeFace:
    def __init__(self):
        self.gesture = None
        self.banner = None
        self.emotion = None

    def set_emotion(self, name):
        self.emotion = name

    def play_gesture(self, kind):
        if kind not in ("nod", "shake"):
            raise ValueError(kind)
        self.gesture = kind

    def show_banner(self, text):
        self.banner = text

def test_gesture_tool_moves_the_face():
    face = FakeFace()
    assert "nod" in box(face=face).run("gesture", {"kind": "Nod"})
    assert face.gesture == "nod"

def test_unknown_gesture_is_refused_not_crashed():
    face = FakeFace()
    assert "can't" in box(face=face).run("gesture", {"kind": "backflip"})
    assert face.gesture is None

def test_add_event_rejects_vague_times_instead_of_inventing_one(tmp_path):
    from mochi.agenda import Agenda

    tb = box(agenda=Agenda(str(tmp_path / "a.db")))
    assert "real date" in tb.run("add_event", {"title": "x", "when": "sometime next week"})

def test_calendar_round_trip_through_the_tools(tmp_path):
    from datetime import datetime, timedelta

    from mochi.agenda import Agenda

    face = FakeFace()
    tb = box(agenda=Agenda(str(tmp_path / "a.db")), face=face)
    when = (datetime.now() + timedelta(days=1)).replace(microsecond=0).isoformat()
    assert "dentist" in tb.run("add_event", {"title": "dentist", "when": when})
    assert face.banner == "dentist"
    assert "dentist" in tb.run("list_events", {})
    assert "Removed 1" in tb.run("cancel_event", {"title": "dent"})
    assert "Nothing on your calendar" in tb.run("list_events", {"days": 30})

def test_weather_puts_the_temperature_on_the_face(monkeypatch):
    from mochi import tools as tools_mod

    face = FakeFace()
    monkeypatch.setattr(tools_mod.world, "weather", lambda p: f"{p}: 28 degrees, clear")
    assert "28 degrees" in box(face=face).run("weather", {})
    assert face.banner == "28°"

def test_weather_with_no_place_uses_home(monkeypatch):
    from mochi import tools as tools_mod
    from mochi.constants import OWNER_CITY

    monkeypatch.setattr(tools_mod.world, "weather", lambda p: p)
    assert box().run("weather", {}) == OWNER_CITY

class FakeEyes:
    def __init__(self, answer="A blue mug."):
        self.answer = answer
        self.asked = []

    def look(self, question):
        self.asked.append(question)
        return self.answer

def test_look_tool_passes_the_question_to_the_eyes():
    eyes, face = FakeEyes(), FakeFace()
    tb = box(eyes=eyes, face=face)
    assert tb.run("look", {"question": "what am I holding?"}) == "A blue mug."
    assert eyes.asked == ["what am I holding?"]

def test_look_without_a_camera_says_so():
    from mochi.constants import SIGHT_BLIND

    assert box().run("look", {"question": "what is this"}) == SIGHT_BLIND

def test_look_makes_the_face_peer():
    face = FakeFace()
    box(eyes=FakeEyes(), face=face).run("look", {"question": "what"})
    assert face.emotion == "curious"

class MoodBox:
    """Records what reached the brain, which is the half that sticks."""

    def __init__(self):
        self.moods = []

    def spy(self):
        return Toolbox(Skills(lambda *_: None, self.moods.append), FakeSensors(), face=self.face())

    def face(self):
        outer = self

        class Face:
            emotion = "neutral"

            def set_emotion(self, name):
                from mochi.constants import EMOTIONS

                if name not in EMOTIONS:
                    raise ValueError(name)
                self.emotion = name
                outer.shown = name

        outer.shown = None
        return Face()

def test_going_to_sleep_reaches_the_brain_not_just_the_face():
    """The face is repainted from brain.last_emotion on the next state change,
    so setting only the face meant goodnight never kept Mochi asleep."""
    m = MoodBox()
    tb = m.spy()
    assert tb.run("go_to_sleep", {}) == "eyes closed"
    assert m.moods == ["sleeping"]
    assert m.shown == "sleeping"

def test_show_expression_rejects_an_unknown_one_without_setting_a_mood():
    m = MoodBox()
    tb = m.spy()
    assert tb.run("show_expression", {"name": "banana"}) == "no expression called banana"
    assert m.moods == []

def test_show_expression_accepts_a_real_one():
    m = MoodBox()
    assert m.spy().run("show_expression", {"name": " Happy "}) == "showing happy"
    assert m.moods == ["happy"]

def test_a_reminder_that_fires_out_of_order_keeps_the_right_label():
    """Labels lived in a second list sliced off the end, so a timer finishing
    out of order shifted every remaining name along by one."""

    class Timer:
        def __init__(self, alive):
            self.alive = alive

        def is_alive(self):
            return self.alive

    skills = Skills(lambda *_: None, lambda _: None)
    skills.timers = [
        (Timer(True), "water the plants"),
        (Timer(False), "call mum"),
        (Timer(True), "stretch"),
    ]
    assert skills.pending() == ["water the plants", "stretch"]
