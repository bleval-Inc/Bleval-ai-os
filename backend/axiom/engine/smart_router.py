"""Smart Model Router — task-aware, multi-model intelligence dispatch.

Architecture
────────────
  Task Incoming
       ↓
  [Task Classifier] — analyses task, assigns category + complexity
       ↓
  [Priority Router] — picks best model based on category + availability
       ↓
  [Fallback Chain] — if primary fails, try next-best
       ↓
  [Provider Execution] — sends to the selected model

Task Categories
───────────────
  • STRATEGIC      — executive decisions, org planning, high-level reasoning
  • CODING         — code generation, review, architecture
  • LONG_CONTEXT   — document analysis, research, large-context reasoning
  • AGENTIC        — tool calling, workflow orchestration, multi-step tasks
  • CREATIVE       — content creation, marketing copy, brainstorming
  • ANALYSIS       — data analysis, performance review, pattern detection
  • GENERAL        — everyday conversation, quick queries

Model Assignments
─────────────────
  STRATEGIC     → GLM-5.2 (flagship reasoning + long-horizon planning)
  CODING        → Mistral Mamba MoE (1M context, code-optimised)
  LONG_CONTEXT  → Mistral Mamba MoE (1M context)
  AGENTIC       → GLM-5.2 or Stepfun MoE (agentic-optimised)
  CREATIVE      → NVIDIA General or Stepfun MoE
  ANALYSIS      → GLM-5.2 or Mistral Mamba MoE
  GENERAL       → NVIDIA General (fast, reliable)

Fallback Chain if primary fails:
  GLM-5.2 → Mistral Mamba → Stepfun MoE → NVIDIA General → Anthropic → OpenAI

Architecture Law 9: Intelligence is provider independent.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from axiom.config import settings
from axiom.engine.base import MockProvider, ModelProvider


# ═══════════════════════════════════════════════════════════════════════════
# Task Classification
# ═══════════════════════════════════════════════════════════════════════════


class TaskCategory(str, Enum):
    STRATEGIC = "strategic"
    CODING = "coding"
    LONG_CONTEXT = "long_context"
    AGENTIC = "agentic"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    GENERAL = "general"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    NORMAL = "normal"
    COMPLEX = "complex"
    STRATEGIC = "strategic"


@dataclass
class TaskProfile:
    """The result of analysing a task."""

    category: TaskCategory
    complexity: ComplexityLevel
    requires_tools: bool = False
    requires_memory: bool = False
    estimated_tokens: int = 0
    confidence: float = 0.0
    tags: List[str] = field(default_factory=list)


class TaskClassifier:
    """Analyse a task description to determine its category and complexity.

    Uses keyword analysis and heuristics to classify tasks without an
    LLM call — cheap, fast, predictable.
    """

    # ── Category Keywords ──────────────────────────────────────────────────

    STRATEGIC_PATTERNS = [
        r"\b(strateg(y|ic)|vision|mission|direction|objective|goal|priority|roadmap|plan|initiative|long.?term|quarter)\b",
        r"\b(executive|board|founder|leadership|decision|organi[sz]ation|department|review|oversight)\b",
        r"\b(resource.?allocation|budget|invest|growth|scale|partnership|acquisition)\b",
    ]

    CODING_PATTERNS = [
        r"\b(code|implement|function|class|api|endpoint|route|schema|type|interface|component)\b",
        r"\b(refactor|debug|test|build|compile|deploy|migration|schema|database|query)\b",
        r"\b(algorithm|data.?structure|pattern|architecture|dependency|version|commit|pr)\b",
    ]

    LONG_CONTEXT_PATTERNS = [
        r"\b(analyse|analyze|summarize|summarise|review|research|document|report|study)\b",
        r"\b(compare|contrast|evaluat|assess|investigat|comprehensiv|thorough|deep.?dive)\b",
        r"\b(contract|legal|policy|manual|handbook|specification|whitepaper|thesis)\b",
    ]

    AGENTIC_PATTERNS = [
        r"\b(workflow|orchestrat|delegat|dispatch|coordinat|launch|trigger|execut|run)\b",
        r"\b(automat|pipeline|task|agent|tool|function.?call|step|process|handler)\b",
        r"\b(schedule|cron|interval|event.?driven|webhook|callback|chain)\b",
    ]

    CREATIVE_PATTERNS = [
        r"\b(creat|write|draft|compose|generat|brainstorm|idea|content|copy|headline)\b",
        r"\b(design|brand|marketing|campaign|advert|social|post|email|newsletter|blog)\b",
        r"\b(story|narrativ|creative|art|image|video|audio|music|script|dialogue)\b",
    ]

    ANALYSIS_PATTERNS = [
        r"\b(analytics|metric|kpi|score|trend|pattern|insight|statistic|correlation)\b",
        r"\b(performance|efficien|optimize|benchmark|measure|track|monitor|dashboard)\b",
        r"\b(learning|score|pattern|recommend|predict|forecast|model|data|visuali[sz])\b",
    ]

    # ── Classification ────────────────────────────────────────────────────

    def classify(self, task_description: str, agent_id: str = "") -> TaskProfile:
        """Classify a task by analysing its description.

        Args:
            task_description: The task or prompt to classify
            agent_id: Optional agent ID for context (e.g. executives → strategic)

        Returns:
            A TaskProfile with the inferred category, complexity, and metadata
        """
        text = task_description.lower()

        # Agent-based bias: executive agents default to strategic
        if agent_id in ("jenson", "valta_prime", "yamako", "founder"):
            category = self._classify_agent_task(text, agent_id)
        else:
            category = self._classify_by_content(text)

        complexity = self._determine_complexity(text)
        requires_tools = self._check_tool_requirement(text)
        requires_memory = self._check_memory_requirement(text)
        estimated_tokens = self._estimate_tokens(text)

        return TaskProfile(
            category=category,
            complexity=complexity,
            requires_tools=requires_tools,
            requires_memory=requires_memory,
            estimated_tokens=estimated_tokens,
            confidence=0.8,
            tags=self._extract_tags(text),
        )

    def _classify_agent_task(self, text: str, agent_id: str) -> TaskCategory:
        """Classify tasks for executive agents.

        Executives get strategic routing by default, but we still
        check for specific task types.
        """
        # Check for coding
        if any(re.search(p, text) for p in self.CODING_PATTERNS):
            return TaskCategory.CODING
        # Check for creative
        if any(re.search(p, text) for p in self.CREATIVE_PATTERNS):
            return TaskCategory.CREATIVE
        # Check for analysis
        if any(re.search(p, text) for p in self.ANALYSIS_PATTERNS):
            return TaskCategory.ANALYSIS
        # Check for long-context
        if any(re.search(p, text) for p in self.LONG_CONTEXT_PATTERNS):
            return TaskCategory.LONG_CONTEXT
        # Check for agentic
        if any(re.search(p, text) for p in self.AGENTIC_PATTERNS):
            return TaskCategory.AGENTIC

        # Default: strategic for executives
        return TaskCategory.STRATEGIC

    def _classify_by_content(self, text: str) -> TaskCategory:
        """Classify a non-executive task by content analysis."""
        scores: Dict[TaskCategory, int] = {cat: 0 for cat in TaskCategory}

        patterns = {
            TaskCategory.STRATEGIC: self.STRATEGIC_PATTERNS,
            TaskCategory.CODING: self.CODING_PATTERNS,
            TaskCategory.LONG_CONTEXT: self.LONG_CONTEXT_PATTERNS,
            TaskCategory.AGENTIC: self.AGENTIC_PATTERNS,
            TaskCategory.CREATIVE: self.CREATIVE_PATTERNS,
            TaskCategory.ANALYSIS: self.ANALYSIS_PATTERNS,
        }

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, text)
                scores[category] += len(matches)

        # Get the highest-scoring category
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[best] > 0:
            return best

        return TaskCategory.GENERAL

    def _determine_complexity(self, text: str) -> ComplexityLevel:
        """Determine task complexity based on length and content."""
        word_count = len(text.split())

        if word_count > 300:
            return ComplexityLevel.STRATEGIC
        if word_count > 100:
            return ComplexityLevel.COMPLEX
        if word_count > 30:
            return ComplexityLevel.NORMAL

        return ComplexityLevel.SIMPLE

    def _check_tool_requirement(self, text: str) -> bool:
        """Check if the task requires tool access."""
        tool_keywords = [
            "launch", "run workflow", "execute", "deploy", "dispatch",
            "call api", "send", "create", "schedule", "tool",
        ]
        return any(kw in text for kw in tool_keywords)

    def _check_memory_requirement(self, text: str) -> bool:
        """Check if the task requires memory access."""
        memory_keywords = [
            "remember", "recall", "memory", "history", "previous",
            "context", "learn", "knowledge", "store", "know",
        ]
        return any(kw in text for kw in memory_keywords)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars ≈ 1 token)."""
        return len(text) // 4

    def _extract_tags(self, text: str) -> List[str]:
        """Extract meaningful tags from the task description."""
        tags = []
        keywords = {
            "code": "coding",
            "write": "writing",
            "plan": "planning",
            "review": "review",
            "analyse": "analysis",
            "create": "creation",
            "deploy": "deployment",
            "research": "research",
            "design": "design",
            "test": "testing",
        }
        for keyword, tag in keywords.items():
            if keyword in text:
                tags.append(tag)
        return tags


# ═══════════════════════════════════════════════════════════════════════════
# Smart Model Router
# ═══════════════════════════════════════════════════════════════════════════


class SmartRouter:
    """Task-aware model selection with priority routing and fallback chains.

    Analyses each incoming task and selects the optimal model based on:
      - Task category (strategic / coding / creative / etc.)
      - Model capability profile
      - Model availability (configured + API accessible)
      - Agent type (executives get strategic routing)

    If the primary model fails, falls back through the chain.
    In production mode (REAL_PROVIDERS_ONLY=true), mock provider is NEVER used.
    """

    def __init__(self) -> None:
        self._classifier = TaskClassifier()
        self._providers: Dict[str, ModelProvider] = {}
        self._nvidia_providers: List[ModelProvider] = []
        self._mock_provider = MockProvider()

    def register_provider(self, name: str, provider: ModelProvider) -> None:
        """Register a provider for routing."""
        self._providers[name] = provider

    def register_nvidia_provider(self, provider: ModelProvider) -> None:
        """Register an NVIDIA provider with priority-aware ordering."""
        self._nvidia_providers.append(provider)
        self._providers[provider.name] = provider

    def register_providers(self, providers: Dict[str, ModelProvider]) -> None:
        """Register multiple providers at once."""
        self._providers.update(providers)

    @property
    def providers(self) -> Dict[str, ModelProvider]:
        """Return all registered providers."""
        return dict(self._providers)

    @property
    def nvidia_providers(self) -> List[ModelProvider]:
        """Return all registered NVIDIA providers, sorted by priority."""
        return list(self._nvidia_providers)

    @property
    def has_real_provider(self) -> bool:
        """Whether any real (non-mock) provider is registered."""
        return any(
            not isinstance(p, MockProvider)
            for p in self._providers.values()
        )

    # ── Priority Model Maps ──────────────────────────────────────────────

    def _get_priority_chain(self, category: TaskCategory, agent_id: str = "") -> List[str]:
        """Get the ordered priority chain of provider names for a task category.

        Returns a list of provider names from best-match to worst-match.
        """
        # Map provider names to their labels (iterate over keys only)
        all_names = list(self._providers.keys())
        glm52_names = [n for n in all_names
                       if "glm52" in n.lower() or "glm" in n.lower() or "z-ai" in n.lower() or "zai" in n.lower()]
        mistral_names = [n for n in all_names
                         if "mistral" in n.lower() or "mamba" in n.lower()]
        stepfun_names = [n for n in all_names
                         if "stepfun" in n.lower() or "step" in n.lower()]
        general_nvidia = [n for n in all_names
                          if "general" in n.lower() or "nemotron" in n.lower()]

        glm52 = glm52_names[0] if glm52_names else None
        mistral = mistral_names[0] if mistral_names else None
        stepfun = stepfun_names[0] if stepfun_names else None
        general = general_nvidia[0] if general_nvidia else None

        # ── Priority Chains by Category ──────────────────────────────
        category_chains: Dict[TaskCategory, List[str]] = {
            TaskCategory.STRATEGIC: [
                glm52, mistral, stepfun, general,
            ],
            TaskCategory.CODING: [
                mistral, glm52, stepfun, general,
            ],
            TaskCategory.LONG_CONTEXT: [
                mistral, glm52, stepfun, general,
            ],
            TaskCategory.AGENTIC: [
                glm52, stepfun, mistral, general,
            ],
            TaskCategory.CREATIVE: [
                general, stepfun, glm52,
            ],
            TaskCategory.ANALYSIS: [
                glm52, mistral, stepfun, general,
            ],
            TaskCategory.GENERAL: [
                general, glm52, stepfun, mistral,
            ],
        }

        chain = category_chains.get(category, [
            glm52, mistral, stepfun, general,
        ])

        # Filter to only available providers, removing None entries
        return [
            name for name in chain
            if name and name in self._providers and self._providers[name].available
        ]

    # ── Routing ──────────────────────────────────────────────────────────

    def select_provider(
        self,
        task_description: str = "",
        task_profile: Optional[TaskProfile] = None,
        agent_id: str = "",
        preferred_provider: Optional[str] = None,
    ) -> ModelProvider:
        """Select the best provider for a given task with intelligent failover.

        Args:
            task_description: The task description to classify (if no profile)
            task_profile: A pre-classified task profile (skip classification)
            agent_id: The agent requesting intelligence (for context)
            preferred_provider: If set, try this provider first

        Returns:
            A ModelProvider instance.

        Raises:
            RuntimeError: If no real provider is available in production mode.
        """
        # If a specific provider is requested and available, use it
        if preferred_provider and preferred_provider in self._providers:
            provider = self._providers[preferred_provider]
            if provider.available:
                return provider

        # Classify the task if no profile provided
        profile = task_profile or self._classifier.classify(
            task_description, agent_id
        )

        # Get the priority chain for this category
        chain = self._get_priority_chain(profile.category, agent_id)

        # Return the best available provider from the chain (real providers only)
        for name in chain:
            provider = self._providers.get(name)
            if provider and provider.available and not isinstance(provider, MockProvider):
                return provider

        # Fallback: any real provider (NVIDIA-only)
        for provider in self._providers.values():
            if provider.available and not isinstance(provider, MockProvider):
                return provider

        # In production mode, NEVER fall back to mock
        if settings.real_providers_only or not settings.debug:
            raise RuntimeError(
                "No real AI provider available. "
                "Configure at least one NVIDIA provider API key "
                "or set REAL_PROVIDERS_ONLY=false for development."
            )

        # Last resort: mock provider (only in development)
        return self._mock_provider

    def select_provider_for_complexity(self, complexity: str) -> ModelProvider:
        """Legacy compatibility: select provider by complexity only.

        Maps complexity levels to the best general-purpose model.
        """
        category_map = {
            "simple": TaskCategory.GENERAL,
            "normal": TaskCategory.GENERAL,
            "complex": TaskCategory.ANALYSIS,
            "strategic": TaskCategory.STRATEGIC,
        }
        category = category_map.get(complexity, TaskCategory.GENERAL)
        return self.select_provider(
            task_profile=TaskProfile(category=category, complexity=ComplexityLevel(complexity))
        )

    # ── Information ──────────────────────────────────────────────────────

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Return information about all registered providers."""
        result = []
        for name, provider in self._providers.items():
            info = {
                "name": name,
                "available": provider.available,
                "type": type(provider).__name__,
            }
            # Add NVIDIA-specific metadata
            if hasattr(provider, "label"):
                info["label"] = provider.label
            if hasattr(provider, "role"):
                info["role"] = provider.role
            if hasattr(provider, "model_id"):
                info["model"] = provider.model_id
            if hasattr(provider, "provider_name"):
                info["provider"] = provider.provider_name
            result.append(info)
        return result

    def get_route_for_task(self, task_description: str, agent_id: str = "") -> Dict[str, Any]:
        """Analyse a task and show which model would handle it.

        Useful for debugging and transparency.
        """
        profile = self._classifier.classify(task_description, agent_id)
        provider = self.select_provider(task_profile=profile, agent_id=agent_id)

        return {
            "task_category": profile.category.value,
            "complexity": profile.complexity.value,
            "estimated_tokens": profile.estimated_tokens,
            "requires_tools": profile.requires_tools,
            "requires_memory": profile.requires_memory,
            "selected_provider": provider.name if hasattr(provider, "name") else type(provider).__name__,
            "available_providers": self.get_available_providers(),
        }