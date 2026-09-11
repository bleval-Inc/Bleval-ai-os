"""
TTS provider abstraction layer.

Enables swapping between Piper, ElevenLabs, and other TTS providers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..models import SynthesizedAudio

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
    ) -> Optional[SynthesizedAudio]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier (provider-specific)
            
        Returns:
            SynthesizedAudio with audio bytes and metadata, or None on error
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is healthy and ready."""
        pass


class TTSProviderFactory:
    """Factory for creating TTS provider instances."""
    
    _providers = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a TTS provider."""
        cls._providers[name] = provider_class
    
    @classmethod
    def create(cls, provider_name: str, **kwargs) -> Optional[TTSProvider]:
        """
        Create a TTS provider instance.
        
        Args:
            provider_name: Name of the provider (piper, elevenlabs)
            **kwargs: Additional arguments to pass to the provider
            
        Returns:
            TTSProvider instance or None if provider not found
        """
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            logger.error(f"Unknown TTS provider: {provider_name}")
            return None
        
        try:
            return provider_class(**kwargs)
        except Exception as e:
            logger.error(f"Error creating {provider_name} provider: {e}")
            return None
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers."""
        return list(cls._providers.keys())


class TTSProviderProxy:
    """
    Proxy that manages primary and fallback TTS providers.
    
    Automatically falls back to fallback provider if primary fails.
    """
    
    def __init__(
        self,
        primary_provider_name: str,
        fallback_provider_name: str,
        **provider_kwargs,
    ):
        """
        Initialize the proxy with primary and fallback providers.
        
        Args:
            primary_provider_name: Name of primary provider
            fallback_provider_name: Name of fallback provider
            **provider_kwargs: Additional arguments for providers
        """
        self.primary = TTSProviderFactory.create(primary_provider_name, **provider_kwargs)
        self.fallback = TTSProviderFactory.create(fallback_provider_name, **provider_kwargs)
        
        if not self.primary and not self.fallback:
            logger.error("No TTS providers available!")
    
    def synthesize(
        self,
        text: str,
        voice_id: str,
    ) -> Optional[SynthesizedAudio]:
        """
        Synthesize text using primary provider, falling back if needed.
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            
        Returns:
            SynthesizedAudio or None if all providers fail
        """
        # Try primary provider
        if self.primary:
            try:
                result = self.primary.synthesize(text, voice_id)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Primary TTS provider failed: {e}")
        
        # Try fallback provider
        if self.fallback:
            try:
                logger.info("Falling back to fallback TTS provider")
                result = self.fallback.synthesize(text, voice_id)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Fallback TTS provider also failed: {e}")
        
        return None
    
    def health_check(self) -> bool:
        """Check whether any configured provider is ready."""
        primary_ok = self.primary.health_check() if self.primary else False
        fallback_ok = self.fallback.health_check() if self.fallback else False
        return primary_ok or fallback_ok
