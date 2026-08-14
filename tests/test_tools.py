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
