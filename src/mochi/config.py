"""Repo-level connections loaded from config.yaml (endpoints only, never secrets)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Connections:
    brain_host: str = "127.0.0.1"
    brain_port: int = 11434
    llm_model: str = "qwen2.5:7b"


def load(path: str | None = None) -> Connections:
    file = Path(path or os.environ.get("MOCHI_CONFIG", "config.yaml"))
    if not file.is_file():
        return Connections()
    raw = yaml.safe_load(file.read_text()) or {}
    brain = raw.get("brain", {})
    base = Connections()
    return Connections(
        brain_host=brain.get("host", base.brain_host),
        brain_port=brain.get("port", base.brain_port),
        llm_model=brain.get("model", base.llm_model),
    )


CONNECTIONS = load()
