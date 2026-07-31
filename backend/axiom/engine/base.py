"""Base Provider Interface — abstract base for all AI model providers.

Extracted to its own module to avoid circular imports between intelligence.py
and provider implementations (NVIDIA, Anthropic, OpenAI, etc.).

Architecture Law 9: Intelligence is provider independent.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ModelProvider(ABC):
    """Abstract base class for AI model providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Send a prompt to the model and return the response."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider is configured and usable."""


class MockProvider(ModelProvider):
    """Mock provider that returns canned responses for testing.

    Used when no API keys are configured and no real provider is available.
    """

    @property
    def name(self) -> str:
        return "mock"

    @property
    def available(self) -> bool:
        return True  # Always available

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        prompt_len = len(prompt)
        return json.dumps({
            "provider": "mock",
            "status": "mock_response",
            "analysis": (
                f"[MockProvider] Received {prompt_len} chars. "
                f"Prompt preview: {prompt[:200]}..."
            ),
            "recommendation": "No action needed (mock mode)",
            "rationale": "Mock provider is active. Set API keys for real reasoning.",
        })