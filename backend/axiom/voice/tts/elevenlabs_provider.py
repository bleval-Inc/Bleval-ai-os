"""
ElevenLabs TTS provider implementation (optional fallback).

Provides higher quality voices with emotional direction.
Can be used as hybrid with Piper fallback.
"""

import logging
from typing import Optional

from ..models import SynthesizedAudio
from .provider_base import TTSProvider, TTSProviderFactory

logger = logging.getLogger(__name__)


class ElevenLabsTTS(TTSProvider):
    """
    Text-to-Speech using ElevenLabs API.
    
    Provides high-quality, emotionally-controlled voices.
    Requires ELEVENLABS_API_KEY environment variable.
    """
    
    def __init__(self, api_key: str = "", **kwargs):
        """
        Initialize ElevenLabs TTS.
        
        Args:
            api_key: ElevenLabs API key
            **kwargs: Additional config options
        """
        self.api_key = api_key
        self.client = None
        self._load_client()
    
    def _load_client(self):
        """Load the ElevenLabs client."""
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
            return
        
        try:
            from elevenlabs import ElevenLabs
            
            logger.info("Initializing ElevenLabs client")
            self.client = ElevenLabs(api_key=self.api_key)
            logger.info("ElevenLabs client initialized")
        except ImportError:
            logger.warning(
                "elevenlabs not installed. Install with: pip install elevenlabs"
            )
        except Exception as e:
            logger.error(f"Error initializing ElevenLabs: {e}")
    
    def synthesize(
        self,
        text: str,
        voice_profile: VoiceProfile,
    ) -> Optional[SynthesizedAudio]:
        """
        Synthesize text to speech using ElevenLabs.

        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use

        Returns:
            SynthesizedAudio with audio bytes
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return None

        # Extract voice ID from the voice profile's extra data
        # For ElevenLabs, the voice ID is stored in the extra field as voice_id
        voice_id = voice_profile.extra.get("voice_id", "") if voice_profile.extra else ""
        if not voice_id:
            logger.error("ElevenLabs voice ID not configured in voice profile")
            return None

        try:
            logger.debug(
                f"Synthesizing with ElevenLabs: voice={voice_id}, text='{text[:50]}...'"
            )

            # Call ElevenLabs API
            audio = self.client.generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1",  # or "eleven_multilingual_v2"
            )

            audio_bytes = b''.join(audio)

            if not audio_bytes:
                logger.error("ElevenLabs returned empty audio")
                return None

            # Estimate duration (ElevenLabs returns MP3, so we estimate)
            # Typical MP3 bitrate is 128-192 kbps
            estimated_duration = len(audio_bytes) / (128 * 1024 / 8)

            logger.info(f"ElevenLabs synthesis complete: ~{estimated_duration:.2f}s audio")

            return SynthesizedAudio(
                audio_bytes=audio_bytes,
                audio_url=None,
                duration_seconds=estimated_duration,
                sample_rate=24000,  # ElevenLabs uses 24kHz
            )

        except Exception as e:
            logger.error(f"Error in ElevenLabs synthesis: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if ElevenLabs is configured and accessible."""
        if not self.client:
            return False
        
        try:
            # Try to get voices as a health check
            voices = self.client.voices.get_all()
            return len(voices.voices) > 0
        except Exception as e:
            logger.warning(f"ElevenLabs health check failed: {e}")
            return False


# Register ElevenLabs as a TTS provider
TTSProviderFactory.register("elevenlabs", ElevenLabsTTS)
