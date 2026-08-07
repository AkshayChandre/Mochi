# Prompt: Mochi Companion Mobile App

Copy everything below into your AI app builder.

---

Build a mobile app called **Mochi Companion** - the phone-side remote for Mochi,
an open-source desktop robot (a physical device with an animated face, voice,
and a local LLM brain running on the owner's PC via Ollama).

## Purpose

The app connects to Mochi over the local network and lets the owner chat with
it by text, see its live state, manage what it remembers, and tune its
personality and settings. It is a companion remote, NOT a chatbot of its own -
all intelligence lives on the robot's brain server.

## Connectivity

- Configurable base URL (host + port) in Settings, default `http://192.168.1.x:8765`.
- REST + WebSocket. The robot's API is under development; build against this
  contract with a clean API layer and a **mock mode** (toggle in Settings) that
  fakes all responses so the UI is fully demoable without the robot:
  - `GET /status` → `{online, emotion, state, model, uptime_s}`
    (state is one of idle | listening | thinking | speaking)
  - `WS /events` → pushes `{type: "state"|"emotion"|"transcript"|"reply", data}`
  - `POST /chat {text}` → streams reply text (SSE or chunked)
  - `GET /memories` → `[{id, text, created_at, approved}]`
  - `POST /memories/{id}/approve`, `DELETE /memories/{id}`
  - `GET/PUT /personality` → `{humor, curiosity, energy, warmth, sarcasm}` 0-100
  - `GET/PUT /config` → `{model, voice, volume, wake_enabled}`
  - `POST /expression {name}` → makes the robot play an expression
    (happy, excited, sad, surprised, thinking, sleeping, neutral)

## Screens

1. **Home** - big live status: an animated pair of eyes mirroring Mochi's
   current emotion and state (reuse the emotion colors below), connection
   indicator, model name, quick expression-trigger buttons.
2. **Chat** - classic chat UI with streaming replies; code blocks in replies
   render in monospace cards.
3. **Memories** - list of things Mochi remembered; approve or delete each;
   pending items highlighted.
4. **Personality** - five sliders (humor, curiosity, energy, warmth, sarcasm)
   with a live preview sentence that restyles as sliders move.
5. **Settings** - host/port, mock mode, model picker, voice volume,
   theme.

## Design

- Dark theme, near-black `#0a0c10` background, rounded cards.
- Emotion accent colors: neutral `#40e0ff`, happy `#50ffbe`, excited `#ffaa46`,
  sad `#5f82ff`, thinking `#b982ff`, surprised `#ffe15a`, sleeping `#465f82`.
- Cute but clean - inspired by EMO/Vector robot companion apps. The eyes on
  the Home screen should blink occasionally and ease between colors.
- Handle offline gracefully everywhere: friendly "Mochi is sleeping -
  can't reach her" state with a retry.

## Tech

- Cross-platform (React Native/Expo or Flutter - your choice).
- Clean separation: `api/` client with interchangeable real/mock
  implementations, typed models, state management appropriate to the
  framework.
- No accounts, no cloud, no analytics. Everything talks only to the robot on
  the LAN.
  