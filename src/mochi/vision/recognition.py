from __future__ import annotations

import sqlite3
import sys
import threading
import time

import numpy as np

from mochi.constants import (
    CAMERA_INDEX,
    DB_PATH,
    ENROLL_FRAMES,
    FACE_MATCH_THRESHOLD,
    PRESENCE_TRIES,
    STRANGER_FRAMES,
)


class FaceDB:
    def __init__(self, path: str = DB_PATH) -> None:
        # the ambient thread reads this too
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS persons ("
            "id INTEGER PRIMARY KEY, name TEXT UNIQUE, embedding BLOB, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )

    def add(self, name: str, embedding: np.ndarray) -> None:
        blob = embedding.astype(np.float32).tobytes()
        self.conn.execute(
            "INSERT INTO persons(name, embedding) VALUES(?, ?) "
            "ON CONFLICT(name) DO UPDATE SET embedding = excluded.embedding",
            (name, blob),
        )
        self.conn.commit()

    def all(self) -> list[tuple[str, np.ndarray]]:
        rows = self.conn.execute("SELECT name, embedding FROM persons").fetchall()
        return [(n, np.frombuffer(b, dtype=np.float32)) for n, b in rows]

    # ponytail: linear cosine scan, fine below ~10k people; sqlite-vec if ever beyond
    def identify(self, embedding: np.ndarray) -> tuple[str | None, float]:
        best, score = None, 0.0
        emb = embedding / np.linalg.norm(embedding)
        for name, known in self.all():
            s = float(np.dot(emb, known / np.linalg.norm(known)))
            if s > score:
                best, score = name, s
        return (best, score) if score >= FACE_MATCH_THRESHOLD else (None, score)

def track_stranger(seen: list[np.ndarray], emb: np.ndarray) -> list[np.ndarray]:
    if seen and float(np.dot(emb, seen[-1])) < FACE_MATCH_THRESHOLD:
        return [emb]
    return [*seen, emb]

class Recognizer:
    def __init__(self) -> None:
        import cv2
        from insightface.app import FaceAnalysis

        self.app = FaceAnalysis(name="buffalo_s", providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self.cam = cv2.VideoCapture(CAMERA_INDEX)
        self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.lock = threading.Lock()  # conversation and ambient threads share the camera
        if not self.cam.isOpened():
            raise RuntimeError(f"no camera at index {CAMERA_INDEX} (see constants.CAMERA_INDEX)")

    def embedding(self) -> np.ndarray | None:
        with self.lock:
            for _ in range(3):
                self.cam.grab()
            ok, frame = self.cam.read()
        if not ok:
            return None
        faces = self.app.get(frame)
        if not faces:
            return None
        largest = max(faces, key=lambda f: f.bbox[2] - f.bbox[0])
        return largest.normed_embedding

class Presence:
    def __init__(self) -> None:
        self.db = FaceDB()
        self.rec = Recognizer()
        self.cached: tuple[str | None, bool] = (None, False)
        self.cached_at = 0.0

    # face detection costs a few hundred ms; re-running it every utterance
    # was the biggest chunk of per-turn latency
    def whos_there(self, tries: int = PRESENCE_TRIES, max_age: float = 0.0):
        if max_age and time.monotonic() - self.cached_at < max_age:
            return self.cached
        for _ in range(tries):
            emb = self.rec.embedding()
            if emb is not None:
                self.cached = (self.db.identify(emb)[0], True)
                self.cached_at = time.monotonic()
                return self.cached
            time.sleep(0.2)
        self.cached, self.cached_at = (None, False), time.monotonic()
        return self.cached

def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    db = FaceDB()
    if cmd == "list":
        for name, _ in db.all():
            print(name)
        return
    rec = Recognizer()
    if cmd == "enroll":
        if len(sys.argv) < 3:
            sys.exit('usage: mochi-vision enroll "Name"')
        name = sys.argv[2]
        print(f"look at the camera, {name}...")
        embs: list[np.ndarray] = []
        while len(embs) < ENROLL_FRAMES:
            emb = rec.embedding()
            if emb is not None:
                embs.append(emb)
                print(f"captured {len(embs)}/{ENROLL_FRAMES}")
            time.sleep(0.3)
        mean = np.mean(embs, axis=0)
        db.add(name, mean / np.linalg.norm(mean))
        print(f"enrolled {name}")
        return
    print("watching - Ctrl+C to quit; strangers get asked for a name")
    strangers: list[np.ndarray] = []
    try:
        while True:
            emb = rec.embedding()
            if emb is None:
                strangers = []
                time.sleep(0.5)
                continue
            name, score = db.identify(emb)
            print(f"{name or 'stranger'}  ({score:.2f})")
            if name:
                strangers = []
            else:
                strangers = track_stranger(strangers, emb)
                if len(strangers) >= STRANGER_FRAMES:
                    new = input("new face! what's their name? (Enter to skip): ").strip()
                    if new:
                        mean = np.mean(strangers, axis=0)
                        db.add(new, mean / np.linalg.norm(mean))
                        print(f"enrolled {new}")
                    strangers = []
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
