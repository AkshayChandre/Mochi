from mochi.brain.memory import Memory, MemoryStore


class FakeBrain:
    def __init__(self, reply):
        self.reply = reply
        self.person = "Ravi"
        self.history = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "Ravi: I love tea"},
            {"role": "assistant", "content": "nice"},
        ]

    def ask_once(self, system, user, timeout=None):
        return self.reply


def test_store_recall_filters_by_person(tmp_path):
    s = MemoryStore(str(tmp_path / "m.db"))
    s.add("Ravi", "loves tea")
    s.add("Akshay", "plays basketball")
    s.add(None, "wifi password is on the fridge")
    got = s.recall("Ravi")
    assert any("loves tea" in g for g in got)
    assert any("fridge" in g for g in got)
    assert all("basketball" not in g for g in got)


def test_extract_returns_fact(tmp_path):
    m = Memory(FakeBrain("Ravi loves tea"), MemoryStore(str(tmp_path / "m.db")))
    assert m.extract() == "Ravi loves tea"


def test_extract_rejects_none_and_duplicates(tmp_path):
    store = MemoryStore(str(tmp_path / "m.db"))
    assert Memory(FakeBrain("NONE"), store).extract() is None
    store.add("Ravi", "ravi loves tea")
    assert Memory(FakeBrain("Ravi loves tea"), store).extract() is None


def test_explicit_remember_captures_fact(tmp_path):
    m = Memory(FakeBrain(""), MemoryStore(str(tmp_path / "m.db")))
    assert m.explicit("Mochi remember my DOB is 5th August") == "DOB is 5th August"
    assert m.explicit("remember that I love tea") == "I love tea"
    assert m.explicit("what is the weather") is None


def test_extract_survives_brain_errors(tmp_path):
    class Broken(FakeBrain):
        def ask_once(self, system, user, timeout=None):
            raise OSError("offline")

    assert Memory(Broken(""), MemoryStore(str(tmp_path / "m.db"))).extract() is None


def test_save_attributes_to_person(tmp_path):
    store = MemoryStore(str(tmp_path / "m.db"))
    m = Memory(FakeBrain(""), store)
    m.save("loves tea")
    assert store.recall("Ravi") == ["Ravi: loves tea"]
