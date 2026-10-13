"""Axiom OS Speech-to-Text package."""

from axiom.voice.stt.whisper_engine import (
    WhisperEngine,
    MockWhisperEngine,
    create_whisper_engine,
)

# Also export from the original stt module for backward compatibility
from axiom.voice.stt_legacy import (
    EXECUTIVE_WAKE_WORDS,
    VALID_EXECUTIVES,
    SpeechToTextError,
    detect_wake_word,
    extract_command_after_wake,
    is_available,
    transcribe_wav,
)

__all__ = [
    "WhisperEngine",
    "MockWhisperEngine",
    "create_whisper_engine",
    "EXECUTIVE_WAKE_WORDS",
    "VALID_EXECUTIVES",
    "SpeechToTextError",
    "detect_wake_word",
    "extract_command_after_wake",
    "is_available",
    "transcribe_wav",
]