"""Speech-to-text via faster-whisper."""

from __future__ import annotations

from mochi.constants import WHISPER_MODEL
from mochi.voice.audio import Recorder


class WhisperTranscriber:
    def __init__(self, recorder: Recorder | None = None) -> None:
        from faster_whisper import WhisperModel

        self.model = WhisperModel(WHISPER_MODEL, compute_type="int8")
        self.recorder = recorder or Recorder()

    def listen(self) -> str:
        audio = self.recorder.record_utterance()
        if audio is None:
            return ""
        segments, info = self.model.transcribe(audio, beam_size=1, language="en")
        return " ".join(seg.text.strip() for seg in segments).strip()
