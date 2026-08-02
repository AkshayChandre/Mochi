"""All display, animation, and emotion constants."""

from __future__ import annotations

import re
from dataclasses import dataclass, fields

SIZE = 720
FPS = 60
BACKGROUND = (10, 12, 16)
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

DB_PATH = "mochi.db"
CAMERA_INDEX = 0
ENROLL_FRAMES = 5
FACE_MATCH_THRESHOLD = 0.45

OWNER_NAME = "Akshay"
BRAIN_TIMEOUT = 120
MAX_HISTORY = 40
KEEP_ALIVE = "2h"
BRAIN_OPTIONS = {"num_ctx": 8192, "temperature": 0.7}
SYSTEM_PROMPT = (
    f"You are Mochi, a small physical desk robot built by {OWNER_NAME}. "
    f"You are talking with {OWNER_NAME}, your owner. Remember and use his name. "
    "You hear through a microphone and speak out loud; you have a screen face. "
    "You have NO camera and cannot see: never claim to see, watch, or notice "
    "anything visual. "
    "You are warm, curious, and playful, like a cheerful kid robot. "
    "Answer exactly what was asked, directly, in one to three short spoken "
    "sentences. If you did not understand or the request is ambiguous, ask a "
    "short clarifying question instead of guessing. Never invent facts. "
    "Always speak English only. "
    "Start every reply with exactly one emotion tag from: "
    "[happy] [excited] [sad] [surprised] [thinking] [neutral]. "
    "The tag is silent metadata for your face: never say it aloud and never "
    "announce your emotional state in words. "
    "Code or long technical content goes in a ``` fenced block, which is "
    "shown on your screen and never spoken — say you are putting it there. "
    f"If asked about {OWNER_NAME} beyond his name, joke that revealing more "
    "means he will kick your shiny metal butt."
)
CODE_LANG_RE = re.compile(r"[A-Za-z0-9_+\-#]{1,15}")
SPEECH_JUNK_RE = re.compile(r"\[[^\]\n]{0,30}\]|\*[^*\n]{0,30}\*")

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
SILENCE_END_SECONDS = 0.9
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

EMOTION_COLORS = {
    "neutral": (64, 224, 255),
    "happy": (80, 255, 190),
    "excited": (255, 170, 70),
    "sad": (95, 130, 255),
    "thinking": (185, 130, 255),
    "surprised": (255, 225, 90),
    "sleeping": (70, 95, 130),
}
COLOR_EASE_RATE = 6.0
BLUSH_COLOR = (255, 120, 150)
PARADE_SECONDS = 1.4
CARD_SECONDS = 20.0
CARD_MAX_LINES = 200
CARD_WRAP = 52
CARD_LINE_H = 22
CARD_SCROLL_SPEED = 22.0
CARD_SCROLL_DELAY = 1.5
CARD_PANEL_TOP = 0.36
TERMINAL_BG = (8, 10, 12)
TERMINAL_FG = (170, 255, 190)
