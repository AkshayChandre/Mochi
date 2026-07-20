# Changelog

All notable changes to Mochi are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Printable shell v1 (`hardware/cad`): parametric OpenSCAD, NOVA-style —
  head, body, neck, base, ears, arms, tread pods, glowing heart inlay,
  with screw bosses throughout. Electronics dims are placeholders until
  parts are measured.
- Real audio I/O: microphone capture with VAD (`mochi.voice.audio`),
  faster-whisper STT, Piper TTS with kid-robot pitch and tremolo.
- Procedural robot sounds: boot chirp, listening blip, thinking beeps —
  synthesized, no audio assets.
- Conversation-driven emotions: the brain tags each reply with an emotion
  that drives the face while speaking; talking mouth animation.
- `mochi` now starts listening immediately on launch; console fallback when
  audio dependencies are missing.

### Fixed
- Whisper pinned to CPU by default: faster-whisper auto-selected CUDA on
  NVIDIA machines and crashed without the CUDA 12 runtime. Set
  `WHISPER_DEVICE = "cuda"` in constants after installing
  `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` to opt back in.
- Conversations are now multi-turn: after replying, Mochi keeps listening
  for follow-ups; silence (empty input) ends the conversation instead of
  requiring a re-wake every turn.

### Added
- App shell (`mochi` command): face window and voice pipeline in one
  process — pipeline states drive facial emotions live.
- `.gitattributes` enforcing LF line endings to stop CRLF diff churn.
- Voice pipeline (`mochi.voice`): wake -> listen -> think -> speak state
  machine with pluggable components and face-emotion mapping.
- Brain client (`mochi.brain`): Ollama chat with rolling history and offline
  rollback. Console demo entry point: `mochi-voice`.
- Enterprise project scaffolding: src-layout package, test suite, ruff lint
  config, contribution standards.

## [0.1.0] - 2026-07-18

### Added
- Face engine (`mochi.face`): 7 procedural emotions, time-based easing,
  blink cycles with double-blink, idle gaze wander, mouse-follow gaze,
  velocity-driven squash-and-stretch. Renders 720x720 for the round DSI
  display; runs on PC and Pi unchanged.
