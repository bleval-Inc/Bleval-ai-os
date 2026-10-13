"""Axiom OS Text-to-Speech package."""

from axiom.voice.tts.provider_base import (
    TTSProvider,
    VoiceProfile,
    TTSProviderRegistry,
    tts_registry,
)
from axiom.voice.tts.piper_provider import PiperTTS
from axiom.voice.tts.elevenlabs_provider import ElevenLabsTTS
from axiom.voice.tts.voice_profiles import (
    EXECUTIVE_VOICE_PROFILES,
    EXECUTIVE_GREETINGS,
    get_voice_profile,
    get_elevenlabs_voice_profile,
    get_best_voice_profile,
)
from axiom.voice.tts.service import TextToSpeechService, get_tts_service

__all__ = [
    "TTSProvider",
    "VoiceProfile",
    "TTSProviderRegistry",
    "tts_registry",
    "PiperTTS",
    "ElevenLabsTTS",
    "EXECUTIVE_VOICE_PROFILES",
    "EXECUTIVE_GREETINGS",
    "get_voice_profile",
    "get_elevenlabs_voice_profile",
    "get_best_voice_profile",
    "TextToSpeechService",
    "get_tts_service",
]