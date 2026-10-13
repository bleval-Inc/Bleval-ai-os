"""Voice profiles configuration for each executive."""

from __future__ import annotations

from typing import Any, Dict, Optional

from axiom.voice.tts.provider_base import VoiceProfile
from axiom.voice.config import voice_config


# Executive voice profiles - maps executive_id to VoiceProfile
EXECUTIVE_VOICE_PROFILES: Dict[str, VoiceProfile] = {
    "axiom": VoiceProfile(
        provider="piper",
        model="en_GB-alan-medium",  # British female - "secret agent" tone
        speaker_id=0,
        length_scale=1.0,
        noise_scale=0.667,
        noise_w=0.8,
        extra={
            "description": "Female, British, secret agent - poised, precise, dry wit",
        },
    ),
    "jenson": VoiceProfile(
        provider="piper",
        model="en_US-ryan-high",  # Male authoritative
        speaker_id=0,
        length_scale=1.0,
        noise_scale=0.667,
        noise_w=0.8,
        extra={
            "description": "Male, mature, commanding, strong leader tone",
        },
    ),
    "yamako": VoiceProfile(
        provider="piper",
        model="en_US-lessac-high",  # Lighter/brighter female
        speaker_id=0,
        length_scale=1.1,  # Slightly faster for playful energy
        noise_scale=0.667,
        noise_w=0.8,
        extra={
            "description": "Female, flirty, fun, quirky, playful energy",
        },
    ),
    "valta_prime": VoiceProfile(
        provider="piper",
        model="en_US-ryan-low",  # Stern, serious male
        speaker_id=0,
        length_scale=0.9,  # Slower for gravitas
        noise_scale=0.667,
        noise_w=0.8,
        extra={
            "description": "Male, mature, stern, serious, no-nonsense",
        },
    ),
}


def get_voice_profile(executive_id: str) -> Optional[VoiceProfile]:
    """Get the voice profile for an executive."""
    return EXECUTIVE_VOICE_PROFILES.get(executive_id.lower())


def get_elevenlabs_voice_profile(executive_id: str) -> Optional[VoiceProfile]:
    """Get the ElevenLabs voice profile for an executive (if configured)."""
    voice_ids = voice_config.tts.elevenlabs_voice_ids
    exec_id = executive_id.lower()
    
    if not voice_ids.get(exec_id):
        return None
    
    # Base profiles for ElevenLabs (would need actual voice IDs)
    base_profiles = {
        "axiom": {
            "voice_id": voice_ids.get("axiom", ""),
            "model_id": "eleven_monolingual_v1",
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,  # Some expressiveness for dry wit
            "use_speaker_boost": True,
        },
        "jenson": {
            "voice_id": voice_ids.get("jenson", ""),
            "model_id": "eleven_monolingual_v1",
            "stability": 0.6,
            "similarity_boost": 0.8,
            "style": 0.1,  # More consistent/commanding
            "use_speaker_boost": True,
        },
        "yamako": {
            "voice_id": voice_ids.get("yamako", ""),
            "model_id": "eleven_monolingual_v1",
            "stability": 0.4,
            "similarity_boost": 0.7,
            "style": 0.6,  # More expressive/playful
            "use_speaker_boost": True,
        },
        "valta_prime": {
            "voice_id": voice_ids.get("valta_prime", ""),
            "model_id": "eleven_monolingual_v1",
            "stability": 0.8,
            "similarity_boost": 0.9,
            "style": 0.0,  # Flat/stern
            "use_speaker_boost": True,
        },
    }
    
    if exec_id not in base_profiles:
        return None
    
    profile_data = base_profiles[exec_id]
    if not profile_data["voice_id"]:
        return None
    
    return VoiceProfile(
        provider="elevenlabs",
        model=exec_id,
        extra=profile_data,
    )


def get_best_voice_profile(executive_id: str) -> VoiceProfile:
    """
    Get the best available voice profile for an executive.
    
    Prefers ElevenLabs if configured and available, falls back to Piper.
    """
    # Try ElevenLabs first
    elevenlabs_profile = get_elevenlabs_voice_profile(executive_id)
    if elevenlabs_profile:
        from axiom.voice.tts.elevenlabs_provider import ElevenLabsTTS
        from axiom.voice.tts.provider_base import tts_registry
        
        provider = tts_registry.get("elevenlabs")
        if provider and isinstance(provider, ElevenLabsTTS) and provider.is_available():
            return elevenlabs_profile
    
    # Fall back to Piper
    return get_voice_profile(executive_id) or EXECUTIVE_VOICE_PROFILES["axiom"]


# Wake word greetings per executive
EXECUTIVE_GREETINGS: Dict[str, str] = {
    "axiom": "Axiom online. How can I help?",
    "jenson": "Jenson here. Operations standing by.",
    "valta_prime": "Valta Prime active. Markets monitored.",
    "yamako": "Yamako ready. Personal ops at your service.",
}