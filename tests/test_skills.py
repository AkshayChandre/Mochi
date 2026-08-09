import time

from mochi.desktop import app_name, context_note
from mochi.skills import Skills, answer_screen, answer_time, parse_timer


def test_parse_timer_units():
    assert parse_timer("set a timer for 5 minutes") == (300, "5 minutes")
    assert parse_timer("timer for 1 minute") == (60, "1 minute")
    assert parse_timer("remind me in 2 hours") == (7200, "2 hours")
    assert parse_timer("30 seconds") == (30, "30 seconds")
    assert parse_timer("tell me a joke") is None


def test_timer_fires_and_announces():
    spoken = []
    skills = Skills(spoken.append)
    assert "10 seconds" in skills.start_timer(0, "10 seconds")
    time.sleep(0.05)
    assert spoken and "timer is up" in spoken[0]


def test_timer_only_on_timer_intent():
    skills = Skills(lambda _: None)
    assert skills.handle("set a timer for 5 minutes") is not None
    assert skills.handle("I ran 5 minutes today") is None


def test_time_and_date_answers():
    assert answer_time("what time is it") is not None
    assert "," in answer_time("what's the date today")
    assert answer_time("how are you") is None


def test_screen_answer_without_windows():
    reply = answer_screen("what am i working on")
    assert reply is not None
    assert answer_screen("tell me a story") is None


def test_app_name_strips_document_prefix():
    assert app_name("client.py - Mochi - Visual Studio Code") == "Visual Studio Code"
    assert app_name("Untitled") == "Untitled"


def test_context_note_has_time():
    note = context_note()
    assert "It is" in note and ":" in note
