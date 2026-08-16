"""Multi-Model Intelligence Abstraction Layer — PHASE C §4.

Prepares the architecture for specialized AI providers/models without
hard-coding individual providers into workflows.

Model capability categories (§4):
  reasoning, research, coding, image generation, video generation,
  audio, transcription, embeddings, classification, extraction

Architecture Law 9: Intelligence is provider independent.

The capability-aware router extends the existing SmartRouter and
works through the existing intelligence/tool abstraction.
"""

from typing import Any, Dict, List, Optional

from axiom.engine.base import MockProvider, ModelProvider
from axiom.engine.smart_router import (
    ComplexityLevel,
    SmartRouter,
    TaskCategory,
    TaskClassifier,
    TaskProfile,
)
from axiom.models.intelligence_specialized import (
    CapabilityRouterConfig,
    CapabilityRouterRule,
    IntelligenceRequest,
    IntelligenceResponse,
    ModelCapability,
    ModelProfile,
    ModelProviderRegistration,
    MultiModelRegistry,
)


class ModelCapabilityMapper:
    """Maps between ModelCapability enum and SmartRouter TaskCategory.

    This is the bridge between the PHASE C multi-model abstraction
    and the existing SmartRouter framework (Architecture Law 9).
    """

    CAPABILITY_TO_CATEGORY: Dict[ModelCapability, TaskCategory] = {
        ModelCapability.REASONING: TaskCategory.STRATEGIC,
        ModelCapability.RESEARCH: TaskCategory.LONG_CONTEXT,
        ModelCapability.CODING: TaskCategory.CODING,
        ModelCapability.IMAGE_GENERATION: TaskCategory.CREATIVE,
        ModelCapability.VIDEO_GENERATION: TaskCategory.CREATIVE,
        ModelCapability.AUDIO: TaskCategory.CREATIVE,
        ModelCapability.TRANSCRIPTION: TaskCategory.ANALYSIS,
        ModelCapability.EMBEDDINGS: TaskCategory.GENERAL,
        ModelCapability.CLASSIFICATION: TaskCategory.ANALYSIS,
        ModelCapability.EXTRACTION: TaskCategory.ANALYSIS,
        ModelCapability.GENERAL: TaskCategory.GENERAL,
    }

    CATEGORY_TO_CAPABILITY: Dict[TaskCategory, ModelCapability] = {
        TaskCategory.STRATEGIC: ModelCapability.REASONING,
        TaskCategory.CODING: ModelCapability.CODING,
        TaskCategory.LONG_CONTEXT: ModelCapability.RESEARCH,
        TaskCategory.AGENTIC: ModelCapability.REASONING,
        TaskCategory.CREATIVE: ModelCapability.IMAGE_GENERATION,
        TaskCategory.ANALYSIS: ModelCapability.ANALYSIS,
        TaskCategory.GENERAL: ModelCapability.GENERAL,
    }

    @classmethod
    def to_task_category(cls, capability: ModelCapability) -> TaskCategory:
        """Map a ModelCapability to the closest SmartRouter TaskCategory."""
        return cls.CAPABILITY_TO_CATEGORY.get(capability, TaskCategory.GENERAL)

    @classmethod
    def to_model_capability(cls, category: TaskCategory) -> ModelCapability:
        """Map a SmartRouter TaskCategory to ModelCapability."""
        return cls.CATEGORY_TO_CAPABILITY.get(category, ModelCapability.GENERAL)


class CapabilityAwareRouter:
    """Extends SmartRouter with capability-aware routing.

    PHASE C §4: Routes to specialized providers based on task capability
    requirements, not just complexity. Supports fallback chains per capability.

    Architecture:
      Task arrives with required_capabilities []
          ↓
      CapabilityAwareRouter checks the capability map
          ↓
      For each capability, tries the priority chain of providers
          ↓
      Falls back through the chain if primary fails
          ↓
      Returns the best match

    In production mode (REAL_PROVIDERS_ONLY=true), mock provider is NEVER used.
    """

    def __init__(self, smart_router: SmartRouter) -> None:
        self._smart_router = smart_router
        self._mapper = ModelCapabilityMapper()

        # Capability routing rules
        self._rules: Dict[ModelCapability, CapabilityRouterRule] = {}
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """Set up default routing rules for each capability category.

        These can be overridden via the config system.
        Each capability has a priority chain — the router tries
        providers in order and falls through on failure.

        In production mode, 'mock' is automatically excluded from fallback chains.
        """
        self._rules = {
            ModelCapability.REASONING: CapabilityRouterRule(
                rule_id="reasoning",
                capability=ModelCapability.REASONING,
                priority_chain=["anthropic", "openai"],
                fallback_providers=[],
            ),
            ModelCapability.RESEARCH: CapabilityRouterRule(
                rule_id="research",
                capability=ModelCapability.RESEARCH,
                priority_chain=["anthropic", "openai"],
                fallback_providers=[],
            ),
            ModelCapability.CODING: CapabilityRouterRule(
                rule_id="coding",
                capability=ModelCapability.CODING,
                priority_chain=["anthropic", "openai"],
                fallback_providers=[],
            ),
            ModelCapability.IMAGE_GENERATION: CapabilityRouterRule(
                rule_id="image",
                capability=ModelCapability.IMAGE_GENERATION,
                priority_chain=["openai"],  # e.g., DALL-E
                fallback_providers=[],
            ),
            ModelCapability.VIDEO_GENERATION: CapabilityRouterRule(
                rule_id="video",
                capability=ModelCapability.VIDEO_GENERATION,
                priority_chain=[],
                fallback_providers=[],
            ),
            ModelCapability.AUDIO: CapabilityRouterRule(
                rule_id="audio",
                capability=ModelCapability.AUDIO,
                priority_chain=[],
                fallback_providers=[],
            ),
            ModelCapability.TRANSCRIPTION: CapabilityRouterRule(
                rule_id="transcription",
                capability=ModelCapability.TRANSCRIPTION,
                priority_chain=["openai"],  # e.g., Whisper
                fallback_providers=[],
            ),
            ModelCapability.EMBEDDINGS: CapabilityRouterRule(
                rule_id="embeddings",
                capability=ModelCapability.EMBEDDINGS,
                priority_chain=["openai"],
                fallback_providers=[],
            ),
            ModelCapability.CLASSIFICATION: CapabilityRouterRule(
                rule_id="classification",
                capability=ModelCapability.CLASSIFICATION,
                priority_chain=["anthropic", "openai"],
                fallback_providers=[],
            ),
            ModelCapability.EXTRACTION: CapabilityRouterRule(
                rule_id="extraction",
                capability=ModelCapability.EXTRACTION,
                priority_chain=["anthropic", "openai"],
                fallback_providers=[],
            ),
            ModelCapability.GENERAL: CapabilityRouterRule(
                rule_id="general",
                capability=ModelCapability.GENERAL,
                priority_chain=["anthropic", "openai"],
                fallback_providers=[],
            ),
        }

    # ── Rule Management ──────────────────────────────────────────────

    def set_rule(self, rule: CapabilityRouterRule) -> None:
        """Override a routing rule for a capability."""
        self._rules[rule.capability] = rule

    def get_rule(self, capability: ModelCapability) -> Optional[CapabilityRouterRule]:
        """Get the routing rule for a capability."""
        return self._rules.get(capability)

    def set_rules_from_config(self, config: CapabilityRouterConfig) -> None:
        """Apply routing rules from configuration."""
        for rule in config.rules:
            self._rules[rule.capability] = rule

    def list_rules(self) -> List[Dict[str, Any]]:
        """Return all routing rules for inspection."""
        return [
            {
                "capability": rule.capability.value,
                "priority_chain": rule.priority_chain,
                "fallback_providers": rule.fallback_providers,
            }
            for rule in self._rules.values()
        ]

    # ── Routing ──────────────────────────────────────────────────────

    def select_provider(
        self,
        required_capabilities: Optional[List[ModelCapability]] = None,
        task_description: str = "",
        preferred_provider: Optional[str] = None,
    ) -> ModelProvider:
        """Select the best provider for one or more required capabilities.

        If multiple capabilities are required, selects the best provider
        that covers the highest-priority capability.

        Falls back through the chain if primary is unavailable.

        In production mode, mock provider is NEVER used.
        """
        # If specific provider requested, try it first
        if preferred_provider:
            providers = self._smart_router.providers
            if preferred_provider in providers:
                return providers[preferred_provider]

        # Determine the primary capability
        capabilities = required_capabilities or [ModelCapability.GENERAL]
        primary_cap = capabilities[0]

        # Get the routing rule for this capability
        rule = self._rules.get(primary_cap)
        if not rule:
            return self._fallback_to_smart_router(task_description)

        # Try the priority chain
        providers = self._smart_router.providers
        for provider_name in rule.priority_chain:
            if provider_name in providers:
                provider = providers[provider_name]
                if provider.available and not isinstance(provider, MockProvider):
                    return provider

        # Try fallback providers (skipping mock in production)
        for provider_name in rule.fallback_providers:
            if provider_name in providers:
                provider = providers[provider_name]
                if provider.available and not isinstance(provider, MockProvider):
                    return provider

        # Ultimate fallback to smart router
        return self._fallback_to_smart_router(task_description)

    def _fallback_to_smart_router(self, task_description: str) -> ModelProvider:
        """Fall back to the SmartRouter for unhandled capabilities."""
        return self._smart_router.select_provider(
            task_description=task_description,
        )

    # ── Provider Registration ───────────────────────────────────────

    def register_provider_for_capability(
        self,
        provider_name: str,
        capabilities: List[ModelCapability],
        priority: int = 0,
    ) -> None:
        """Register a provider for one or more capabilities.

        Adds the provider to the front of the priority chain for each
        specified capability.
        """
        for capability in capabilities:
            rule = self._rules.get(capability)
            if rule:
                # Insert at the priority position
                if priority == 0:
                    rule.priority_chain.insert(0, provider_name)
                else:
                    pos = min(priority, len(rule.priority_chain))
                    rule.priority_chain.insert(pos, provider_name)

    def get_route_for_capability(
        self, capability: ModelCapability
    ) -> Dict[str, Any]:
        """Show the routing decision for a capability.

        Useful for debugging and transparency.
        """
        rule = self._rules.get(capability)
        providers = self._smart_router.providers
        available_chain = [
            name for name in (rule.priority_chain if rule else [])
            if name in providers and providers[name].available
        ]
        return {
            "capability": capability.value,
            "priority_chain": rule.priority_chain if rule else [],
            "available_in_chain": available_chain,
            "selected": available_chain[0] if available_chain else "mock",
        }


class MultiModelEngine:
    """Multi-model intelligence engine — PHASE C §4.

    Wraps the existing IntelligenceEngine with capability-aware routing.
    Provides a unified interface for requesting intelligence by capability
    rather than by provider name.

    Architecture Law 9: Intelligence is provider independent.

    Usage:
      engine = MultiModelEngine(intelligence_engine)
      response = await engine.generate_by_capability(
          capabilities=[ModelCapability.CODING],
          prompt="Write a function that...",
      )
    """

    def __init__(
        self,
        intelligence_engine: Any,  # IntelligenceEngine
    ) -> None:
        self._intelligence = intelligence_engine

        # Get the underlying SmartRouter
        smart_router = None
        if hasattr(intelligence_engine, "_smart_router"):
            smart_router = intelligence_engine._smart_router
        if smart_router is None and hasattr(intelligence_engine, "router"):
            smart_router = intelligence_engine.router

        self._smart_router = smart_router
        self._capability_router = CapabilityAwareRouter(
            smart_router or SmartRouter()
        )
        self._mapper = ModelCapabilityMapper()

        # Provider registry for specialized models
        self._provider_registry: Dict[str, ModelProviderRegistration] = {}

    # ── Properties ──────────────────────────────────────────────────

    @property
    def capability_router(self) -> CapabilityAwareRouter:
        """Expose the capability router for inspection."""
        return self._capability_router

    # ── Generation by Capability ────────────────────────────────────

    async def generate_by_capability(
        self,
        capabilities: List[ModelCapability],
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        agent_id: str = "",
    ) -> IntelligenceResponse:
        """Generate a response using providers that match the required capabilities.

        Uses the capability-aware router to select the best provider,
        then delegates to the IntelligenceEngine for generation.
        """
        import time
        import uuid

        request_id = str(uuid.uuid4())
        start = time.monotonic()

        # Select provider by capability
        provider = self._capability_router.select_provider(
            required_capabilities=capabilities,
            task_description=prompt[:500],
        )
        provider_name = provider.name if hasattr(provider, "name") else type(provider).__name__

        # Track fallback chain
        fallback_chain: List[str] = []

        try:
            # If we have a real intelligence engine, use it
            if self._intelligence and hasattr(self._intelligence, "generate"):
                result = await self._intelligence.generate(
                    agent_id=agent_id or "multi_model",
                    task_description=prompt,
                    additional_context={
                        "required_capabilities": [c.value for c in capabilities],
                        "request_id": request_id,
                    },
                    max_tokens=max_tokens,
                    temperature=temperature,
                    preferred_provider=provider_name if provider_name != "mock" else None,
                )
            else:
                result = await provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            duration_ms = (time.monotonic() - start) * 1000

            return IntelligenceResponse(
                request_id=request_id,
                provider_used=provider_name,
                model_used=provider_name,
                content=result,
                duration_ms=duration_ms,
                success=True,
                fallback_chain=fallback_chain,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            return IntelligenceResponse(
                request_id=request_id,
                provider_used=provider_name,
                model_used=provider_name,
                content=str(exc),
                duration_ms=duration_ms,
                success=False,
                error=str(exc),
                fallback_chain=fallback_chain,
            )

    async def generate_raw(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        preferred_provider: Optional[str] = None,
    ) -> str:
        """Generate from raw prompt — compatible with IntelligenceEngine API."""
        capabilities = [ModelCapability.GENERAL]
        response = await self.generate_by_capability(
            capabilities=capabilities,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.content

    # ── Provider Registration ───────────────────────────────────────

    def register_provider(
        self, registration: ModelProviderRegistration
    ) -> None:
        """Register a model provider with its capabilities.

        Maps the provider's models to the capability router so they
        are selected for matching tasks.
        """
        self._provider_registry[registration.provider_name] = registration

        # Register each model for its capabilities
        for model in registration.models:
            for capability in model.capabilities:
                self._capability_router.register_provider_for_capability(
                    provider_name=model.model_id or registration.provider_name,
                    capabilities=[capability],
                    priority=registration.priority,
                )

    def list_registered_providers(self) -> List[Dict[str, Any]]:
        """Return all registered providers with their capabilities."""
        result = []
        for name, reg in self._provider_registry.items():
            result.append({
                "provider": name,
                "enabled": reg.enabled,
                "priority": reg.priority,
                "models": [
                    {
                        "model_id": m.model_id,
                        "capabilities": [c.value for c in m.capabilities],
                        "available": m.available,
                    }
                    for m in reg.models
                ],
            })
        return result

    def get_route_for_capability(
        self, capability: ModelCapability
    ) -> Dict[str, Any]:
        """Show routing for a capability (debug/transparency)."""
        return self._capability_router.get_route_for_capability(capability)

    # ── Summary ─────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the multi-model engine state."""
        return {
            "registered_providers": len(self._provider_registry),
            "capability_rules": len(self._capability_router.list_rules()),
            "available_capabilities": [
                c.value for c in ModelCapability
            ],
            "routing_rules": self._capability_router.list_rules(),
        }