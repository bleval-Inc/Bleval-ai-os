"""NVIDIA NIM Provider — connects to NVIDIA's OpenAI-compatible API.

Supports multiple models hosted on NVIDIA's platform, each with its own
API key and endpoint.  Models are configured via environment variables:

  NVIDIA_GLM52_KEY / NVIDIA_GLM52_MODEL        — Z.ai GLM-5.2 (strategic)
  NVIDIA_MISTRAL_MAMBA_KEY / ...               — Mistral Mamba MoE (long-context)
  NVIDIA_STEPFUN_KEY / ...                     — Stepfun Sparse MoE (multimodal)
  NVIDIA_GENERAL_KEY / ...                     — NVIDIA general (everyday)

All keys use the nvapi-* format and route through:
    https://integrate.api.nvidia.com/v1
"""

import json
import os
from typing import Any, Dict, List, Optional

from axiom.config import settings
from axiom.engine.base import ModelProvider


# ── Model Configuration ────────────────────────────────────────────────────

class NVIDIAModelConfig:
    """Configuration for a single NVIDIA-hosted model."""

    def __init__(self, env_key: str, env_model: str, env_provider: str, label: str, role: str) -> None:
        self.api_key = os.getenv(env_key, "")
        self.model_id = os.getenv(env_model, "")
        self.provider_name = os.getenv(env_provider, "nvidia")
        self.label = label
        self.role = role
        self.base_url = os.getenv("NVIDIA_API_BASE_URL", "https://integrate.api.nvidia.com/v1")

    @property
    def configured(self) -> bool:
        return bool(self.api_key) and bool(self.model_id)


# ── NVIDIA Provider ────────────────────────────────────────────────────────

class NVIDIAProvider(ModelProvider):
    """Provider for NVIDIA-hosted models via OpenAI-compatible API.

    Each instance wraps a single model+key pair.  The SmartRouter
    selects which instance to use based on task analysis.

    Architecture Law 9: Intelligence is provider independent.
    """

    def __init__(self, config: NVIDIAModelConfig) -> None:
        self._config = config
        self._client: Optional[Any] = None

    @property
    def name(self) -> str:
        return f"nvidia-{self._config.provider_name}"

    @property
    def model_id(self) -> str:
        return self._config.model_id

    @property
    def label(self) -> str:
        return self._config.label

    @property
    def provider_name(self) -> str:
        return self._config.provider_name

    @property
    def role(self) -> str:
        return self._config.role

    @property
    def available(self) -> bool:
        return self._config.configured

    async def _get_client(self) -> Any:
        """Lazy-init the OpenAI client pointed at NVIDIA's API."""
        if self._client is None and self._config.configured:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self._config.api_key,
                    base_url=self._config.base_url,
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
                    model=self._config.model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                # Check if this is a transient error we should retry
                error_str = str(exc).lower()
                is_transient = (
                    "503" in error_str or
                    "service unavailable" in error_str or
                    "timeout" in error_str or
                    "overloaded" in error_str or
                    "rate limit" in error_str or
                    "429" in error_str
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
            "provider": self.provider_name,
            "role": self.role,
            "available": self.available,
        }


# ── Provider Factory ───────────────────────────────────────────────────────

def create_nvidia_providers() -> List[NVIDIAProvider]:
    """Discover and instantiate all configured NVIDIA models.

    Reads environment variables and returns a list of providers
    for every model that has both a key and a model ID configured.
    """
    configs = [
        NVIDIAModelConfig(
            env_key="NVIDIA_NEMOTRON_ULTRA_KEY",
            env_model="NVIDIA_NEMOTRON_ULTRA_MODEL",
            env_provider="NVIDIA_NEMOTRON_ULTRA_PROVIDER",
            label="NVIDIA Nemotron 3 Ultra",
            role="FLAGSHIP — strategic reasoning, executive decisions, long-horizon planning",
        ),
        NVIDIAModelConfig(
            env_key="NVIDIA_GLM52_KEY",
            env_model="NVIDIA_GLM52_MODEL",
            env_provider="NVIDIA_GLM52_PROVIDER",
            label="Z.ai GLM-5.2",
            role="FLAGSHIP — strategic reasoning, executive decisions, long-horizon planning",
        ),
        NVIDIAModelConfig(
            env_key="NVIDIA_MISTRAL_MAMBA_KEY",
            env_model="NVIDIA_MISTRAL_MAMBA_MODEL",
            env_provider="NVIDIA_MISTRAL_MAMBA_PROVIDER",
            label="Mistral Mamba-Transformer MoE",
            role="LONG-CONTEXT — 1M context, agentic reasoning, planning, tool calling",
        ),
        NVIDIAModelConfig(
            env_key="NVIDIA_STEPFUN_KEY",
            env_model="NVIDIA_STEPFUN_MODEL",
            env_provider="NVIDIA_STEPFUN_PROVIDER",
            label="Stepfun Sparse MoE",
            role="MULTIMODAL — enterprise reasoning, agentic tasks, code generation",
        ),
        NVIDIAModelConfig(
            env_key="NVIDIA_GENERAL_KEY",
            env_model="NVIDIA_GENERAL_MODEL",
            env_provider="NVIDIA_GENERAL_PROVIDER",
            label="NVIDIA General Purpose",
            role="GENERAL — text generation, coding, everyday agentic tasks",
        ),
    ]

    return [NVIDIAProvider(cfg) for cfg in configs if cfg.configured]