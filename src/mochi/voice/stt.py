from __future__ import annotations

from mochi.constants import WHISPER_DEVICE, WHISPER_FILLERS, WHISPER_MODEL
from mochi.voice.audio import Recorder


def is_noise(text: str) -> bool:
    stripped = "".join(c for c in text.lower() if c.isalnum() or c.isspace()).strip()
    return not stripped or stripped in WHISPER_FILLERS


class WhisperTranscriber:
    def __init__(self, recorder: Recorder | None = None) -> None:
        from faster_whisper import WhisperModel

        self.model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8")
        self.recorder = recorder or Recorder()

    def listen(self) -> str:
        audio = self.recorder.record_utterance()
        if audio is None:
            return ""
        segments, _ = self.model.transcribe(
            audio, beam_size=1, language="en", vad_filter=True
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return "" if is_noise(text) else text
