from datetime import datetime, timedelta

from mochi.agenda import Agenda, speak_when


def fresh(tmp_path) -> Agenda:
    return Agenda(str(tmp_path / "test.db"))


def test_upcoming_is_ordered_and_window_bounded(tmp_path):
    a = fresh(tmp_path)
    now = datetime.now()
    a.add("dentist", now + timedelta(days=2))
    a.add("standup", now + timedelta(hours=1))
    a.add("next month", now + timedelta(days=40))
    titles = [t for _, t, _ in a.upcoming(7, now)]
    assert titles == ["standup", "dentist"]


def test_past_events_do_not_come_back(tmp_path):
    a = fresh(tmp_path)
    now = datetime.now()
    a.add("yesterday", now - timedelta(days=1))
    assert a.upcoming(7, now) == []


def test_drop_matches_loosely_and_counts(tmp_path):
    a = fresh(tmp_path)
    now = datetime.now()
    a.add("Dentist appointment", now + timedelta(days=1))
    assert a.drop("dentist") == 1
    assert a.drop("dentist") == 0


def test_drop_leaves_the_past_alone(tmp_path):
    a = fresh(tmp_path)
    now = datetime.now()
    a.add("old dentist", now - timedelta(days=3))
    assert a.drop("dentist") == 0


def test_speak_when_reads_like_a_person():
    base = datetime(2026, 8, 11, 9, 0)
    assert speak_when(base.replace(hour=15), base) == "today at 3:00 PM"
    assert speak_when(base + timedelta(days=1), base) == "tomorrow at 9:00 AM"
    assert speak_when(base + timedelta(days=3), base).startswith("Friday at")
    assert "August" in speak_when(base + timedelta(days=20), base)
