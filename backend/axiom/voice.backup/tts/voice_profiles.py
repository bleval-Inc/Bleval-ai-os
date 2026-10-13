"""
Voice profiles for each entity.

Maps entities to their TTS voice configuration.
"""

from dataclasses import dataclass

from ..config import ENTITIES


@dataclass
class VoiceProfile:
    """Configuration for an entity's voice."""
    
    entity_name: str
    piper_voice_id: str  # Piper model identifier
    elevenlabs_voice_id: str  # ElevenLabs voice ID (optional)
    stability: float = 0.5  # For ElevenLabs: 0.0-1.0
    similarity_boost: float = 0.75  # For ElevenLabs: 0.0-1.0


# Piper voice identifiers (available models)
# List available: python -m piper.download --list-voices
VOICE_PROFILES = {
    "axiom": VoiceProfile(
        entity_name="axiom",
        # High-quality British English voice - "secret agent" persona
        piper_voice_id="en_GB-bnk-medium",  # Jenny (British)
        elevenlabs_voice_id="VR6AewLBeTwqdI0wgc4G",  # Grace (British, professional)
        stability=0.6,
        similarity_boost=0.85,
    ),
    "jenson": VoiceProfile(
        entity_name="jenson",
        # Male authoritative US voice - commanding COO
        piper_voice_id="en_US-ryan-high",  # Ryan (Male, US)
        elevenlabs_voice_id="pFZP5JQG7d50QdPLLp94",  # Adam (Male, commanding)
        stability=0.65,
        similarity_boost=0.80,
    ),
    "yamako": VoiceProfile(
        entity_name="yamako",
        # Female lighter pitch - flirty/quirky personal assistant
        piper_voice_id="en_US-kristin-medium",  # Kristin (Female, neutral)
        elevenlabs_voice_id="EXAVITQu4vr4xnSDxMaL",  # Elli (Female, bright)
        stability=0.5,
        similarity_boost=0.75,
    ),
    "valtaprime": VoiceProfile(
        entity_name="valtaprime",
        # Male stern/serious tone - no-nonsense trading COO
        piper_voice_id="en_US-hfc-medium",  # Henry (Male, US, professional)
        elevenlabs_voice_id="D38z5RcWu1voky8WS1d1",  # Arnold (Male, stern)
        stability=0.75,
        similarity_boost=0.85,
    ),
}


def get_voice_profile(entity_name: str) -> VoiceProfile:
    """
    Get the voice profile for an entity.
    
    Args:
        entity_name: Name of the entity
        
    Returns:
        VoiceProfile for the entity
        
    Raises:
        KeyError if entity not found
    """
    if entity_name not in VOICE_PROFILES:
        raise KeyError(f"No voice profile for entity: {entity_name}")
    
    return VOICE_PROFILES[entity_name]


def get_piper_voice_id(entity_name: str) -> str:
    """Get Piper voice ID for an entity."""
    return get_voice_profile(entity_name).piper_voice_id


def get_elevenlabs_voice_id(entity_name: str) -> str:
    """Get ElevenLabs voice ID for an entity."""
    return get_voice_profile(entity_name).elevenlabs_voice_id
