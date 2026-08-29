"""Axiom OS voice processing package.

Speech-to-text (STT) and wake-word detection for the AI OS's own voice
pipeline. Voice audio is captured on the machine and transcribed locally,
removing the dependency on browser-native speech recognition.
"""

from axiom.voice.stt import (
    EXECUTIVE_WAKE_WORDS,
    VALID_EXECUTIVES,
    SpeechToTextError,
    detect_wake_word,
    extract_command_after_wake,
    is_available,
    transcribe_wav,
)

__all__ = [
    "EXECUTIVE_WAKE_WORDS",
    "VALID_EXECUTIVES",
    "SpeechToTextError",
    "detect_wake_word",
    "extract_command_after_wake",
    "is_available",
    "transcribe_wav",
]