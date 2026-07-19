# Changelog

All notable changes to Mochi are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
