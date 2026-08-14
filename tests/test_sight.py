import io
import json

import pytest

from mochi.constants import SIGHT_BLIND, SIGHT_NOTHING, SIGHT_OFFLINE
from mochi.vision import sight
from mochi.vision.sight import Eyes


class Camera:
    def __init__(self, value="a frame"):
        self.value = value
        self.grabs = 0

    def frame(self):
        self.grabs += 1
        return self.value


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def answering(monkeypatch, text, captured=None):
    monkeypatch.setattr(sight, "encode", lambda frame: "BASE64PICTURE")

    def fake(req, timeout):
        if captured is not None:
            captured.update(json.loads(req.data))
        return Resp(json.dumps({"message": {"content": text}}).encode())

    monkeypatch.setattr(sight, "urlopen", fake)


def test_look_sends_the_picture_and_the_question(monkeypatch):
    seen = {}
    answering(monkeypatch, "A blue coffee mug.", seen)
    eyes = Eyes(Camera(), host="test", port=1, model="moondream")
    assert eyes.look("what am I holding?") == "A blue coffee mug."
    message = seen["messages"][0]
    assert message["images"] == ["BASE64PICTURE"]
    assert message["content"] == "what am I holding?"
    assert seen["model"] == "moondream"
    assert seen["stream"] is False


def test_the_owners_own_question_is_passed_through(monkeypatch):
    """One tool covers describing, reading and counting because the question
    goes straight to the model."""
    seen = {}
    answering(monkeypatch, "It says CAUTION WET FLOOR.", seen)
    Eyes(Camera(), host="test", port=1).look("read the sign")
    assert seen["messages"][0]["content"] == "read the sign"


def test_no_camera_is_admitted_not_hallucinated():
    assert Eyes(None, host="test", port=1).look("what is this") == SIGHT_BLIND


def test_a_dead_camera_is_admitted(monkeypatch):
    monkeypatch.setattr(sight, "encode", lambda frame: "X")
    assert Eyes(Camera(None), host="test", port=1).look("what is this") == SIGHT_BLIND


def test_unencodable_frame_is_admitted(monkeypatch):
    monkeypatch.setattr(sight, "encode", lambda frame: "")
    assert Eyes(Camera(), host="test", port=1).look("what is this") == SIGHT_BLIND


def test_vision_model_offline_returns_words_not_an_exception(monkeypatch):
    monkeypatch.setattr(sight, "encode", lambda frame: "X")
    monkeypatch.setattr(
        sight, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("no moondream"))
    )
    assert Eyes(Camera(), host="test", port=1).look("what is this") == SIGHT_OFFLINE


def test_empty_answer_is_admitted(monkeypatch):
    answering(monkeypatch, "   ")
    assert Eyes(Camera(), host="test", port=1).look("what is this") == SIGHT_NOTHING


def test_multiline_answer_is_flattened_for_speech(monkeypatch):
    answering(monkeypatch, "A mug.\n\nIt is  blue.\n")
    assert Eyes(Camera(), host="test", port=1).look("what") == "A mug. It is blue."


def test_looking_grabs_exactly_one_frame(monkeypatch):
    answering(monkeypatch, "A mug.")
    camera = Camera()
    Eyes(camera, host="test", port=1).look("what")
    assert camera.grabs == 1, "sight is on demand, not a video feed"


def test_encode_shrinks_a_big_frame():
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    from mochi.constants import SIGHT_WIDTH

    big = np.zeros((1080, 1920, 3), dtype=np.uint8)
    data = sight.encode(big)
    assert data
    import base64

    decoded = cv2.imdecode(np.frombuffer(base64.b64decode(data), np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape[1] == SIGHT_WIDTH

def missing(monkeypatch, code):
    from urllib.error import HTTPError

    monkeypatch.setattr(sight, "encode", lambda frame: "X")

    def boom(req, timeout):
        raise HTTPError("http://test", code, "err", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr(sight, "urlopen", boom)


def test_vision_model_not_pulled_says_how_to_fix_it(monkeypatch):
    missing(monkeypatch, 404)
    said = Eyes(Camera(), host="test", port=1, model="moondream").look("what")
    assert "ollama pull moondream" in said


def test_other_http_errors_fall_back_to_the_generic_line(monkeypatch):
    missing(monkeypatch, 500)
    assert Eyes(Camera(), host="test", port=1).look("what") == SIGHT_OFFLINE
