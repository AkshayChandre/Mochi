from __future__ import annotations

import base64
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from mochi.config import CONNECTIONS
from mochi.constants import (
    CAMERA_INDEX,
    JPEG_QUALITY,
    SIGHT_BLIND,
    SIGHT_MISSING,
    SIGHT_NOTHING,
    SIGHT_OFFLINE,
    SIGHT_WIDTH,
    VISION_KEEP_ALIVE,
    VISION_OPTIONS,
    VISION_TIMEOUT,
)


def encode(frame) -> str:
    """Shrink before sending. The model downscales anyway, and a 1080p frame
    is megabytes of base64 for no extra detail."""
    import cv2

    height, width = frame.shape[:2]
    if width > SIGHT_WIDTH:
        scale = SIGHT_WIDTH / width
        frame = cv2.resize(frame, (SIGHT_WIDTH, int(height * scale)))
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if not ok:
        return ""
    return base64.b64encode(buffer).decode()

class Eyes:
    """Sight on demand. Mochi has no continuous vision: a frame is captured
    at the moment this is called and nowhere else."""

    def __init__(self, camera, host: str | None = None, port: int | None = None,
                 model: str | None = None) -> None:
        host = host or CONNECTIONS.brain_host
        port = port or CONNECTIONS.brain_port
        self.url = f"http://{host}:{port}/api/chat"
        self.model = model or CONNECTIONS.vision_model
        self.camera = camera

    def look(self, question: str) -> str:
        if self.camera is None:
            return SIGHT_BLIND
        frame = self.camera.frame()
        if frame is None:
            return SIGHT_BLIND
        picture = encode(frame)
        if not picture:
            return SIGHT_BLIND
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": question.strip(), "images": [picture]}],
            "stream": False,
            # short, so the chat model can have its memory back on machines
            # where the two do not fit at once
            "keep_alive": VISION_KEEP_ALIVE,
            "options": VISION_OPTIONS,
        }
        request = Request(
            self.url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
        )
        try:
            with urlopen(request, timeout=VISION_TIMEOUT) as resp:
                seen = json.load(resp)["message"]["content"].strip()
        except HTTPError as err:
            # a model that was never pulled answers 404, which is not the
            # same as a dead server and should not be reported as one
            print(f"sight: {self.model} -> {err.code} {err.reason}")
            return SIGHT_MISSING.format(model=self.model) if err.code == 404 else SIGHT_OFFLINE
        except (OSError, KeyError, ValueError):
            return SIGHT_OFFLINE
        return " ".join(seen.split()) or SIGHT_NOTHING

def main() -> None:
    # the eyes with no model deciding whether to use them: says which half
    # is broken when Mochi will not answer what it is looking at
    import sys
    import time
    from types import SimpleNamespace

    import cv2

    cam = cv2.VideoCapture(CAMERA_INDEX)
    for _ in range(3):
        cam.grab()
    ok, frame = cam.read()
    cam.release()
    if not ok:
        print(SIGHT_BLIND)
        return
    started = time.monotonic()
    said = Eyes(SimpleNamespace(frame=lambda: frame)).look(
        " ".join(sys.argv[1:]) or "what do you see?"
    )
    print(f"{said}\n({time.monotonic() - started:.1f}s)")

if __name__ == "__main__":
    main()
