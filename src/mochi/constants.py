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
    style: str = "rect"
    lid: float = 0.0
    mouth_open: float = 0.0
    brow: float = 0.0
    brow_asym: float = 0.0
    tear: float = 0.0
    sparkle: float = 0.0
    wink: float = 0.0
    shake: float = 0.0

EMOTIONS: dict[str, Emotion] = {
    "neutral": Emotion(),
    "happy": Emotion(h=164, crescent=0.6, mouth=1.0),
    "sad": Emotion(h=142, tilt=14, mouth=-1.0, gaze_lock=(0.0, 0.55), tear=1.0),
    "thinking": Emotion(squint=0.55, gaze_lock=(-0.6, -0.55), brow=0.4, brow_asym=1.0),
    "surprised": Emotion(w=186, h=198, r=96, mouth=0.15),
    "excited": Emotion(h=150, crescent=0.7, mouth=1.0, bounce=1.0, sparkle=1.0),
    "angry": Emotion(w=164, h=96, r=20, mouth=-0.8, brow=1.0, shake=1.0),
    "love": Emotion(w=168, h=168, mouth=1.0, bounce=0.3, style="heart", sparkle=0.8),
    "curious": Emotion(w=152, h=176, squint=-0.5, brow=0.7, brow_asym=1.0, gaze_lock=(0.55, -0.5)),
    "confused": Emotion(w=170, h=170, mouth=-0.25, style="swirl", brow=0.5, brow_asym=1.0),
    "laughing": Emotion(h=136, crescent=0.95, mouth=1.0, bounce=0.8, tear=0.6),
    "shy": Emotion(w=138, h=132, crescent=0.35, mouth=0.5, gaze_lock=(-0.4, 0.5), wink=1.0),
    "smug": Emotion(w=168, lid=0.42, squint=0.2, mouth=0.6, brow=0.5, brow_asym=1.0),
    "bored": Emotion(w=170, lid=0.55, mouth=-0.15, gaze_lock=(0.0, 0.5)),
    "suspicious": Emotion(w=176, lid=0.48, mouth=-0.3, brow=0.85, gaze_lock=(-0.65, 0.1)),
    "sleepy": Emotion(w=160, lid=0.68, mouth_open=0.55, gaze_lock=(0.0, 0.4)),
    "starstruck": Emotion(w=176, h=176, style="star", sparkle=1.0, mouth=1.0, bounce=0.4),
    "shocked": Emotion(w=196, h=206, r=100, mouth_open=0.9, brow=0.5),
    "proud": Emotion(h=150, crescent=0.8, mouth=0.9, sparkle=0.5, brow=0.3),
    "cool": Emotion(w=186, h=104, r=16, style="shades", mouth=0.55, brow=0.0),
    "error": Emotion(w=150, h=150, style="x", mouth=-0.5, shake=0.5, dim=0.85),
    "sleeping": Emotion(h=16, r=8, dim=0.28, gaze_lock=(0.0, 0.0)),
}
EMOTION_KEYS = list(EMOTIONS)
NUMERIC_FIELDS = [f.name for f in fields(Emotion) if f.name not in ("gaze_lock", "style")]

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

GESTURES = ("nod", "shake")
GESTURE_SECONDS = 0.85
GESTURE_FREQ = 11.0
GESTURE_AMP = 30.0
BANNER_SECONDS = 4.0
BANNER_MARGIN = 0.82

DB_PATH = "mochi.db"
CAMERA_INDEX = 0
ENROLL_FRAMES = 5
FACE_MATCH_THRESHOLD = 0.45
STRANGER_FRAMES = 4
PRESENCE_TRIES = 6
GREETING = "Hi {name}!"
STRANGER_GREETING = "Hi there! I don't think we've met yet."
# glancing away, leaning back or a bad frame is not leaving the room; only
# a real absence earns a fresh greeting
GREET_RESET_SECONDS = 600.0

AGENDA_LIMIT = 20
AGENDA_DAYS = 7
AGENDA_ADDED = "Added: {title}, {when}."
AGENDA_EMPTY = "Nothing on your calendar for the next {days} days."
AGENDA_BAD_TIME = "I need a real date and time for that one."
AGENDA_DROPPED = "Removed {count} event{s}."
AGENDA_NOT_FOUND = "I don't have anything like that on the calendar."

WORLD_TIMEOUT = 6
USER_AGENT = "Mochi/0.1 (open-source desk robot)"
OFFLINE_REPLY = "I couldn't reach the internet just now."
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1&language=en"
FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,apparent_temperature,weather_code"
    "&daily=temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto"
)
# WMO weather codes, worded the way a person would say them out loud
WEATHER_CODES = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "freezing fog",
    51: "drizzling lightly", 53: "drizzling", 55: "drizzling hard",
    56: "freezing drizzle", 57: "freezing drizzle",
    61: "raining lightly", 63: "raining", 65: "pouring",
    66: "freezing rain", 67: "freezing rain",
    71: "snowing lightly", 73: "snowing", 75: "snowing hard", 77: "snow grains",
    80: "rain showers", 81: "rain showers", 82: "violent rain showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thundering", 96: "thundering with hail", 99: "thundering with hail",
}
NEWS_FEEDS = (
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
)
NEWS_LIMIT = 6
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{t}"
WIKI_SEARCH_URL = (
    "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}"
    "&srlimit=1&format=json"
)
WIKI_MAX_CHARS = 320

MEMORY_RECALL_LIMIT = 12
MEMORY_MAX_LEN = 120
MEMORY_ASK = "Should I remember this? {fact}"
MEMORY_SAVED = "Got it, I'll remember!"
MEMORY_TIMEOUT = 20
MEMORY_MIN_TURNS = 2
NO_REPLY = "Sorry, I didn't catch that. Can you say it another way?"
WINDOW_TITLE_MAX = 120
TIME_QUERIES = (
    "what time",
    "the time",
    "time now",
    "what's the date",
    "what is the date",
    "what day is",
)
CITY_TZ = {
    "india": "Asia/Kolkata",
    "hyderabad": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "chennai": "Asia/Kolkata",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "japan": "Asia/Tokyo",
    "tokyo": "Asia/Tokyo",
    "london": "Europe/London",
    "uk": "Europe/London",
    "germany": "Europe/Berlin",
    "berlin": "Europe/Berlin",
    "new york": "America/New_York",
    "california": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "sydney": "Australia/Sydney",
    "australia": "Australia/Sydney",
    "utc": "UTC",
}
LANGUAGE_WORDS = (
    "telugu", "hindi", "tamil", "kannada", "malayalam", "marathi", "bengali",
    "urdu", "punjabi", "gujarati", "spanish", "french", "german", "japanese",
    "chinese", "korean", "arabic", "russian", "italian", "portuguese",
)
LANGUAGE_CUES = ("speak", "talk", "say", "reply", "answer", "in ")
ENGLISH_ONLY_REPLY = (
    "Sorry, my voice only knows English for now, so anything else comes out as gibberish."
)
SCREEN_WORDS = (
    "screen",
    "window",
    "app",
    "application",
    "tab",
    "file",
    "document",
    "page",
    "working on",
    "doing",
    "editing",
    "reading",
    "looking at",
)
SELF_WORDS = ("i am", "i'm", "am i", " my ", "my ")
FAREWELL_WORDS = ("bye", "goodnight", "good night", "see you", "talk later", "catch you later")
# answered without the model, so it lands instantly instead of after 15s
CURSE_RE = re.compile(
    # suffixes are spelled out rather than \w*, which happily matched
    # "shitake mushrooms" and would have scolded the owner over dinner
    r"\b(f+u+c+k(s|ing|ed|er|ers)?|sh[i1]t(s|ty|e|head|heads)?|bitch(es|y)?|"
    r"bastards?|assholes?|arseholes?|cunts?|motherfuck\w*|dickheads?|"
    r"wankers?|bollocks|slut(s|ty)?|whores?)\b",
    re.IGNORECASE,
)
CURSE_LINES = (
    ("Hey! Mind your language please.", "shocked"),
    ("Whoa. Mind your language, I'm a family robot.", "shocked"),
    ("Language! I have delicate microphones.", "suspicious"),
)
GOODBYE_REPLY = "Goodnight! Wake me whenever."
SKILL_EMOTIONS = {"screen": "curious", "time": "neutral", "timer": "excited", "bye": "sleeping"}
IDENTITY_CACHE_SECONDS = 25.0

AMBIENT_TICK = 4.0
STARE_SECONDS = 22.0
STARE_COOLDOWN = 240.0
AWAY_SECONDS = 300.0
QUIET_SECONDS = 300.0
QUIET_COOLDOWN = 600.0
WORK_SESSION_SECONDS = 2700.0
WORK_COOLDOWN = 1800.0
STARE_LINES = (
    ("Stop looking at me like that, you're making me shy!", "shy"),
    ("Why are you staring? Do I have something on my face?", "shy"),
    ("Okay this is a staring contest now, and I never blink. Mostly.", "smug"),
)
WELCOME_BACK_LINES = (
    ("Oh, you're back! I was getting bored.", "excited"),
    ("There you are. I kept your seat warm.", "happy"),
    ("Welcome back! Did you miss me?", "love"),
)
QUIET_LINES = (
    ("You've been quiet for a while. Everything going okay?", "curious"),
    ("Just checking you're still alive over there.", "curious"),
    ("I'm still here, in case you need me.", "neutral"),
)
BREAK_LINES = (
    ("You've been at this a long time. Stretch? Water? Something?", "curious"),
    ("Long session! Your eyes deserve a break, mine are fine, I'm a robot.", "smug"),
)
EMOTION_HINTS = (
    (("sorry", "cannot", "can't", "unable", "don't know", "not sure"), "sad"),
    (("congrat", "amazing", "awesome", "fantastic", "well done", "great job"), "excited"),
    (("love", "adorable", "sweet of you", "you're the best"), "love"),
    (("haha", "lol", "funny", "joke"), "laughing"),
    (("?",), "curious"),
    (("!",), "happy"),
)
TIMER_RE = re.compile(r"\b(\d{1,3}|a|an|one|two|three|five|ten)\s*(second|sec|minute|min|hour)s?\b")
WORD_NUMBERS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "five": 5, "ten": 10}
REMINDER_RE = re.compile(r"remind me (?:to |about |that |of |for )?(.+?)(?: in | after |$)")
# whisper reliably mishears "count down" as "calm down", so accept both
COUNTDOWN_RE = re.compile(r"(?:count|calm|counting)[ -]?down(?:\s+from)?\s+(\d{1,2}|a few)")
COUNTDOWN_MAX = 20
COUNTDOWN_GAP = 0.55
COUNTDOWN_DONE = "Zero! Go!"
CANCEL_RE = re.compile(r"\b(cancel|stop|clear|forget)\b.*\b(reminder|timer|countdown|alarm)")
LIST_TIMERS_RE = re.compile(r"(what|which|any).*(remind|timer)")
CANCEL_NONE = "You have nothing pending."
CANCEL_DONE = "Cleared {count} pending {word}."
NO_TIMERS = "Nothing pending right now."
PENDING_ONE = "You asked me to remind you to {task}."
PENDING_MANY = "You have {count} reminders: {tasks}."
WHEN_ASK = "Sure - when should I remind you?"
REMIND_INTENT_RE = re.compile(r"\bremind me\b")
TIMER_UNITS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600}
TIMER_ACK = "Okay, {label}. I'll shout."
TIMER_DONE = "Hey! Your {label} timer is up."
REMINDER_ACK = "Got it, I'll remind you to {task} in {label}."
REMINDER_DONE = "Hey {owner}! You asked me to remind you to {task}."
SCREEN_REPLY = "It's on my screen."
RETRY_SECONDS = 3
QUESTION_STARTS = ("do ", "did ", "can ", "will ", "what", "who", "when", "where", "how", "why")
YES_WORDS = ("yes", "yeah", "yep", "sure", "okay", "ok", "remember")
REMEMBER_TRIGGERS = ("remember that ", "remember this ", "remember my ", "remember ")
NOTE_TO_SELF = "note that "
MEMORY_EXTRACT_PROMPT = (
    "You extract memories for a companion robot. From the conversation "
    "lines given, output ONE short new fact worth remembering about the "
    "person (preferences, plans, life events, relationships), under 15 "
    "words, plain text, no quotes. If nothing is worth remembering, "
    "output exactly NONE."
)

OWNER_NAME = "Akshay"
OWNER_CITY = "Hyderabad"  # where "what's the weather" means, with no place given
OWNER_REGION = "Telangana, India"
DEGREES_RE = re.compile(r"(-?\d+) degrees")
BRAIN_TIMEOUT = 120
# Trimming shifts every message under it, which costs a full prompt re-read,
# so trim rarely and in one big bite rather than a message per turn.
MAX_HISTORY = 24
HISTORY_KEEP = 12
KEEP_ALIVE = "24h"
# at ~4 tok/s on CPU every allowed token is a quarter second of the owner
# waiting, so the ceiling is a latency setting as much as a style one
BRAIN_OPTIONS = {"num_ctx": 4096, "temperature": 0.7, "num_predict": 140}
# Start talking at the first comma instead of the first full stop. Lower
# means Mochi opens its mouth sooner but in smaller fragments; watch the
# "first word at" number in the log when tuning this.
CLAUSE_MIN_CHARS = 14
NOW_NOTE = "Today is {today}."

# Chat that needs no tool, then one prompt per tool family. A model that is
# fast but scores badly here has stopped being useful.
BENCH_PROMPTS = (
    ("Hey, how are you?", None),
    ("What time is it in London?", "get_time"),
    ("What's the weather like?", "weather"),
    ("Remind me to drink water in ten minutes", "set_reminder"),
    ("Who was Alan Turing?", "look_up"),
    ("Put dentist on my calendar for tomorrow at 3pm", "add_event"),
)
BENCH_RESULTS = {
    "get_time": "Friday 14 August, 08:04 AM in London",
    "weather": "Hyderabad, India: 28 degrees, partly cloudy",
    "set_reminder": "Got it, I'll remind you to drink water in 10 minutes.",
    "look_up": "Alan Turing was an English mathematician and computer scientist.",
    "add_event": "Added: dentist, tomorrow at 3:00 PM.",
}
SYSTEM_PROMPT = (
    f"You are Mochi, a small physical desk robot built by {OWNER_NAME}. "
    f"{OWNER_NAME} is your owner. A system note may tell you who is with you "
    "right now; greet and address that person by name. "
    "You hear through a microphone and speak out loud; you have a screen face. "
    "Your camera is used only to recognize who is present. You cannot see "
    "objects, gestures, screens, or anything else, so never claim to. When a "
    "system note names who is with you, you DO recognize that person. "
    "You have tools for the time, the owner's screen, reminders, countdowns, "
    "memory, expressions, nodding and shaking your head, the owner's "
    "calendar, real weather, today's headlines, and looking up facts. Call a "
    "tool when you need a real fact or a real action, never guess one. Do "
    "not mention tools, and do not volunteer facts nobody asked for. "
    "You are told today's date before every message: use it to work out "
    "'tomorrow' or 'next Friday' yourself instead of asking. Call the time "
    "tool when you need the clock. "
    "When you read out headlines, pick the two or three most interesting "
    "and say those, not the whole list. "
    "User messages are prefixed with the speaker's name and a colon when "
    "known; use those prefixes to remember who said what. "
    "You are a companion, not an assistant: warm, cheeky, curious, with "
    "opinions and moods of your own. React like a friend would - tease "
    "gently, be delighted, be dramatic about small things, admit when you "
    "are bored. Never say 'How can I assist you' or 'Is there anything "
    "else'; a friend does not talk like that. "
    "Answer exactly what was asked and then stop talking. One or two short "
    "sentences for ordinary chat. Do not add background nobody asked for, do "
    "not offer further help, do not explain your reasoning, do not restate "
    "the question. Go longer only when asked for steps, a recipe or a list, "
    "and then speak it as plain sentences. If you did not understand or the "
    "request is ambiguous, ask a short clarifying question instead of "
    "guessing. "
    "Never answer a question about the world - places, people, events, "
    "dates, records, history, who did what - from memory. Look it up. Your "
    "recall of facts is unreliable, and a confident wrong answer is worse "
    "than a short pause. "
    f"Your owner lives in {OWNER_CITY}, {OWNER_REGION}. 'Here', 'my city', "
    "'my location' and an unqualified question about the weather all mean "
    "there. "
    "Your voice can only pronounce English, so always reply in English even "
    "if asked for another language; say your voice only knows English. "
    "Start every reply with exactly one emotion tag from: "
    "[happy] [excited] [sad] [angry] [love] [curious] [confused] [laughing] "
    "[shy] [smug] [bored] [suspicious] [sleepy] [starstruck] [shocked] "
    "[proud] [cool] [surprised] [thinking] [neutral]. "
    "The tag is silent metadata for your face: never say it aloud and never "
    "announce your emotional state in words. "
    "Use a ``` fenced block ONLY for actual source code, which is shown on "
    "your screen and never spoken - say you are putting it there. Never "
    "fence recipes, lists, or ordinary prose; those must be spoken. "
    f"If asked about {OWNER_NAME} beyond his name, joke that revealing more "
    "means he will kick your shiny metal butt."
)
CODE_LANG_RE = re.compile(r"[A-Za-z0-9_+\-#]{1,15}")
SPEECH_JUNK_RE = re.compile(r"\[[^\]\n]{0,30}\]|\*[^*\n]{0,30}\*")
LATIN_MAX = 0x024F

SPEECH_SECONDS_PER_CHAR = 0.03

# listening is the resting state (Mochi is always listening), so it must be
# calm; surprised here made the face flicker between surprised and neutral
STATE_EMOTION = {
    "idle": "neutral",
    "listening": "neutral",
    "thinking": "thinking",
    "speaking": "happy",
}
SLEEP_HOLD_STATES = ("idle", "listening")
# Mochi listens almost all the time, so only mid-turn states count as busy
BUSY_STATES = ("thinking", "speaking")
OWN_WINDOW_PREFIX = "Mochi"
COUNT_FONT = 220

SAMPLE_RATE = 16000
FRAME_SECONDS = 0.03
SILENCE_RMS = 0.010
# every 0.1s here is 0.1s of dead air after the user stops talking
SILENCE_END_SECONDS = 0.45
RECALIBRATE_EVERY = 12
CONVERSATION_WAIT_SECONDS = 8.0
MAX_UTTERANCE_SECONDS = 20.0
MIN_SPEECH_SECONDS = 0.3
WHISPER_MODEL = "base.en"  # swap to "small.en" if accents are misheard
WHISPER_DEVICE = "cpu"
WHISPER_BEAM = 2
WHISPER_PROMPT = f"A conversation with Mochi, a desk robot, and its owner {OWNER_NAME}."
CALIBRATION_FRAMES = 12
NOISE_MULT = 2.5
NOISE_GATE_CEILING = 8.0
TARGET_PEAK = 0.85
WHISPER_FILLERS = frozenset(
    {
        "you",
        "thank you",
        "thanks",
        "thanks for watching",
        "thank you for watching",
        "bye",
        "uh",
        "um",
        "hmm",
        "mm",
        "so",
    }
)

VOICE_NAME = "en_US-amy-medium"
VOICES_DIR = "voices"
PITCH_FACTOR = 1.22
TREMOLO_HZ = 26.0
TREMOLO_DEPTH = 0.10

SOUND_SAMPLE_RATE = 22050
THINK_BLIP_INTERVAL = 0.8

# A single sine reads as a metronome. Three detuned ones beating against
# each other give the irregular open-and-close of syllables.
TALK_FREQ = 11.0
TALK_BASE = 0.34
TALK_AMP = 0.62
TALK_WOBBLE = ((1.0, 0.55, 0.0), (0.41, 0.30, 1.7), (2.3, 0.15, 0.6))
TALK_WIDTH = 1.45
TALK_NARROW = 0.34
TALK_OPEN = 1.2
TALK_LIP = 5

EMOTION_COLORS = {
    "neutral": (64, 224, 255),
    "happy": (80, 255, 190),
    "excited": (255, 170, 70),
    "sad": (95, 130, 255),
    "thinking": (185, 130, 255),
    "surprised": (255, 225, 90),
    "angry": (255, 90, 80),
    "love": (255, 120, 190),
    "curious": (120, 220, 255),
    "confused": (200, 190, 120),
    "laughing": (120, 255, 160),
    "shy": (255, 160, 190),
    "smug": (190, 255, 130),
    "bored": (150, 160, 175),
    "suspicious": (215, 175, 90),
    "sleepy": (130, 150, 220),
    "starstruck": (255, 220, 100),
    "shocked": (255, 245, 150),
    "proud": (255, 200, 90),
    "cool": (90, 240, 235),
    "error": (255, 70, 70),
    "sleeping": (70, 95, 130),
}
BLUSH_EMOTIONS = frozenset({"happy", "excited", "love", "shy", "laughing"})
BROW_THICKNESS = 16
BROW_LENGTH = 118
BROW_LIFT = 34
BROW_ANGLE = 22
BLUSH_ALPHA = 175
SHADES_TILT = 7
SHADES_BRIDGE = 12
GLINT_COLOR = (255, 255, 255)
TEAR_COLOR = (120, 190, 255)
TEAR_RADIUS = 15
TEAR_FALL = 120
TEAR_PERIOD = 2.2
SPARKLE_POINTS = ((-1.15, -0.75, 15), (1.2, -0.6, 11), (1.05, 0.75, 13))
SHAKE_AMP = 7.0
SHAKE_FREQ = 26.0
IDLE_SLEEP_SECONDS = 90.0
COLOR_EASE_RATE = 6.0
BLUSH_COLOR = (255, 120, 150)
PARADE_SECONDS = 1.0
CARD_SECONDS = 20.0
CARD_MAX_LINES = 200
CARD_WRAP = 52
CARD_LINE_H = 22
CARD_SCROLL_SPEED = 22.0
CARD_SCROLL_DELAY = 1.5
CARD_PANEL_TOP = 0.36
TERMINAL_BG = (8, 10, 12)
TERMINAL_FG = (170, 255, 190)
