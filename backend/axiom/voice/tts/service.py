"""TTS Service for synthesizing executive speech."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

from axiom.voice.tts.provider_base import TTSProvider, VoiceProfile, tts_registry
from axiom.voice.tts.voice_profiles import (
    EXECUTIVE_VOICE_PROFILES,
    EXECUTIVE_GREETINGS,
    get_best_voice_profile,
    get_voice_profile,
)
from axiom.voice.config import voice_config

logger = logging.getLogger("axiom.voice.tts.service")


class TextToSpeechService:
    """
    High-level TTS service for executive speech synthesis.
    
    Handles provider selection, voice profiles, and audio output.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else {}
        self._default_provider_name = self.config.get("default_provider", voice_config.tts.provider)
        self._lock = threading.Lock()
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize all registered providers."""
        results = tts_registry.initialize_all()
        
        # Set default provider
        if self._default_provider_name in tts_registry._providers:
            tts_registry.set_default(self._default_provider_name)
            logger.info(f"Default TTS provider set to: {self._default_provider_name}")
        else:
            # Fall back to first available
            available = [name for name, success in results.items() if success]
            if available:
                tts_registry.set_default(available[0])
                logger.info(f"Default TTS provider set to: {available[0]}")
            else:
                logger.error("No TTS providers available")
                return False
        
        self._initialized = True
        return True
    
    def synthesize(
        self,
        text: str,
        executive_id: str,
        provider_name: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize text for an executive.
        
        Args:
            text: Text to synthesize
            executive_id: Executive identifier (axiom, jenson, valta_prime, yamako)
            provider_name: Optional specific provider to use
            
        Returns:
            Audio data as bytes
        """
        if not self._initialized:
            self.initialize()
        
        # Get voice profile
        voice_profile = get_best_voice_profile(executive_id)
        
        # Get provider
        if provider_name:
            provider = tts_registry.get(provider_name)
        else:
            provider = tts_registry.get(voice_profile.provider)
        
        if not provider:
            # Fall back to default
            provider = tts_registry.get_default()
            if not provider:
                raise RuntimeError("No TTS provider available")
            logger.warning(f"Requested provider not available, using default: {provider.name}")
        
        if not provider.is_available():
            raise RuntimeError(f"Provider {provider.name} not available")
        
        logger.info(f"Synthesizing for {executive_id} using {provider.name}: '{text[:50]}...'")
        
        try:
            audio_data = provider.synthesize(text, voice_profile)
            return audio_data
        except Exception as e:
            logger.error(f"TTS synthesis failed for {executive_id}: {e}")
            # Try fallback provider if not already using default
            if provider != tts_registry.get_default():
                logger.info("Attempting fallback to default provider")
                fallback = tts_registry.get_default()
                if fallback and fallback != provider and fallback.is_available():
                    try:
                        return fallback.synthesize(text, voice_profile)
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}")
            raise
    
    def synthesize_greeting(self, executive_id: str) -> bytes:
        """Synthesize the standard greeting for an executive."""
        greeting = EXECUTIVE_GREETINGS.get(executive_id.lower(), f"{executive_id} online.")
        return self.synthesize(greeting, executive_id)
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {
            name: provider.is_available()
            for name, provider in tts_registry._providers.items()
        }
    
    def get_voice_profile(self, executive_id: str) -> Optional[VoiceProfile]:
        """Get the voice profile for an executive."""
        return get_voice_profile(executive_id)


# Global TTS service instance (lazy initialization)
_tts_service_instance: Optional[TextToSpeechService] = None


def get_tts_service() -> TextToSpeechService:
    """Get or create the global TTS service instance."""
    global _tts_service_instance
    if _tts_service_instance is None:
        _tts_service_instance = TextToSpeechService()
    return _tts_service_instance


# Backward compatibility
tts_service = None  # Will be set on first access via get_tts_service()


def speak_executive(
    executive_id: str,
    text: str,
    provider_name: Optional[str] = None,
) -> bytes:
    """Convenience function to synthesize executive speech."""
    return get_tts_service().synthesize(text, executive_id, provider_name)


def speak_greeting(executive_id: str) -> bytes:
    """Convenience function to synthesize executive greeting."""
    return get_tts_service().synthesize_greeting(executive_id)