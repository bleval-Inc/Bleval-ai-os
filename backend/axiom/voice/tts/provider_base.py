"""TTS Provider abstraction layer."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("axiom.voice.tts.provider_base")


@dataclass
class VoiceProfile:
    """Voice profile configuration for an executive."""
    provider: str
    model: str
    speaker_id: int = 0
    length_scale: float = 1.0
    noise_scale: float = 0.667
    noise_w: float = 0.8
    # Provider-specific config
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the TTS provider. Returns True on success."""
        pass
    
    @abstractmethod
    def synthesize(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """
        Synthesize text to speech audio.
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use
            
        Returns:
            Audio data as bytes (WAV format)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass


class TTSProviderRegistry:
    """Registry for managing TTS providers."""
    
    def __init__(self):
        self._providers: Dict[str, TTSProvider] = {}
        self._default_provider: Optional[str] = None
    
    def register(self, provider: TTSProvider, name: Optional[str] = None) -> None:
        """Register a provider."""
        provider_name = name or provider.name
        self._providers[provider_name] = provider
        if self._default_provider is None:
            self._default_provider = provider_name
        logger.info(f"Registered TTS provider: {provider_name}")
    
    def get(self, name: str) -> Optional[TTSProvider]:
        """Get a provider by name."""
        return self._providers.get(name)
    
    def get_default(self) -> Optional[TTSProvider]:
        """Get the default provider."""
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None
    
    def set_default(self, name: str) -> bool:
        """Set the default provider."""
        if name in self._providers:
            self._default_provider = name
            return True
        return False
    
    def list_providers(self) -> list:
        """List available providers."""
        return list(self._providers.keys())
    
    def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = provider.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize provider {name}: {e}")
                results[name] = False
        return results


# Global registry instance
tts_registry = TTSProviderRegistry()