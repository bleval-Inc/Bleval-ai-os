"""Pydantic models for the multi-model intelligence abstraction layer (§4).

Prepares the architecture for specialized AI providers/models without
hard-coding individual providers into workflows.

Specialized model categories:
  reasoning, research, coding, image generation, video generation,
  audio, transcription, embeddings, classification, extraction

Architecture Law 9: Intelligence is provider independent.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelCapability(str, Enum):
    """Categories of model capability (§4)."""
    REASONING = "reasoning"
    RESEARCH = "research"
    CODING = "coding"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO = "audio"
    TRANSCRIPTION = "transcription"
    EMBEDDINGS = "embeddings"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    GENERAL = "general"


class ModelProfile(BaseModel):
    """Profile of a model's capabilities and characteristics."""
    model_id: str
    provider: str
    display_name: str = ""
    capabilities: List[ModelCapability] = Field(default_factory=list)
    max_tokens: int = 4096
    context_window: int = 8192
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    latency_preference: str = "normal"  # fast | normal | thorough
    available: bool = True
    description: str = ""


class ModelProviderRegistration(BaseModel):
    """Registration of a model provider with the intelligence layer."""
    provider_name: str
    base_url: str = ""
    api_key_env: str = ""
    models: List[ModelProfile] = Field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    weight: float = 1.0
    tags: List[str] = Field(default_factory=list)


class IntelligenceRequest(BaseModel):
    """A request to the multi-model intelligence layer."""
    request_id: str
    prompt: str
    system_prompt: str = ""
    required_capabilities: List[ModelCapability] = Field(default_factory=list)
    preferred_provider: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    agent_id: str = ""
    workflow_instance_id: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class IntelligenceResponse(BaseModel):
    """Response from the multi-model intelligence layer."""
    request_id: str
    provider_used: str
    model_used: str
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    fallback_chain: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CapabilityRouterRule(BaseModel):
    """Routing rule that maps capability to model/provider."""
    rule_id: str
    capability: ModelCapability
    priority_chain: List[str] = Field(default_factory=list)  # Ordered provider names
    fallback_providers: List[str] = Field(default_factory=list)
    min_quality_score: float = 0.0
    max_cost_per_call: float = 0.0
    timeout_seconds: int = 60


class CapabilityRouterConfig(BaseModel):
    """Configuration for the capability-aware model router."""
    rules: List[CapabilityRouterRule] = Field(default_factory=list)
    default_chain: List[str] = Field(default_factory=list)
    enable_fallback: bool = True
    retry_on_failure: bool = True
    max_retries: int = 3
    log_routing: bool = True


class MultiModelRegistry(BaseModel):
    """Registry of all available models across all providers."""
    providers: Dict[str, ModelProviderRegistration] = Field(default_factory=dict)
    capability_map: Dict[str, List[str]] = Field(default_factory=dict)
    last_updated: Optional[datetime] = None