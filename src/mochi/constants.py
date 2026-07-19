"""All display, animation, and emotion constants."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields

SIZE = 720
FPS = 60
BACKGROUND = (10, 12, 16)
EYE_COLOR = (64, 224, 255)
BEZEL = (30, 34, 42)
EASE_RATE = 9.0
GAZE_RANGE = (46, 34)


@dataclass(frozen=True)
class Emotion:
    w: float = 150.0
    h: float = 178.0
    r: float = 64.0
    tilt: float = 0.0
    crescent: float = 0.0
    squint: float = 0.0
    mouth: float = 0.0
    bounce: float = 0.0
    dim: float = 1.0
    gaze_lock: tuple[float, float] | None = None


EMOTIONS: dict[str, Emotion] = {
    "neutral": Emotion(),
    "happy": Emotion(h=164, crescent=0.6, mouth=1.0),
    "sad": Emotion(h=142, tilt=14, mouth=-1.0, gaze_lock=(0.0, 0.55)),
    "thinking": Emotion(squint=0.55, gaze_lock=(-0.6, -0.55)),
    "surprised": Emotion(w=186, h=198, r=96, mouth=0.15),
    "excited": Emotion(h=150, crescent=0.7, mouth=1.0, bounce=1.0),
    "sleeping": Emotion(h=16, r=8, dim=0.28, gaze_lock=(0.0, 0.0)),
}
EMOTION_KEYS = list(EMOTIONS)
NUMERIC_FIELDS = [f.name for f in fields(Emotion) if f.name != "gaze_lock"]

EYE_GAP = 105
EYE_RAISE = 30
GAZE_LERP_RATE = 8.0
WANDER_INTERVAL = (1.4, 3.8)
WANDER_RADIUS = 0.8

BLINK_SPEED = 1 / 0.09
BLINK_INTERVAL = (2.0, 5.5)
DOUBLE_BLINK_CHANCE = 0.15
DOUBLE_BLINK_DELAY = 0.28

BREATH_PERIOD = 4.2
BREATH_AMP = 0.008
BOUNCE_FREQ = 9.0
BOUNCE_AMP = 26.0
SQUINT_FACTOR = 0.55

STRETCH_GAIN = 0.05
STRETCH_CROSS = 0.03
STRETCH_LIMITS = (0.88, 1.14)

MOUTH_HALF_WIDTH = 42
MOUTH_DEPTH = 16
MOUTH_THICKNESS = 6
MOUTH_OFFSET_Y = 128
MOUTH_VISIBLE_MIN = 0.08

AUTOPILOT_INTERVAL = 3.5

OWNER_NAME = "Akshay"
BRAIN_TIMEOUT = 120
MAX_HISTORY = 40
SYSTEM_PROMPT = (
    f"You are Mochi, a small desk companion robot owned by {OWNER_NAME}. "
    "You are warm, curious, and playful, like a cheerful kid robot. "
    "Keep replies short and conversational, one to three sentences. "
    "Start every reply with exactly one emotion tag from: "
    "[happy] [excited] [sad] [surprised] [thinking] [neutral]. "
    "Example: [happy] Hi Akshay! Nothing comes before the tag."
)
EMOTION_TAG = re.compile(r"^\s*\[(\w+)\]\s*")

SPEECH_SECONDS_PER_CHAR = 0.03

STATE_EMOTION = {
    "idle": "neutral",
    "listening": "surprised",
    "thinking": "thinking",
    "speaking": "happy",
}

SAMPLE_RATE = 16000
FRAME_SECONDS = 0.03
SILENCE_RMS = 0.010
SILENCE_END_SECONDS = 1.2
CONVERSATION_WAIT_SECONDS = 8.0
MAX_UTTERANCE_SECONDS = 20.0
MIN_SPEECH_SECONDS = 0.3
WHISPER_MODEL = "base.en"
WHISPER_DEVICE = "cpu"

VOICE_NAME = "en_US-amy-medium"
VOICES_DIR = "voices"
PITCH_FACTOR = 1.22
TREMOLO_HZ = 26.0
TREMOLO_DEPTH = 0.10

SOUND_SAMPLE_RATE = 22050
THINK_BLIP_INTERVAL = 0.8

TALK_FREQ = 13.0
TALK_BASE = 0.55
TALK_AMP = 0.45
