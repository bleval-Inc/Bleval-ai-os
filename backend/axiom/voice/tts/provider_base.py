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
    def synthesize(self, text: str, voice_profile: VoiceProfile) -> Optional[SynthesizedAudio]:
        """
        Synthesize text to speech audio.

        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use

        Returns:
            SynthesizedAudio object containing audio bytes and metadata, or None if synthesis failed
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
        voice_profile: VoiceProfile,
    ) -> Optional[bytes]:
        """
        Synthesize text using primary provider, falling back if needed.

        Args:
            text: Text to synthesize
            voice_profile: Voice profile to use

        Returns:
            Audio data as bytes or None if all providers fail
        """
        # Try primary provider
        if self.primary:
            try:
                result = self.primary.synthesize(text, voice_profile)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Primary TTS provider failed: {e}")

        # Try fallback provider
        if self.fallback:
            try:
                logger.info("Falling back to fallback TTS provider")
                result = self.fallback.synthesize(text, voice_profile)
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


class TTSProviderRegistry:
    """Registry for managing TTS provider instances."""

    def __init__(self):
        self._providers: dict[str, TTSProvider] = {}
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
        if self._default_provider and self._default_provider in self._providers:
            return self._providers.get(self._default_provider)
        # Return first available provider if no default set
        if self._providers:
            return next(iter(self._providers.values()))
        return None

    def set_default(self, name: str) -> bool:
        """Set the default provider."""
        if name in self._providers:
            self._default_provider = name
            logger.info(f"Default TTS provider set to: {name}")
            return True
        return False

    def list_providers(self) -> list:
        """List available providers."""
        return list(self._providers.keys())

    def initialize_all(self) -> dict[str, bool]:
        """Initialize all registered providers.

        Returns:
            Dictionary mapping provider names to initialization success
        """
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = provider.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize provider {name}: {e}")
                results[name] = False
        return results

    def is_available(self, name: str) -> bool:
        """Check if a provider is available."""
        provider = self._providers.get(name)
        if provider is None:
            return False
        if hasattr(provider, 'is_available'):
            return provider.is_available()
        return provider.health_check()


# Global registry instance
tts_registry = TTSProviderRegistry()