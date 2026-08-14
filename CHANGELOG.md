# Changelog

All notable changes to Mochi are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Calendar: Mochi keeps its own events in `mochi.db` (`add_event`,
  `list_events`, `cancel_event`). No account, no OAuth, works offline.
  The current date and time are handed to the model each turn, so it
  resolves "tomorrow at 3" itself.
- World knowledge, all keyless and free: real weather (Open-Meteo),
  today's headlines (RSS), and fact lookup (Wikipedia) so Mochi looks
  things up instead of inventing them. Every failure returns a spoken
  sentence, never an exception.
- Face: `nod` and `shake` gestures the model can call mid-sentence, and a
  banner line under the eyes for temperatures and event names - the face
  stays a face underneath it.

### Fixed
- The mouth moved while nothing was playing. It was driven by pipeline
  state, so it mimed through the several seconds between one spoken
  sentence and the next while the model was still writing. It now
  follows actual audio playback. The shape changed too: a single 13Hz
  sine read as a metronome, so it is now three detuned waves driving a
  jaw that narrows as it opens.
- Mochi greeted you again every time it briefly lost your face - turning
  your head, leaning back, or one bad frame all counted as leaving the
  room. A fresh greeting now needs a real absence.

### Changed
- Latency. The dominant cost was Ollama re-reading the entire prompt
  every turn instead of reusing its cached prefix. Three things were
  breaking the cache: the per-turn note sat below the conversation so
  every later turn shifted it, the note carried a clock that changed
  every minute, and the answering pass after a tool call dropped the
  tool schemas and so changed the system block. The note is now pinned
  at index 1, carries the date only (the clock is a tool call), and the
  schemas ride along on both passes. History trimming also moved to
  batches (24 -> 12) because trimming a message per turn shifts the
  whole prompt and costs the same full re-read.
- Audio path: the microphone stream is opened once for the process
  lifetime instead of reopened and re-calibrated (~0.5s) before every
  utterance; the mic buffer is drained after Mochi speaks so it stops
  transcribing its own voice; end-of-speech silence 0.7s -> 0.45s;
  Whisper's redundant second VAD pass dropped; context 8192 -> 4096.
  The first clause is spoken at the comma rather than the full stop.
- Every reply now prints time to first word alongside what the model
  actually read and wrote, in tokens and seconds, so latency claims can
  be checked instead of guessed at. Time to first word is the number
  that matches what the silence feels like.
- Replies were running 50-76 tokens, which at CPU speed is fifteen
  seconds of waiting for padding nobody asked for. The prompt now says
  answer and stop - no unrequested background, no offers of further
  help, no restating the question - and the output ceiling dropped from
  220 to 140 tokens.
- Mochi answered world questions from memory and got them wrong
  (Independence Day, most notably). It is now told plainly that its
  recall of facts is unreliable and to look things up, and it knows
  where its owner lives, so "here" and "my city" mean something.
- Startup primes Ollama's prompt cache in the background, so the first
  question no longer pays the ~20s cost of reading the tool schemas.

### Added
- `mochi-bench` runs the same six prompts against any set of models and
  reports time to first word, tokens per second, reply length and how
  many tools each model actually called. Model choice depends entirely
  on the machine, so it is the one question worth measuring rather than
  reasoning about.
- Swearing gets a "mind your language" straight from the guard, without
  waking the model, so it lands instantly instead of fifteen seconds
  later. Suffixes are spelled out rather than globbed, so ordering
  shitake mushrooms no longer earns a telling-off.

### Added
- Desktop awareness: active window and clock are injected into every
  brain turn, and local skills answer time, date, "what am I working on",
  and timers deterministically without the LLM. Timers announce
  themselves out loud.
- Face: 15 new emotions (angry, love, curious, confused, laughing, shy,
  smug, bored, suspicious, sleepy, starstruck, shocked, proud, cool,
  error) with heart, spiral, star, X and shades eye styles, brows,
  tears, sparkles and winks. The face sleeps after 90s idle.

### Added
- Persistent memory: after a conversation, Mochi extracts one worthwhile
  fact, asks aloud for permission, and stores it per person in mochi.db;
  saved memories are recalled into every future conversation and survive
  restarts. Nothing is ever stored without a spoken yes.

### Changed
- Streaming voice: LLM replies stream sentence-by-sentence into TTS, so
  Mochi starts speaking after the first sentence instead of the full
  reply. Ollama `keep_alive` pinned to 2h (no cold reloads); TTS
  synthesizes the next sentence while the previous one plays;
  end-of-speech silence window tightened 1.2s -> 0.9s.

### Added
- Printable shell v1 (`hardware/cad`): parametric OpenSCAD, NOVA-style -
  head, body, neck, base, ears, arms, tread pods, glowing heart inlay,
  with screw bosses throughout. Electronics dims are placeholders until
  parts are measured.
- Real audio I/O: microphone capture with VAD (`mochi.voice.audio`),
  faster-whisper STT, Piper TTS with kid-robot pitch and tremolo.
- Procedural robot sounds: boot chirp, listening blip, thinking beeps -
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
  process - pipeline states drive facial emotions live.
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
