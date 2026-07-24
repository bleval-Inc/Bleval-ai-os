"""Intelligence Engine — model routing, context assembly, and provider abstraction.

Architecture Law 9: Intelligence is provider independent.
Executives and agents request reasoning.  The Intelligence Engine selects
the appropriate model and assembles full context from memory, tools,
and conversation history.

Every reasoning cycle includes:
  Memory retrieval  →  Tool context  →  Provider routing  →  Generation
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from axiom.config import settings
from axiom.engine.memory import MemoryEngine
from axiom.engine.tool import ToolEngine
from axiom.registry.agent import AgentRegistryLoader


# =========================================================================
# Provider Abstraction
# =========================================================================


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


# =========================================================================
# Anthropic Provider
# =========================================================================


class AnthropicProvider(ModelProvider):
    """Anthropic Claude provider via the Anthropic SDK.

    Requires ANTHROPIC_API_KEY to be set in the environment or .env file.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self._client: Optional[Any] = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def _get_client(self) -> Any:
        """Lazy-init the Anthropic client."""
        if self._client is None and self._api_key:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
            except ImportError:
                raise RuntimeError(
                    "Anthropic SDK not installed. Run: pip install anthropic"
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
            return "[AnthropicProvider] No API key configured"

        kwargs: Dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = await client.messages.create(**kwargs)
            return response.content[0].text if response.content else ""
        except Exception as exc:
            return f"[AnthropicProvider Error] {exc}"


class AnthropicFastProvider(AnthropicProvider):
    """Anthropic Claude Haiku — faster, cheaper for simple tasks."""

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.5,
    ) -> str:
        client = await self._get_client()
        if not client:
            return "[AnthropicFastProvider] No API key configured"

        kwargs: Dict[str, Any] = {
            "model": "claude-haiku-4-20250514",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = await client.messages.create(**kwargs)
            return response.content[0].text if response.content else ""
        except Exception as exc:
            return f"[AnthropicFastProvider Error] {exc}"


# =========================================================================
# OpenAI Provider
# =========================================================================


class OpenAIProvider(ModelProvider):
    """OpenAI GPT provider via the OpenAI SDK.

    Requires OPENAI_API_KEY to be set in the environment or .env file.
    """

    FAST_MODEL = "gpt-4o-mini"
    POWER_MODEL = "gpt-4o"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or settings.openai_api_key
        self._client: Optional[Any] = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def _get_client(self) -> Any:
        if self._client is None and self._api_key:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self._api_key)
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
            return "[OpenAIProvider] No API key configured"

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self.POWER_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            return f"[OpenAIProvider Error] {exc}"


class OpenAIFastProvider(OpenAIProvider):
    """OpenAI GPT-4o-mini — faster, cheaper for simple tasks."""

    POWER_MODEL = "gpt-4o-mini"  # Override to use fast model for everything

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.5,
    ) -> str:
        client = await self._get_client()
        if not client:
            return "[OpenAIFastProvider] No API key configured"

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self.FAST_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            return f"[OpenAIFastProvider Error] {exc}"


# =========================================================================
# Mock Provider (fallback / testing)
# =========================================================================


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
        # Return a structured mock response that mimics what a real model
        # would return, so the system can operate in mock mode for testing
        prompt_len = len(prompt)
        return json.dumps({
            "provider": "mock",
            "status": "mock_response",
            "analysis": (
                f"[MockProvider] Received {prompt_len} chars. "
                f"Prompt preview: {prompt[:200]}..."
            ),
            "recommendation": "No action needed (mock mode)",
            "rationale": "Mock provider is active. Set ANTHROPIC_API_KEY or OPENAI_API_KEY for real reasoning.",
        })


# =========================================================================
# Provider Router
# =========================================================================

# Complexity levels for task routing
COMPLEXITY_SIMPLE = "simple"
COMPLEXITY_NORMAL = "normal"
COMPLEXITY_COMPLEX = "complex"
COMPLEXITY_STRATEGIC = "strategic"


class ProviderRouter:
    """Routes reasoning requests to the appropriate provider and model.

    Selection criteria:
      - Available API keys (Anthropic preferred, OpenAI fallback)
      - Task complexity (simple → fast model, complex → powerful model)
      - Agent type (executives get strategic routing)
    """

    def __init__(self) -> None:
        self._providers: Dict[str, ModelProvider] = {}
        self._register_available()

    def _register_available(self) -> None:
        """Register all providers that have their API keys configured."""
        # Anthropic providers
        anthro = AnthropicProvider()
        if anthro.available:
            self._providers["anthropic"] = anthro
            self._providers["anthropic-fast"] = AnthropicFastProvider()

        # OpenAI providers (fallback if Anthropic not available)
        openai = OpenAIProvider()
        if openai.available and "anthropic" not in self._providers:
            self._providers["openai"] = openai
            self._providers["openai-fast"] = OpenAIFastProvider()

        # Always register mock as last resort
        self._providers["mock"] = MockProvider()

    def select_provider(
        self,
        complexity: str = COMPLEXITY_NORMAL,
        preferred_provider: Optional[str] = None,
    ) -> ModelProvider:
        """Select the best provider for the given complexity.

        Args:
            complexity: task complexity level
            preferred_provider: if set, try this provider first

        Returns:
            A ModelProvider instance (always at least MockProvider)
        """
        # If a specific provider is requested and available, use it
        if preferred_provider and preferred_provider in self._providers:
            return self._providers[preferred_provider]

        # Route by complexity
        if complexity == COMPLEXITY_STRATEGIC:
            # Strategic tasks get the most powerful model
            for name in ("anthropic", "openai"):
                if name in self._providers:
                    return self._providers[name]
        elif complexity == COMPLEXITY_COMPLEX:
            # Complex tasks get the powerful model
            for name in ("anthropic", "openai"):
                if name in self._providers:
                    return self._providers[name]
        elif complexity == COMPLEXITY_SIMPLE:
            # Simple tasks get the fast/cheap model
            for name in ("anthropic-fast", "openai-fast"):
                if name in self._providers:
                    return self._providers[name]
        else:
            # Normal tasks get the standard model (prefer Anthropic)
            for name in ("anthropic", "openai"):
                if name in self._providers:
                    return self._providers[name]

        # Fallback to any registered provider
        for provider in self._providers.values():
            return provider

        # Last resort (should never reach here since mock is always registered)
        return MockProvider()

    def list_available(self) -> List[Dict[str, Any]]:
        """Return info about all registered providers."""
        return [
            {"name": p.name, "available": p.available}
            for p in self._providers.values()
        ]

    @property
    def has_real_provider(self) -> bool:
        """Whether at least one real (non-mock) provider is available."""
        return any(
            p.available and not isinstance(p, MockProvider)
            for p in self._providers.values()
        )


# =========================================================================
# Context Builder
# =========================================================================


def _complexity_for_agent(agent_id: str) -> str:
    """Determine task complexity based on agent type.

    Executives and strategic roles get higher complexity routing.
    """
    strategic_agents = {"jenson", "valta_prime", "yamako"}
    if agent_id in strategic_agents:
        return COMPLEXITY_STRATEGIC
    return COMPLEXITY_NORMAL


class ContextBuilder:
    """Assembles full reasoning context from all available sources.

    Every reasoning cycle retrieves:
      1. Agent instructions and identity
      2. Memory context (layered: global → org → dept → agent)
      3. Tool context (available tools + permissions)
      4. Task description and additional context
    """

    def __init__(
        self,
        memory: MemoryEngine,
        tool: ToolEngine,
        agent_loader: AgentRegistryLoader,
    ) -> None:
        self._memory = memory
        self._tool = tool
        self._agent_loader = agent_loader

    def assemble_prompt(
        self,
        agent_id: str,
        task_description: str,
        org_id: str = "",
        dept_id: str = "",
        additional_context: Optional[Dict[str, Any]] = None,
        include_memory: bool = True,
        include_tools: bool = True,
    ) -> str:
        """Assemble a full reasoning prompt for an agent.

        Returns a structured prompt string with all context sections.
        """
        parts = []

        # 1. Agent instructions
        instructions = self._agent_loader.load_instructions(agent_id)
        if instructions:
            parts.append("## INSTRUCTIONS\n" + instructions.strip())

        # 2. Agent identity
        identity = self._agent_loader.load_identity(agent_id)
        if identity:
            parts.append("## IDENTITY\n" + identity.strip())

        # 3. Memory context (layered retrieval)
        if include_memory:
            memory_str = self._memory.get_context_string(agent_id, org_id, dept_id)
            if memory_str:
                parts.append("## MEMORY CONTEXT\n" + memory_str)

        # 4. Tool context
        if include_tools and org_id:
            tool_context = self._build_tool_context(agent_id, org_id)
            if tool_context:
                parts.append("## AVAILABLE TOOLS\n" + tool_context)

        # 5. Task description
        parts.append("## TASK\n" + task_description)

        # 6. Additional context
        if additional_context:
            context_lines = "\n".join(
                f"{k}: {v}" for k, v in additional_context.items()
            )
            parts.append("## ADDITIONAL CONTEXT\n" + context_lines)

        # 7. Execution constraints
        parts.append(
            "## EXECUTION CONSTRAINTS\n"
            "- You are an AI executive/specialist in the Axiom OS platform.\n"
            "- You NEVER perform operational work directly.\n"
            "- You reason, plan, and delegate through workflows.\n"
            "- Your response must be actionable and specific.\n"
            "- If you lack information, state what you need.\n"
        )

        return "\n\n---\n\n".join(parts)

    def _build_tool_context(self, agent_id: str, org_id: str) -> str:
        """Build a formatted string of available tools and permissions."""
        lines: List[str] = []

        # Available tools for the org
        tools = self._tool.get_available_tools(org_id)
        if tools:
            lines.append("Available tools for your organization:")
            for t in tools:
                caps = ", ".join(t.capabilities) if hasattr(t, "capabilities") else ""
                lines.append(f"  - {t.id}: {t.description} [{caps}]")

        # Agent permissions
        can_actions: List[str] = []
        detail = self._agent_loader.load_detail(agent_id)
        if detail:
            can_actions = detail.permissions.can

        if can_actions:
            lines.append(f"\nYour permitted actions: {', '.join(can_actions)}")

        return "\n".join(lines) if lines else ""

    def build_system_prompt(self, agent_id: str, org_id: str = "") -> str:
        """Build the system prompt that defines the agent's role and constraints.

        This is sent as the system message to the LLM provider.
        """
        identity = self._agent_loader.load_identity(agent_id)
        instructions = self._agent_loader.load_instructions(agent_id)

        parts = [
            "You are an autonomous AI agent in the Axiom OS platform.",
            "",
        ]

        if identity:
            parts.append(identity.strip())
            parts.append("")

        if instructions:
            parts.append(instructions.strip())
            parts.append("")

        parts.extend([
            "## CORE RULES",
            "- You NEVER perform operational work directly (Architecture Law 2).",
            "- You reason, plan, and delegate through approved workflows.",
            "- You use available tools and memory to make informed decisions.",
            "- You consult organizational memory before making strategic decisions.",
            "- You report outcomes and request approvals when required.",
        ])

        return "\n".join(parts)


# =========================================================================
# Intelligence Engine
# =========================================================================


class IntelligenceEngine:
    """Model routing, context assembly, and prompt orchestration.

    This is the central reasoning engine for Axiom OS.  Every reasoning
    cycle flows through:

        1. Context assembly (memory + tools + identity)
        2. Provider selection (routed by complexity)
        3. Generation (real LLM or mock)
        4. Response parsing

    Architecture Law 9: Intelligence is provider independent.
    """

    def __init__(
        self,
        memory: Optional[MemoryEngine] = None,
        tool: Optional[ToolEngine] = None,
    ) -> None:
        self._memory = memory or MemoryEngine()
        self._tool = tool or ToolEngine()
        self._agent_loader = AgentRegistryLoader()
        self._router = ProviderRouter()
        self._context_builder = ContextBuilder(
            memory=self._memory,
            tool=self._tool,
            agent_loader=self._agent_loader,
        )

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def has_real_provider(self) -> bool:
        """Whether at least one real (non-mock) provider is available."""
        return self._router.has_real_provider

    @property
    def router(self) -> ProviderRouter:
        """Expose the provider router for inspection."""
        return self._router

    # ── Context Assembly ──────────────────────────────────────────────────

    def assemble_prompt(
        self,
        agent_id: str,
        task_description: str,
        org_id: str = "",
        dept_id: str = "",
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Assemble a full reasoning prompt (public API, backward-compatible)."""
        return self._context_builder.assemble_prompt(
            agent_id=agent_id,
            task_description=task_description,
            org_id=org_id,
            dept_id=dept_id,
            additional_context=additional_context,
        )

    def build_system_prompt(self, agent_id: str, org_id: str = "") -> str:
        """Build the system prompt for an agent."""
        return self._context_builder.build_system_prompt(agent_id, org_id)

    # ── Generation ────────────────────────────────────────────────────────

    async def generate(
        self,
        agent_id: str,
        task_description: str,
        org_id: str = "",
        dept_id: str = "",
        additional_context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        preferred_provider: Optional[str] = None,
    ) -> str:
        """Generate a response for an agent with full context assembly.

        This is the primary reasoning entry point.  It:
        1. Determines complexity based on agent role
        2. Assembles full context (memory + tools + identity)
        3. Routes to the best provider
        4. Generates and returns the response
        """
        # Determine complexity
        complexity = _complexity_for_agent(agent_id)

        # Build the system prompt
        system_prompt = self.build_system_prompt(agent_id, org_id)

        # Assemble the full prompt
        prompt = self.assemble_prompt(
            agent_id=agent_id,
            task_description=task_description,
            org_id=org_id,
            dept_id=dept_id,
            additional_context=additional_context,
        )

        # Select provider
        provider = self._router.select_provider(
            complexity=complexity,
            preferred_provider=preferred_provider,
        )

        # Generate
        return await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def generate_raw(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        preferred_provider: Optional[str] = None,
    ) -> str:
        """Generate a response from a raw prompt without context assembly."""
        provider = self._router.select_provider(
            complexity=COMPLEXITY_NORMAL,
            preferred_provider=preferred_provider,
        )
        return await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def generate_for_executive(
        self,
        exec_id: str,
        task_description: str,
        org_id: str = "",
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a response for an executive agent with strategic routing.

        Executives always get:
        - Strategic complexity routing (most powerful model)
        - Full memory context
        - Tool context
        - Executive-level system prompt
        """
        system_prompt = self.build_system_prompt(exec_id, org_id)
        prompt = self.assemble_prompt(
            agent_id=exec_id,
            task_description=task_description,
            org_id=org_id,
            additional_context=additional_context,
        )

        provider = self._router.select_provider(complexity=COMPLEXITY_STRATEGIC)
        return await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=8192,
        )

    # ── Provider Management ──────────────────────────────────────────────

    def get_provider(self) -> ModelProvider:
        """Return the default active provider (backward-compatible)."""
        return self._router.select_provider()

    def set_provider(self, provider: ModelProvider) -> None:
        """Override the model provider (for testing)."""
        self._router._providers["custom"] = provider

    def list_providers(self) -> List[Dict[str, Any]]:
        """Return info about all registered providers."""
        return self._router.list_available()