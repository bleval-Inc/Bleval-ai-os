"""Axiom OS voice processing package.

Full backend-driven voice pipeline: wake word detection (openWakeWord),
speech-to-text (faster-whisper), intent routing, TTS (Piper/ElevenLabs),
and WebSocket relay to frontend.
"""

from .config import voice_config
EXECUTIVE_WAKE_WORDS = voice_config.executive_wake_words
VALID_EXECUTIVES = voice_config.valid_executives
from .stt import (
    SpeechToTextError,
    detect_wake_word,
    extract_command_after_wake,
    is_available,
    transcribe_wav,
)
from .pipeline_orchestrator import (
    VoicePipelineOrchestrator,
    VoiceEvent,
    get_pipeline,
    initialize_pipeline,
)
from .tts.service import tts_service, TextToSpeechService
from .tts.voice_profiles import (
    EXECUTIVE_VOICE_PROFILES,
    EXECUTIVE_GREETINGS,
    get_voice_profile,
    get_best_voice_profile,
)

__all__ = [
    # Config
    "voice_config",
    "EXECUTIVE_WAKE_WORDS",
    "VALID_EXECUTIVES",
    # STT
    "SpeechToTextError",
    "detect_wake_word",
    "extract_command_after_wake",
    "is_available",
    "transcribe_wav",
    # Pipeline
    "VoicePipelineOrchestrator",
    "VoiceEvent",
    "get_pipeline",
    "initialize_pipeline",
    # TTS
    "tts_service",
    "TextToSpeechService",
    "EXECUTIVE_VOICE_PROFILES",
    "EXECUTIVE_GREETINGS",
    "get_voice_profile",
    "get_best_voice_profile",
]