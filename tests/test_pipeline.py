from mochi.constants import EMOTIONS, STATE_EMOTION
from mochi.voice.pipeline import State, VoicePipeline


class Wake:
    def wait(self):
        return ""

class Stt:
    def __init__(self, *texts):
        self.texts = list(texts)

    def listen(self):
        return self.texts.pop(0) if self.texts else ""

class Brain:
    def __init__(self):
        self.asked = []
        self.last_emotion = "happy"
        self.last_blocks = []

    def chat_stream(self, text):
        self.asked.append(text)
        yield f"echo: {text}."
        yield "More."

class Tts:
    def __init__(self):
        self.spoken = []
        self.flushes = 0

    def say(self, text):
        self.spoken.append(text)

    def flush(self):
        self.flushes += 1

def build(*texts):
    states = []
    brain, tts = Brain(), Tts()
    pipe = VoicePipeline(Wake(), Stt(*texts), brain, tts, states.append)
    return pipe, brain, tts, states

def test_single_turn_speaks_per_sentence():
    pipe, brain, tts, states = build("hello")
    assert pipe.converse() == "echo: hello. More."
    assert brain.asked == ["hello"]
    assert tts.spoken == ["echo: hello.", "More."]
    assert tts.flushes == 1
    assert states == [
        State.LISTENING,
        State.THINKING,
        State.SPEAKING,
        State.LISTENING,
        State.IDLE,
    ]

def test_multi_turn_conversation_without_rewake():
    pipe, brain, tts, states = build("hi", "how are you")
    assert pipe.converse() != ""
    assert brain.asked == ["hi", "how are you"]
    assert len(tts.spoken) == 4
    assert states.count(State.LISTENING) == 3
    assert states[-1] == State.IDLE

def test_silence_ends_conversation():
    pipe, brain, tts, states = build()
    assert pipe.converse() == ""
    assert brain.asked == []
    assert tts.spoken == []
    assert states == [State.LISTENING, State.IDLE]

def test_wake_greeting_is_spoken_not_asked():
    class GreetWake:
        def wait(self):
            return "Hi Akshay!"

    states = []
    brain, tts = Brain(), Tts()
    pipe = VoicePipeline(GreetWake(), Stt(), brain, tts, states.append)
    pipe.converse()
    assert tts.spoken == ["Hi Akshay!"]
    assert brain.asked == []
    assert states[0] == State.SPEAKING

def test_intercept_bypasses_brain():
    brain, tts = Brain(), Tts()
    pipe = VoicePipeline(
        Wake(), Stt("show your expressions"), brain, tts, intercept=lambda t: "Watch!"
    )
    assert pipe.converse() == "Watch!"
    assert brain.asked == []
    assert tts.spoken == ["Watch!"]

def test_display_blocks_forwarded():
    shown = []
    brain, tts = Brain(), Tts()
    brain.last_blocks = ["print('hi')"]
    pipe = VoicePipeline(Wake(), Stt("code please"), brain, tts, on_display=shown.append)
    pipe.converse()
    assert shown == ["print('hi')"]

class Mem:
    def __init__(self, fact):
        self.fact = fact
        self.saved = []

    def extract(self):
        return self.fact

    def save(self, fact):
        self.saved.append(fact)

def test_memory_saved_on_spoken_yes():
    brain, tts = Brain(), Tts()
    mem = Mem("Akshay likes tea")
    pipe = VoicePipeline(Wake(), Stt("hi", "how are you", "", "yes please"), brain, tts, memory=mem)
    pipe.converse()
    assert mem.saved == ["Akshay likes tea"]
    assert any("remember" in s.lower() for s in tts.spoken)

def test_memory_declined_not_saved():
    brain, tts = Brain(), Tts()
    mem = Mem("Akshay likes tea")
    pipe = VoicePipeline(Wake(), Stt("hi", "how are you", "", "no thanks"), brain, tts, memory=mem)
    pipe.converse()
    assert mem.saved == []

def test_silent_reply_gets_spoken_fallback():
    class Mute(Brain):
        def chat_stream(self, text):
            self.asked.append(text)
            return iter(())

    brain, tts = Mute(), Tts()
    pipe = VoicePipeline(Wake(), Stt("recipe please"), brain, tts)
    pipe.converse()
    assert tts.spoken and "screen" not in tts.spoken[0]

def test_silent_reply_with_code_points_at_screen():
    class Fenced(Brain):
        def chat_stream(self, text):
            self.asked.append(text)
            self.last_blocks = ["print(1)"]
            return iter(())

    brain, tts = Fenced(), Tts()
    pipe = VoicePipeline(Wake(), Stt("write code"), brain, tts)
    pipe.converse()
    assert "screen" in tts.spoken[0]

def test_no_memory_ask_after_a_single_turn():
    brain, tts = Brain(), Tts()
    mem = Mem("some fact")
    VoicePipeline(Wake(), Stt("hi"), brain, tts, memory=mem).converse()
    assert mem.saved == []
    assert all("remember" not in s.lower() for s in tts.spoken)

def test_no_memory_ask_when_nothing_was_said():
    brain, tts = Brain(), Tts()
    mem = Mem("stale fact")
    pipe = VoicePipeline(Wake(), Stt(), brain, tts, memory=mem)
    pipe.converse()
    assert tts.spoken == []
    assert mem.saved == []

def test_every_state_maps_to_a_real_emotion():
    assert set(STATE_EMOTION) == {s.value for s in State}
    assert set(STATE_EMOTION.values()) <= set(EMOTIONS)
