"""ElevenLabs TTS provider implementation (optional fallback)."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import requests

from axiom.voice.tts.provider_base import TTSProvider, VoiceProfile
from axiom.voice.config import voice_config

logger = logging.getLogger("axiom.voice.tts.elevenlabs_provider")


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS provider for high-quality cloud synthesis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = config.get("api_key") or os.getenv("ELEVENLABS_API_KEY") or voice_config.tts.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self._voice_ids = config.get("voice_ids", voice_config.tts.elevenlabs_voice_ids)
        self._session = None
        
    @property
    def name(self) -> str:
        return "elevenlabs"
    
    def initialize(self) -> bool:
        """Check if ElevenLabs API is available."""
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
            return False
        
        try:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            })
            
            # Test API with a simple request
            response = self._session.get(f"{self.base_url}/voices", timeout=10)
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                logger.info(f"ElevenLabs initialized with {len(voices)} voices available")
                self._initialized = True
                return True
            else:
                logger.error(f"ElevenLabs API error: {response.status_code}")
                return False
                
        except ImportError:
            logger.error("requests library not installed. Install with: pip install requests")
            return False
        except Exception as e:
            logger.error(f"ElevenLabs initialization failed: {e}")
            return False
    
    def is_available(self) -> bool:
        return self._initialized and self.api_key is not None
    
    def synthesize(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """
        Synthesize text to speech using ElevenLabs.
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile with voice_id and parameters
            
        Returns:
            MP3 audio data as bytes
        """
        if not self.is_available():
            raise RuntimeError("ElevenLabs TTS not available")
        
        voice_id = voice_profile.extra.get("voice_id") or self._voice_ids.get(voice_profile.model, "")
        
        if not voice_id:
            # Try to find a matching voice
            raise RuntimeError(f"No ElevenLabs voice_id configured for {voice_profile.model}")
        
        # Build request
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        payload = {
            "text": text,
            "model_id": voice_profile.extra.get("model_id", "eleven_monolingual_v1"),
            "voice_settings": {
                "stability": voice_profile.extra.get("stability", 0.5),
                "similarity_boost": voice_profile.extra.get("similarity_boost", 0.75),
                "style": voice_profile.extra.get("style", 0.0),
                "use_speaker_boost": voice_profile.extra.get("use_speaker_boost", True),
            },
        }
        
        try:
            response = self._session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"ElevenLabs synthesized {len(text)} chars -> {len(audio_data)} bytes")
                return audio_data
            else:
                error_msg = response.text
                logger.error(f"ElevenLabs synthesis failed: {response.status_code} - {error_msg}")
                raise RuntimeError(f"ElevenLabs synthesis failed: {error_msg}")
                
        except requests.exceptions.Timeout:
            raise RuntimeError("ElevenLabs request timed out")
        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
            raise
    
    def list_voices(self) -> list:
        """List available ElevenLabs voices."""
        if not self.is_available():
            return []
        
        try:
            response = self._session.get(f"{self.base_url}/voices", timeout=10)
            if response.status_code == 200:
                return response.json().get("voices", [])
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
        return []


# Try to register ElevenLabs if configured
try:
    elevenlabs_provider = ElevenLabsTTS({
        "api_key": voice_config.tts.elevenlabs_api_key,
        "voice_ids": voice_config.tts.elevenlabs_voice_ids,
    })
    if elevenlabs_provider.initialize():
        from axiom.voice.tts.provider_base import tts_registry
        tts_registry.register(elevenlabs_provider)
        logger.info("ElevenLabs TTS provider registered as fallback")
    else:
        logger.info("ElevenLabs TTS not configured, using Piper only")
except Exception as e:
    logger.debug(f"ElevenLabs provider not registered: {e}")