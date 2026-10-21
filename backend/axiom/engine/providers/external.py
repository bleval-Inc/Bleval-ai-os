"""External API Provider — connects to an external OpenAI-compatible API gateway.

Supports connecting to a LiteLLM gateway or any OpenAI-compatible endpoint.
Configured via environment variables:

  GATEWAY_API_BASE_URL   — Base URL of the gateway (e.g., http://127.0.0.1:4000)
  GATEWAY_API_KEY        — API key for authentication (Bearer token)
  GATEWAY_MODEL          — Model alias to use (e.g., axiom-primary)

Architecture Law 9: Intelligence is provider independent.
"""

import json
import os
from typing import Any, Dict, List, Optional

from axiom.config import settings
from axiom.engine.base import ModelProvider


class ExternalAPIProvider(ModelProvider):
    """Provider for external OpenAI-compatible API gateways.

    Each instance wraps a single gateway+model pair.  The SmartRouter
    can select this provider based on configuration.
    """

    def __init__(self, base_url: str, api_key: str, model_id: str, label: str = "Gateway") -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_id = model_id
        self._label = label
        self._client: Optional[Any] = None

    @property
    def name(self) -> str:
        return f"external-{self._label.lower().replace(' ', '-')}"

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def label(self) -> str:
        return self._label

    @property
    def available(self) -> bool:
        from axiom.config import settings
        return bool(self._api_key) and bool(self._model_id) and bool(self._base_url) and settings.use_gateway_for_intelligence

    async def _get_client(self) -> Any:
        """Lazy-init the OpenAI client pointed at the external gateway."""
        if self._client is None and self.available:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self._api_key,
                    base_url=f"{self._base_url}/v1",
                    timeout=120.0,  # 120s timeout for slow cold-starts
                    max_retries=0,   # we handle retries via fallback chain
                )
            except ImportError:
                raise RuntimeError(
                    "OpenAI SDK not installed. Run: pip install openai"
                )
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        client = await self._get_client()
        if not client:
            return f"[{self.name}] Not configured"

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try up to 2 times for transient errors
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await client.chat.completions.create(
                    model=self._model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                # Check if this is a transient error we should retry
                error_str = str(exc).lower()
                is_transient = (
                    "503" in error_str
                    or "service unavailable" in error_str
                    or "timeout" in error_str
                    or "overloaded" in error_str
                    or "rate limit" in error_str
                    or "429" in error_str
                )

                # If it's not transient or we've used all retries, return the error
                if not is_transient or attempt == max_retries:
                    return f"[{self.name} Error] {exc}"

                # If transient and we have retries left, continue to next attempt
                if attempt < max_retries:
                    continue

        # This shouldn't be reached, but just in case
        return f"[{self.name} Error] Max retries exceeded"

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable description of this provider."""
        return {
            "name": self.name,
            "label": self.label,
            "model": self.model_id,
            "provider": "external",
            "available": self.available,
        }