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

def test_time_in_another_country():
    reply = answer_time("what is the time in india")
    assert reply and "India" in reply
    assert "London" in answer_time("what time is it in london")
    assert answer_time("what time is it") is not None


def test_language_request_declined_politely():
    from mochi.skills import answer_language

    assert "English" in answer_language("can you talk in telugu")
    assert "English" in answer_language("speak hindi")
    assert answer_language("what time is it") is None


def test_non_latin_never_reaches_the_voice():
    from mochi.brain.client import clean_speech

    assert clean_speech("నమస్కారం") == ""
    assert clean_speech("नमस्ते") == ""
    assert clean_speech("Hello there") == "Hello there"


def test_screen_query_phrasings():
    from mochi.skills import answer_screen as ans

    for q in [
        "what screen am i on",
        "on what screen am i",
        "which app am i using",
        "what am i doing",
        "what window am i in",
    ]:
        assert ans(q) is not None, q
    assert ans("what is on the screen in the movie") is None


def test_farewell_sleeps():
    moods = []
    skills = Skills(lambda _: None, moods.append)
    assert "Goodnight" in skills.handle("bye")
    assert moods == ["sleeping"]
    assert skills.handle("bye the way tell me about goodbyes in japan") is None


def test_skill_emotions_are_real_emotions():
    from mochi.constants import EMOTIONS, SKILL_EMOTIONS

    assert set(SKILL_EMOTIONS.values()) <= set(EMOTIONS)


def test_guess_emotion_fallback():
    from mochi.brain.client import guess_emotion

    assert guess_emotion("Sorry, I can't do that") == "sad"
    assert guess_emotion("Congratulations, that's amazing!") == "excited"
    assert guess_emotion("What do you mean?") == "curious"
    assert guess_emotion("The file is saved") == "neutral"


def test_screen_answer_without_windows():
    reply = answer_screen("what am i working on")
    assert reply is not None
    assert answer_screen("tell me a story") is None

def test_app_name_strips_document_prefix():
    assert app_name("client.py - Mochi - Visual Studio Code") == "Visual Studio Code"
    assert app_name("Untitled") == "Untitled"


def test_document_name_kept_for_context():
    from mochi.desktop import document_name

    assert document_name("client.py - Mochi - Visual Studio Code") == "Mochi"
    assert document_name("Inbox (12) - Gmail") == "Inbox (12)"
    assert document_name("Untitled") == ""

def test_context_note_has_time():
    note = context_note()
    assert "It is" in note and ":" in note
