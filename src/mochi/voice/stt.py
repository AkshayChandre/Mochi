from __future__ import annotations

from mochi.constants import (
    WHISPER_BEAM,
    WHISPER_DEVICE,
    WHISPER_FILLERS,
    WHISPER_MODEL,
    WHISPER_PROMPT,
)
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
            audio,
            beam_size=WHISPER_BEAM,
            language="en",
            # the recorder already gated on silence; running VAD a second
            # time cost time and clipped quiet word endings
            vad_filter=False,
            condition_on_previous_text=False,
            initial_prompt=WHISPER_PROMPT,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return "" if is_noise(text) else text
