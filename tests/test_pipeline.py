from mochi.voice.pipeline import State, VoicePipeline


class Wake:
    def wait(self):
        pass


class Stt:
    def __init__(self, text):
        self.text = text

    def listen(self):
        return self.text


class Brain:
    def __init__(self):
        self.asked = []

    def chat(self, text):
        self.asked.append(text)
        return f"echo: {text}"


class Tts:
    def __init__(self):
        self.spoken = []

    def say(self, text):
        self.spoken.append(text)


def build(text="hello"):
    states = []
    brain, tts = Brain(), Tts()
    pipe = VoicePipeline(Wake(), Stt(text), brain, tts, states.append)
    return pipe, brain, tts, states


def test_full_turn():
    pipe, brain, tts, states = build("hello")
    assert pipe.once() == "echo: hello"
    assert brain.asked == ["hello"]
    assert tts.spoken == ["echo: hello"]
    assert states == [State.LISTENING, State.THINKING, State.SPEAKING, State.IDLE]


def test_empty_utterance_short_circuits():
    pipe, brain, tts, states = build("   ")
    assert pipe.once() == ""
    assert brain.asked == []
    assert tts.spoken == []
    assert states == [State.LISTENING, State.IDLE]


def test_state_emotion_mapping():
    pipe, *_ = build()
    assert pipe.emotion() == "neutral"
    pipe.set_state(State.THINKING)
    assert pipe.emotion() == "thinking"
