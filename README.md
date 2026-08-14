# Mochi: Open-Source Desktop AI Companion

A robot that gives physical presence to a fully local,
fully open-source AI. The robot body is the presence layer;
PC is the brain. Zero paid services, zero cloud dependency.

## v0.1: Face Engine

Runs on your PC now; the same file runs on the Pi's 720x720 round display later.

### Run it

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
mochi                     # face + voice together (needs Ollama running)
mochi-face                # face only
mochi-voice               # terminal chat only
mochi-vision watch        # face recognition (needs .[vision] extra, see below)
```

### Repo layout

```
src/mochi/     the package - face/ now; voice/ brain/ body/ agent/ as they land
tests/         headless test suite (pytest)
hardware/      BOM, wiring, CAD/STL files
```

### What Mochi can do

The model decides when to act; there is no keyword matching anywhere.
Ask in whatever words you like.

| | |
|---|---|
| Time and date | any city or country |
| Your screen | which app and file you're looking at |
| Reminders | "remind me to stretch in 20 minutes", plus list and cancel |
| Countdowns | counted out loud, on the face |
| Calendar | add, list and cancel events - local, offline, no account |
| Weather | anywhere, live (Open-Meteo) |
| News | today's headlines (RSS feeds you choose in `constants.py`) |
| Lookups | real facts from Wikipedia rather than guesses |
| Memory | remembers you, per person, with your spoken permission |
| Face | 22 emotions, nods, shakes its head, shows code and banners |

Adding a capability is a tool spec plus a method - see `src/mochi/tools.py`.

Development standards: see [CONTRIBUTING.md](CONTRIBUTING.md).

### Controls

| Key | Action |
|-----|--------|
| 1-7 | neutral / happy / sad / thinking / surprised / excited / sleeping |
| M   | mouse-follow gaze - Mochi's eyes track your cursor |
| A   | autopilot demo (cycles emotions) |
| ESC | quit |

Press **M** and move your mouse around - that's the presence effect the whole
project is built on.

### Brain speed

Mochi prints what the model is actually doing on every reply:

```
first word at 3.2s | reply took 9.1s | read 2000 tok in 2.5s | wrote 28 tok in 7.0s (4.0 tok/s)
```

- **first word** is the silence you actually sit through.
- **read** should stay cheap after the first turn. If it costs seconds
  every turn, the prompt cache is being thrown away.
- **tok/s** is the floor. Nothing in this repo can move it.

Under ~10 tok/s the robot feels like a form, not a friend. `ollama ps`
shows where the model landed; the PROCESSOR column is the split. Ollama
falls back to CPU silently, and a model only goes fast if the **whole**
thing fits in free VRAM, weights plus context:

| Model | Needs free VRAM | Notes |
|---|---|---|
| `qwen2.5:7b` | ~5.5 GB | best tool calling, the default |
| `qwen2.5:3b` | ~2.5 GB | still calls tools reliably, much faster |
| `qwen2.5:1.5b` | ~1.5 GB | fast, but tool calling gets unreliable |

Partial offload is the worst case: it pays the transfer cost and gets
none of the speed. Prefer a smaller model that fits entirely over a
bigger one that half fits.

Don't take the table's word for it - measure on your own machine:

```powershell
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
mochi-bench qwen2.5:7b qwen2.5:3b qwen2.5:1.5b
```

```
model                   first word    tok/s   tokens/reply   tools
qwen2.5:1.5b                  0.7s     28.0             30     4/6
qwen2.5:3b                    1.6s      9.5             32     6/6
qwen2.5:7b                    3.4s      4.0             45     6/6
```

The **tools** column is the one that decides it. Every capability Mochi
has arrives through a tool call, so a model that scores 4/6 has stopped
being Mochi no matter how fast it is. Take the quickest model that still
scores full marks, and set it in `config.yaml`:

```yaml
brain:
  model: qwen2.5:3b
```

### Enable audio (talking Mochi)

```powershell
pip install -e .[audio]
python -m piper.download_voices en_US-amy-medium --data-dir voices
mochi
```

### Face recognition (any webcam)

```powershell
pip install -e .[vision]        # one-time; downloads the InsightFace model on first run
mochi-vision enroll "Akshay"    # look at the camera for 5 captures
mochi-vision watch              # live: prints who it sees + confidence
mochi-vision list               # enrolled people
```

### Hearing you accurately

`WHISPER_MODEL` in `constants.py` drives accent accuracy: `base.en`
(default) is fastest; switch to `small.en` if Indian, British, or other
accents get misheard, `medium.en` if you have a GPU. The beam search,
context prompt, and noise handling apply to every model. The mic
auto-calibrates to room noise on every listen, so no
threshold tweaking is normally needed; `SILENCE_RMS` is the floor and
`NOISE_MULT` how far above the room it must be.

GPU (much faster with the bigger models):

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
# then set WHISPER_DEVICE = "cuda" in constants.py
```

### How Mochi decides things

The model drives. It is given tools - the clock, the owner's screen,
reminders, countdowns, memory, expressions, sleep - and calls them when
it needs a real fact or a real action. There is no keyword matching on
what you say, and nothing is force-fed into the prompt: Mochi looks
things up only when they matter, so it stops reciting the date and your
saved facts unprompted. Tools need a model that can call them; the
default is `qwen2.5:7b` (`ollama pull qwen2.5:7b`).

Senses live behind `mochi/context.py`. `LocalSensors` reads this
machine; when the brain moves to a server, a laptop agent implementing
the same two methods reports over the network and no other code changes.

### Desktop awareness

Mochi knows the time and which window is focused, so "what time is it",
"what am I working on", and "set a timer for 10 minutes" are answered
instantly and locally, without asking the LLM. Timers speak up on their
own when they finish. The same context is passed to the brain each turn,
so it can reason about your day without guessing.

### Living on its own

Mochi is not only reactive. A background loop watches the room and speaks
first: it gets shy if you stare too long, welcomes you back after you have
been away, checks in when the room has been quiet, and suggests a break
after a marathon session. Every trigger has a cooldown, and Mochi stays
silent while a conversation is running. Timings live in `constants.py`
(`STARE_SECONDS`, `QUIET_SECONDS`, `WORK_SESSION_SECONDS`).

Reminders and countdowns are real: "remind me to drink water in a min"
announces the task itself when it fires, and "count down from 10" is
spoken one number per second, not all at once.

### Memory

After a conversation ends, Mochi may ask "Should I remember this?" -
say yes and the fact is stored per person in `mochi.db`, recalled in
every future conversation, and survives restarts. Decline and nothing
is saved; Mochi never remembers without permission.

`watch` auto-enrolls: when an unknown face stays in frame for a few
captures, it asks "new face! what's their name?" - type a name to save
them, Enter to ignore. Embeddings live in `mochi.db` (SQLite, local
only, gitignored). Tuning knobs in `constants.py`: `CAMERA_INDEX` if
the wrong camera opens, `FACE_MATCH_THRESHOLD` if lighting causes
misses or false matches.

Mochi boots with a chirp and starts listening immediately - just talk.
Silence ends a conversation; speaking starts a new one. If audio setup is
missing, `mochi` falls back to console mode automatically.

## Zero-cost open-source stack

| Layer | Tool | License |
|-------|------|---------|
| Wake word | openWakeWord | Apache-2.0 |
| Speech-to-text | whisper.cpp | MIT |
| LLM server | Ollama + Qwen2.5 / Llama 3 | MIT / open weights |
| Text-to-speech | Piper | MIT |
| Vision / face ID | OpenCV + InsightFace (buffalo_s) | Apache-2.0 / MIT |
| Speaker ID | SpeechBrain ECAPA-TDNN | Apache-2.0 |
| Memory | SQLite + sqlite-vec | MIT |
| Face/animation | pygame | LGPL |
| Remote access | WireGuard | GPL-2.0 |

## Architecture

```
Mochi body (Pi 5)                    Brain (your PC, LAN or WireGuard)
  face_engine  <──────────┐            Ollama (LLM)
  openWakeWord            ├─ WiFi ──   whisper.cpp (STT)
  speaker-ID gate         │            Piper (TTS)
  servos / camera / AEC ──┘            memory + embeddings
                                       desktop agent (screen context)
```

Offline fallback: a small quantized model on the Pi keeps Mochi alive
(face, wake, basic replies) when the brain is unreachable.

## Roadmap

- **v0.1** face engine on PC → voice loop (wake → STT → LLM → TTS) → move to Pi
- **v0.5** owner-only wake (voice ID + face ID), guest mode, head pan/tilt, arms, memory w/ user approval
- **v1.0** desktop agent (screen/IDE/calendar context), rotating base
- **v2.0** wheels + battery + dock + cliff sensors

License: MIT (proposed).
