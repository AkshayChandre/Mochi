import pytest

np = pytest.importorskip("numpy")

from mochi.vision.recognition import FaceDB  # noqa: E402


def vec(seed):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=512).astype(np.float32)
    return v / np.linalg.norm(v)


def test_enroll_and_identify(tmp_path):
    db = FaceDB(str(tmp_path / "t.db"))
    db.add("akshay", vec(1))
    db.add("ravi", vec(2))
    name, score = db.identify(vec(1) + np.float32(0.01))
    assert name == "akshay"
    assert score > 0.9


def test_stranger_below_threshold(tmp_path):
    db = FaceDB(str(tmp_path / "t.db"))
    db.add("akshay", vec(1))
    name, score = db.identify(vec(99))
    assert name is None
    assert score < 0.45


def test_re_enroll_updates_instead_of_duplicating(tmp_path):
    db = FaceDB(str(tmp_path / "t.db"))
    db.add("akshay", vec(1))
    db.add("akshay", vec(2))
    assert len(db.all()) == 1
