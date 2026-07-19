# Mochi — Open-Source Desktop AI Companion

A soft, blob-shaped robot that gives physical presence to a fully local,
fully open-source AI. The robot body (Raspberry Pi) is the presence layer;
your PC is the brain. Zero paid services, zero cloud dependency.

## v0.1 — Face Engine (this repo, today)

Runs on your PC now; the same file runs on the Pi's 720x720 round display later.

### Run it

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
mochi                     # face + voice together (needs Ollama running)
mochi-face                # face only
mochi-voice               # terminal chat only
```

### Repo layout

```
src/mochi/     the package — face/ now; voice/ brain/ body/ agent/ as they land
tests/         headless test suite (pytest)
hardware/      BOM, wiring, CAD/STL files
```

Development standards: see [CONTRIBUTING.md](CONTRIBUTING.md).

### Controls

| Key | Action |
|-----|--------|
| 1–7 | neutral / happy / sad / thinking / surprised / excited / sleeping |
| M   | mouse-follow gaze — Mochi's eyes track your cursor |
| A   | autopilot demo (cycles emotions) |
| ESC | quit |

Press **M** and move your mouse around — that's the presence effect the whole
project is built on.

### Enable audio (talking Mochi)

```powershell
pip install -e .[audio]
python -m piper.download_voices en_US-amy-medium --data-dir voices
mochi
```

Mochi boots with a chirp and starts listening immediately — just talk.
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
