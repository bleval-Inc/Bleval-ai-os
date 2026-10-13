"""Speech-to-text using faster-whisper."""

from .whisper_engine import WhisperEngine
from ..stt_legacy import (
    SpeechToTextError,
    detect_wake_word,
    extract_command_after_wake,
    is_available,
    transcribe_wav,
)

__all__ = [
    "SpeechToTextError",
    "WhisperEngine",
    "detect_wake_word",
    "extract_command_after_wake",
    "is_available",
    "transcribe_wav",
]
