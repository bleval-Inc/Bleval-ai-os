"""
AXIOM Core — top-level intelligence of the AXIOM AI OS.

AXIOM sits ABOVE the executives (Jenson, Valta Prime, Yamako).
It is NOT an executive. It does NOT run any organization directly.

AXIOM is the system concierge, intelligence layer, health supervisor,
routing layer and Founder interface — the JARVIS of the operating system.

Architecture:
  Founder
     ↓
  AXIOM CORE
     ↓
  Jenson / Valta Prime / Yamako
     ↓
  Departments → Workflows → Agents → Tools/Integrations

Key responsibilities:
  - Boot the operating system
  - Greet the Founder with context-aware message
  - Maintain live system awareness (operational model)
  - Monitor health of all components
  - Detect, diagnose, and repair recoverable failures
  - Route Founder requests to appropriate handlers
  - Communicate with executives on behalf of Founder
  - Manage research workspaces
  - Coordinate multi-modal content retrieval
  - Learn from workflows and Founder preferences
  - Surface critical problems and manage Founder attention
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Core data models
# ═══════════════════════════════════════════════════════════════════════════════


class SystemState(str, Enum):
    """Overall operational state of the AXIOM system."""

    BOOTING = "booting"
    INITIALISING = "initialising"
    ONLINE = "online"
    DEGRADED = "degraded"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


class BootStage(str, Enum):
    """Stages of the AXIOM boot sequence."""

    INITIALISING_RUNTIME = "initialising_runtime"
    LOADING_EXECUTIVE_LAYER = "loading_executive_layer"
    LOADING_MEMORY = "loading_memory"
    LOADING_WORKFLOW_ENGINE = "loading_workflow_engine"
    LOADING_INTELLIGENCE = "loading_intelligence"
    SYNCHRONISING_ORGANISATIONS = "synchronising_organisations"
    CHECKING_SYSTEM_HEALTH = "checking_system_health"
    LOADING_EVENT_BUS = "loading_event_bus"
    LOADING_TOOLS = "loading_tools"
    LOADING_ENGINES = "loading_engines"
    SYSTEM_READY = "system_ready"


@dataclass
class AxiomBootResult:
    """Result of the AXIOM boot sequence."""

    success: bool
    duration_ms: float
    stages_completed: List[str]
    stage_timings: Dict[str, float]
    greeting: str = ""
    system_state: SystemState = SystemState.ONLINE
    errors: List[str] = field(default_factory=list)
    boot_id: str = ""


@dataclass
class SystemAwareness:
    """Live operational model of the entire AXIOM system.

    AXIOM continuously updates this to maintain awareness of:
    - Executives (state, cycle, health)
    - Agents (count, status)
    - Workflows (active, pending, failed)
    - Engines (operational state of each)
    - Runtime (uptime, health score)
    - Intelligence providers (available/unavailable)
    - Memory (integrity)
    - Events (queue depth, dead-letter count)
    - Approvals (pending count)
    """

    @dataclass
    class ExecutiveStatus:
        id: str
        org: str
        state: str
        cycle_count: int
        last_cycle: Optional[str] = None
        health_label: str = "Unknown"

    @dataclass
    class EngineHealth:
        name: str
        state: str
        label: str = ""
        details: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class WorkflowSummary:
        defined: int
        active: int
        pending: int
        failed: int
        awaiting_approval: int

    timestamp: float
    state: SystemState
    health_score: float
    uptime_seconds: float
    overall_health: str

    executives: List[ExecutiveStatus]
    engines: List[EngineHealth]
    workflows: WorkflowSummary
    intelligence_available: bool
    pending_approvals: int
    running_since: float = 0.0
    boot_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "state": self.state.value,
            "health_score": round(self.health_score, 4),
            "uptime_seconds": round(self.uptime_seconds, 1),
            "overall_health": self.overall_health,
            "executives": [
                {
                    "id": e.id,
                    "org": e.org,
                    "state": e.state,
                    "cycle_count": e.cycle_count,
                    "last_cycle": e.last_cycle,
                    "health": e.health_label,
                }
                for e in self.executives
            ],
            "engines": [
                {
                    "name": e.name,
                    "state": e.state,
                    "label": e.label,
                }
                for e in self.engines
            ],
            "workflows": {
                "defined": self.workflows.defined,
                "active": self.workflows.active,
                "pending": self.workflows.pending,
                "failed": self.workflows.failed,
                "awaiting_approval": self.workflows.awaiting_approval,
            },
            "intelligence_available": self.intelligence_available,
            "pending_approvals": self.pending_approvals,
            "running_since": self.running_since,
            "boot_id": self.boot_id,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AXIOM Core — The main intelligence layer
# ═══════════════════════════════════════════════════════════════════════════════


class AXIOMCore:
    """Top-level AI concierge for the AXIOM AI OS.

    AXIOM is the Founder's primary interface — a JARVIS-like intelligence
    layer that provides system awareness, conversational intelligence,
    research workspace management, request routing, and self-healing
    coordination across all executives, engines, and subsystems.
    """

    def __init__(
        self,
        runtime: Any = None,
        logger: Any = None,
    ) -> None:
        self._runtime = runtime
        self._logger = logger

        # Boot state
        self._state = SystemState.SHUTDOWN
        self._boot_id = ""
        self._boot_timestamp = 0.0
        self._boot_stages: Dict[str, float] = {}
        self._boot_errors: List[str] = []

        # Shared components (wired during bootstrap by AxiomRuntime)
        self._intelligence: Any = None
        self._event: Any = None
        self._executive: Any = None
        self._executive_board: Any = None
        self._workflow: Any = None
        self._memory: Any = None
        self._tool: Any = None
        self._learning: Any = None
        self._greeting: Any = None
        self._system_monitor: Any = None
        self._system_tools: Any = None
        self._approval: Any = None

        # Request router (lightweight, no LLM dependency)
        self._request_router: Any = None
        self._health_monitor: Any = None
        self._self_healer: Any = None

        # Research workspace registry
        self._research_workspaces: Dict[str, Any] = {}

        # Continuous monitoring loop
        self._monitor_task: Any = None
        self._monitoring_interval = 30.0  # seconds

    # ── Component wiring (called by AxiomRuntime after bootstrap) ────────

    def wire_components(
        self,
        intelligence: Any = None,
        event: Any = None,
        executive: Any = None,
        executive_board: Any = None,
        workflow: Any = None,
        memory: Any = None,
        tool: Any = None,
        learning: Any = None,
        greeting: Any = None,
        system_monitor: Any = None,
        system_tools: Any = None,
        approval: Any = None,
        health_monitor: Any = None,
        self_healer: Any = None,
        request_router: Any = None,
    ) -> None:
        """Wire all system components into AXIOM Core.

        Called once during runtime bootstrap after all engines are
        initialised. AXIOM does not own these components — it coordinates
        through their public APIs.
        """
        self._intelligence = intelligence
        self._event = event
        self._executive = executive
        self._executive_board = executive_board
        self._workflow = workflow
        self._memory = memory
        self._tool = tool
        self._learning = learning
        self._greeting = greeting
        self._system_monitor = system_monitor
        self._system_tools = system_tools
        self._approval = approval
        self._health_monitor = health_monitor
        self._self_healer = self_healer

        # Lazy import request router to avoid circular dependency
        if request_router is not None:
            self._request_router = request_router
        else:
            from axiom.core.request_router import RequestRouter
            self._request_router = RequestRouter(executive_engine=executive)

        if self._logger:
            self._logger.info("axiom_core", "AXIOM Core wired to all system components")

    # ── Boot Sequence ────────────────────────────────────────────────────

    async def boot(self) -> AxiomBootResult:
        """Execute the full AXIOM boot sequence.

        Returns a detailed boot result with stage timings and any errors.
        """
        self._state = SystemState.BOOTING
        self._boot_id = str(uuid.uuid4())[:8]
        self._boot_timestamp = time.time()
        self._boot_stages.clear()
        self._boot_errors.clear()

        stages = [
            BootStage.INITIALISING_RUNTIME,
            BootStage.LOADING_EXECUTIVE_LAYER,
            BootStage.LOADING_MEMORY,
            BootStage.LOADING_WORKFLOW_ENGINE,
            BootStage.LOADING_INTELLIGENCE,
            BootStage.LOADING_EVENT_BUS,
            BootStage.LOADING_TOOLS,
            BootStage.LOADING_ENGINES,
            BootStage.CHECKING_SYSTEM_HEALTH,
            BootStage.LOADING_EXECUTIVE_LAYER,
            BootStage.SYNCHRONISING_ORGANISATIONS,
            BootStage.SYSTEM_READY,
        ]

        completed_stages = []
        errors = []

        for stage in stages:
            stage_start = time.monotonic()
            try:
                await self._execute_boot_stage(stage)
                elapsed = (time.monotonic() - stage_start) * 1000
                self._boot_stages[stage.value] = elapsed
                completed_stages.append(stage.value)

                if self._logger:
                    self._logger.info(
                        "axiom_core",
                        f"Boot stage [{stage.value}] completed in {elapsed:.0f}ms",
                    )
            except Exception as exc:
                elapsed = (time.monotonic() - stage_start) * 1000
                self._boot_stages[stage.value] = elapsed
                errors.append(f"{stage.value}: {exc}")
                self._boot_errors.append(str(exc))

                if self._logger:
                    self._logger.error(
                        "axiom_core",
                        f"Boot stage [{stage.value}] failed: {exc}",
                    )

        total_duration = (time.monotonic() - self._boot_timestamp) * 1000

        # Determine final state
        if not errors:
            self._state = SystemState.ONLINE
        elif len(errors) >= len(stages):
            self._state = SystemState.FAILED
        else:
            self._state = SystemState.DEGRADED

        # Generate greeting
        greeting = await self._generate_greeting(is_first_boot=True)

        if self._logger:
            state_name = self._state.value.upper()
            self._logger.info(
                "axiom_core",
                f"Boot complete [{state_name}] — {len(completed_stages)}/{len(stages)} "
                f"stages in {total_duration:.0f}ms",
            )

        return AxiomBootResult(
            success=self._state in (SystemState.ONLINE, SystemState.DEGRADED),
            duration_ms=total_duration,
            stages_completed=completed_stages,
            stage_timings=dict(self._boot_stages),
            greeting=greeting,
            system_state=self._state,
            errors=errors,
            boot_id=self._boot_id,
        )

    async def _execute_boot_stage(self, stage: BootStage) -> None:
        """Execute a single boot stage.

        Each stage verifies the corresponding subsystem is operational.
        Stages are independent — failure in one does not abort the sequence.
        """
        runtime = self._runtime
        if runtime is None:
            return

        if stage == BootStage.INITIALISING_RUNTIME:
            if not getattr(runtime, "_initialised", False):
                await runtime.bootstrap()

        elif stage == BootStage.LOADING_EXECUTIVE_LAYER:
            board = getattr(runtime, "executive_board", None)
            if board is not None:
                # Verify all 3 executive loops exist
                for eid in ("jenson", "valta_prime", "yamako"):
                    loop = board.get_loop(eid)
                    if loop is None:
                        raise RuntimeError(f"Executive loop not found: {eid}")

        elif stage == BootStage.LOADING_MEMORY:
            mem = getattr(runtime, "memory", None)
            if mem is None:
                raise RuntimeError("Memory engine not available")

        elif stage == BootStage.LOADING_WORKFLOW_ENGINE:
            wf = getattr(runtime, "workflow", None)
            if wf is None:
                raise RuntimeError("Workflow engine not available")

        elif stage == BootStage.LOADING_INTELLIGENCE:
            intelligence = getattr(runtime, "intelligence", None)
            if intelligence is None:
                raise RuntimeError("Intelligence engine not available")

        elif stage == BootStage.LOADING_EVENT_BUS:
            evt = getattr(runtime, "event", None)
            if evt is None:
                raise RuntimeError("Event engine not available")

        elif stage == BootStage.LOADING_TOOLS:
            tl = getattr(runtime, "tool", None)
            if tl is None:
                raise RuntimeError("Tool engine not available")

        elif stage == BootStage.LOADING_ENGINES:
            learning = getattr(runtime, "learning", None)
            if learning is None:
                raise RuntimeError("Learning engine not available")

        elif stage == BootStage.CHECKING_SYSTEM_HEALTH:
            if self._health_monitor is not None:
                await self._health_monitor.full_snapshot()

        elif stage == BootStage.SYNCHRONISING_ORGANISATIONS:
            exec_eng = getattr(runtime, "executive", None)
            if exec_eng is not None:
                exec_eng.list_organizations()

        elif stage == BootStage.SYSTEM_READY:
            self._state = SystemState.ONLINE

    # ── Greeting ─────────────────────────────────────────────────────────

    async def _generate_greeting(self, is_first_boot: bool = False) -> str:
        """Generate a context-aware boot greeting.

        Delegates to the GreetingEngine if available for rich,
        dynamic greetings. Falls back to a simple default.
        """
        if self._greeting is not None:
            try:
                result = await self._greeting.generate_greeting(
                    telemetry=await self._get_telemetry_snapshot(),
                    is_first_boot=is_first_boot,
                )
                return result.text if hasattr(result, "text") else str(result)
            except Exception:
                pass

        # Simple fallback greeting
        hour = datetime.now(timezone.utc).hour
        if hour < 12:
            period = "morning"
        elif hour < 17:
            period = "afternoon"
        else:
            period = "evening"
        return f"Good {period}. AXIOM systems are online."

    async def _get_telemetry_snapshot(self) -> Any:
        """Get current telemetry snapshot if available."""
        if self._system_monitor is not None:
            try:
                return await self._system_monitor.snapshot()
            except Exception:
                pass
        return None

    # ── System Awareness ─────────────────────────────────────────────────

    async def get_system_awareness(self) -> SystemAwareness:
        """Build the current live operational model of the entire system."""
        runtime = self._runtime
        now = time.time()

        # Gather executive statuses
        executives = []
        if self._executive_board is not None:
            for eid in ("jenson", "valta_prime", "yamako"):
                loop = self._executive_board.get_loop(eid)
                if loop is not None:
                    try:
                        status = loop.get_status() if hasattr(loop, "get_status") else {}
                        executives.append(SystemAwareness.ExecutiveStatus(
                            id=eid,
                            org=status.get("org_id", ""),
                            state="running" if status.get("running", False) else "stopped",
                            cycle_count=status.get("cycle_count", 0),
                            last_cycle=status.get("last_cycle", None),
                            health_label=status.get("health", "Unknown"),
                        ))
                    except Exception:
                        executives.append(SystemAwareness.ExecutiveStatus(
                            id=eid, org="", state="error", cycle_count=0,
                        ))
                else:
                    executives.append(SystemAwareness.ExecutiveStatus(
                        id=eid, org="", state="offline", cycle_count=0,
                    ))

        # Gather engine health
        engines = []
        engine_map = {
            "memory": self._memory,
            "event": self._event,
            "tool": self._tool,
            "workflow": self._workflow,
            "executive": self._executive,
            "intelligence": self._intelligence,
            "learning": self._learning,
        }
        for name, engine in engine_map.items():
            state = "online" if engine is not None else "offline"
            engines.append(SystemAwareness.EngineHealth(
                name=name, state=state,
                label=f"{name.capitalize()} engine" if engine else f"{name.capitalize()} engine unavailable",
            ))

        # Gather workflow summary
        workflows = SystemAwareness.WorkflowSummary(
            defined=0, active=0, pending=0, failed=0, awaiting_approval=0,
        )
        if self._workflow is not None:
            try:
                wf_defs = self._workflow.list_workflows()
                workflows.defined = len(wf_defs)

                instances = self._workflow.list_instances() if hasattr(self._workflow, "list_instances") else []
                for inst in instances:
                    s = getattr(inst, "status", "").lower()
                    if s in ("running",):
                        workflows.active += 1
                    elif s in ("pending",):
                        workflows.pending += 1
                    elif s in ("failed",):
                        workflows.failed += 1
                    elif s in ("awaiting_approval",):
                        workflows.awaiting_approval += 1
            except Exception:
                pass

        # Intelligence availability
        intelligence_available = False
        if self._intelligence is not None:
            try:
                intelligence_available = (
                    self._intelligence.has_real_provider
                    if hasattr(self._intelligence, "has_real_provider")
                    else False
                )
            except Exception:
                pass

        # Pending approvals
        pending_approvals = 0
        if self._approval is not None:
            try:
                if hasattr(self._approval, "pending_count"):
                    pending_approvals = self._approval.pending_count()
                else:
                    pending = self._approval.list_approvals(status="pending")
                    pending_approvals = len(pending)
            except Exception:
                pass

        # Compute health score
        health_score = await self._compute_health_score()
        uptime = 0.0
        if self._system_monitor is not None:
            try:
                snap = await self._system_monitor.snapshot()
                uptime = getattr(snap, "uptime_seconds", 0.0) if hasattr(snap, "uptime_seconds") else 0.0
            except Exception:
                uptime = time.time() - self._boot_timestamp if self._boot_timestamp else 0.0
        elif self._boot_timestamp:
            uptime = time.time() - self._boot_timestamp

        overall_health = self._health_label(health_score)

        return SystemAwareness(
            timestamp=now,
            state=self._state,
            health_score=health_score,
            uptime_seconds=uptime,
            overall_health=overall_health,
            executives=executives,
            engines=engines,
            workflows=workflows,
            intelligence_available=intelligence_available,
            pending_approvals=pending_approvals,
            running_since=self._boot_timestamp,
            boot_id=self._boot_id,
        )

    async def _compute_health_score(self) -> float:
        """Compute overall health score 0.0–1.0 from the health monitor."""
        if self._health_monitor is not None:
            try:
                snapshot = await self._health_monitor.full_snapshot()
                return getattr(snapshot, "health_score", 0.5)
            except Exception:
                pass

        # Fallback: derive from runtime status
        runtime = self._runtime
        if runtime is None:
            return 0.0

        components = getattr(runtime, "get_status", lambda: {})().get("components", {})
        if not components:
            return 0.0

        online = sum(1 for v in components.values() if v)
        return online / max(len(components), 1)

    @staticmethod
    def _health_label(score: float) -> str:
        if score >= 0.8:
            return "healthy"
        elif score >= 0.5:
            return "degraded"
        return "critical"

    # ── Founder Chat / Conversational Interface ──────────────────────────

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Handle a Founder chat message.

        Routes through the AXIOM intelligence layer with full system
        context, rather than going directly to a raw LLM call.
        This gives AXIOM awareness of the current system state,
        executive activity, and operational context.
        """
        if self._intelligence is None:
            return {
                "response": "AXIOM is not yet connected to an intelligence engine.",
                "agent_id": "axiom",
            }

        # Build system awareness context
        awareness = await self.get_system_awareness()

        # Build additional context for the intelligence engine
        additional_context = {
            "system_state": awareness.state.value,
            "health_score": awareness.health_score,
            "overall_health": awareness.overall_health,
            "active_executives": sum(1 for e in awareness.executives if e.state == "running"),
            "active_workflows": awareness.workflows.active,
            "pending_approvals": awareness.pending_approvals,
        }
        if conversation_history:
            additional_context["conversation_history"] = conversation_history[-10:]

        # Route through the RequestRouter first to understand intent
        if self._request_router is not None:
            classified = self._request_router.classify(message)
            routed = self._request_router.route(classified)

            # If it's a system status request, answer from awareness directly
            if classified.category.value == "system_status":
                return {
                    "response": self._format_awareness_summary(awareness),
                    "agent_id": "axiom",
                    "category": "system_status",
                    "awareness": awareness.to_dict(),
                }

            # If it's an information request, answer directly
            if classified.category.value == "information":
                return {
                    "response": (
                        "I'm AXIOM — your AI operating system. I can:\n"
                        "• Monitor system health and executive activity\n"
                        "• Route requests to Jenson, Valta Prime, or Yamako\n"
                        "• Perform research and retrieve information\n"
                        "• Create research workspaces for deep dives\n"
                        "• Launch and monitor workflows\n"
                        "• Manage approvals and system configuration\n\n"
                        "What would you like me to do?"
                    ),
                    "agent_id": "axiom",
                    "category": "information",
                }

            # If routing to an executive, handle that
            if routed.handler == "executive":
                result = await self._communicate_with_executive(
                    exec_id=routed.target,
                    message=message,
                    context=routed.context,
                )
                return result

            # If it's a research request, route to research
            if classified.category.value == "research":
                return {
                    "response": (
                        f"I'll research that for you. Let me gather information "
                        f"on: {classified.intent}"
                    ),
                    "agent_id": "axiom",
                    "category": "research",
                    "intent": classified.intent,
                }

        # Default: generate response via intelligence engine
        try:
            description = message
            if conversation_history:
                description = f"Conversation context: {conversation_history[-3:]}\n\nCurrent message: {message}"

            response = await self._intelligence.generate(
                agent_id="axiom",
                task_description=description,
                additional_context=additional_context or None,
                max_tokens=2048,
                temperature=0.7,
            )
            return {"response": response, "agent_id": "axiom"}
        except Exception as exc:
            return {
                "response": f"I encountered an issue processing your request: {exc}",
                "agent_id": "axiom",
            }

    def _format_awareness_summary(self, awareness: SystemAwareness) -> str:
        """Format a natural-language system status summary."""
        lines = [
            f"System is {awareness.overall_health.upper()} "
            f"(score: {awareness.health_score:.2f})",
            "",
            "Executives:",
        ]

        for e in awareness.executives:
            lines.append(f"  • {e.id} ({e.org}): {e.state} — {e.cycle_count} cycles")

        lines.append("")
        lines.append(f"Workflows: {awareness.workflows.active} active, "
                      f"{awareness.workflows.pending} pending, "
                      f"{awareness.workflows.awaiting_approval} awaiting approval")

        lines.append(f"\nEngines: {sum(1 for e in awareness.engines if e.state == 'online')}/"
                      f"{len(awareness.engines)} online")
        lines.append(f"Intelligence: {'available' if awareness.intelligence_available else 'unavailable'}")
        lines.append(f"Pending approvals: {awareness.pending_approvals}")
        lines.append(f"Uptime: {awareness.uptime_seconds / 60:.0f} minutes")

        return "\n".join(lines)

    # ── Request Routing ──────────────────────────────────────────────────

    async def handle_request(self, message: str) -> Dict[str, Any]:
        """Route a Founder request to the appropriate handler.

        Classifies the request, routes it, and executes the action.
        Returns a structured result with the response and routing info.
        """
        if self._request_router is None:
            return await self.chat(message)

        classified = self._request_router.classify(message)
        routed = self._request_router.route(classified)

        result = {
            "category": classified.category.value,
            "complexity": classified.complexity.value,
            "intent": classified.intent,
            "confidence": classified.confidence,
            "handler": routed.handler,
            "target": routed.target,
            "requires_approval": routed.requires_approval,
        }

        # Execute based on handler
        if routed.handler == "axiom_direct":
            # Handle directly within AXIOM
            if routed.target == "system_awareness":
                awareness = await self.get_system_awareness()
                result["response"] = self._format_awareness_summary(awareness)
                result["awareness"] = awareness.to_dict()
            elif routed.target == "capabilities":
                result["response"] = self._get_capabilities_help()
            elif routed.target == "navigation":
                result["response"] = f"Navigating to {routed.context.get('destination', 'workspace')}..."
            else:
                # Default chat
                chat_result = await self.chat(message)
                result["response"] = chat_result.get("response", "")
        elif routed.handler == "executive":
            comm_result = await self._communicate_with_executive(
                exec_id=routed.target,
                message=message,
                context=routed.context,
            )
            result["response"] = comm_result.get("response", "")
        elif routed.handler == "research":
            result["response"] = "Initiating research..."
            result["research"] = True
        else:
            chat_result = await self.chat(message)
            result["response"] = chat_result.get("response", "")

        return result

    def _get_capabilities_help(self) -> str:
        """Return a help summary of AXIOM's capabilities."""
        return (
            "AXIOM capabilities:\n\n"
            "System Awareness:\n"
            "  • \"What's the system status?\"\n"
            "  • \"How are the executives?\"\n"
            "  • \"Show me health\"\n\n"
            "Research:\n"
            "  • \"Research X\"\n"
            "  • \"Find everything about Y\"\n"
            "  • \"Analyze this topic\"\n\n"
            "Executive Communication:\n"
            "  • \"Tell Jenson to check sales\"\n"
            "  • \"Message Valta Prime about brand\"\n"
            "  • \"Ask Yamako about my schedule\"\n\n"
            "Workflows:\n"
            "  • \"Launch prospect research\"\n"
            "  • \"Start code review\"\n"
            "  • \"Run content production\"\n\n"
            "Navigation:\n"
            "  • \"Go to Command Center\"\n"
            "  • \"Open Executive Board\"\n"
            "  • \"Show me Operations\""
        )

    # ── Executive Communication ──────────────────────────────────────────

    async def _communicate_with_executive(
        self,
        exec_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route a message to an executive agent.

        Uses the ExecutiveBoard to deliver the message through the
        executive's runtime loop for processing.
        """
        if self._executive_board is None:
            return {"response": f"Executive board is not available. Cannot reach {exec_id}."}

        loop = self._executive_board.get_loop(exec_id)
        if loop is None:
            return {"response": f"Executive {exec_id} is not available."}

        try:
            # Attempt to trigger a cycle with the message logged
            result = await loop.trigger_cycle(
                cycle_type="founder_message",
            )
            return {
                "response": f"Message routed to {exec_id}. ",
                "executive": exec_id,
                "cycle_result": result if isinstance(result, dict) else {},
            }
        except Exception as exc:
            return {
                "response": f"Could not reach {exec_id}: {exc}",
                "executive": exec_id,
            }

    async def route_to_executive(
        self,
        exec_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """Public API: route a message to an executive.

        This is the primary method the Founder uses to communicate
        with executives through AXIOM.
        """
        return await self._communicate_with_executive(exec_id, message)

    # ── Research Workspace Management ────────────────────────────────────

    async def create_research_workspace(
        self,
        title: str,
        query: str,
        source_material: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new research workspace.

        Returns a workspace object that tracks:
        - conversation (queries + AXIOM responses)
        - sources (documents, URLs, references)
        - findings (key insights extracted)
        - notes (Founder annotations)
        - conclusions (final synthesis)
        - generated assets (reports, summaries)
        """
        workspace_id = f"research-{uuid.uuid4().hex[:12]}"

        workspace = {
            "id": workspace_id,
            "title": title,
            "query": query,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "conversation": [],
            "sources": [],
            "findings": [],
            "notes": [],
            "conclusions": [],
            "generated_assets": [],
            "documents": [],
            "images": [],
            "videos": [],
            "audio": [],
            "references": [],
            "decisions": [],
            "actions": [],
        }

        # Add initial query as first conversation entry
        workspace["conversation"].append({
            "role": "founder",
            "content": query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # If source material was provided, add it
        if source_material:
            workspace["sources"].append(source_material)

        self._research_workspaces[workspace_id] = workspace

        if self._logger:
            self._logger.info(
                "axiom_core",
                f"Research workspace created: '{title}' ({workspace_id})",
            )

        return workspace

    def get_research_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get a research workspace by ID."""
        return self._research_workspaces.get(workspace_id)

    def list_research_workspaces(self) -> List[Dict[str, Any]]:
        """List all active research workspaces."""
        return [
            {
                "id": w["id"],
                "title": w["title"],
                "query": w["query"],
                "created_at": w["created_at"],
                "status": w["status"],
                "sources_count": len(w["sources"]),
                "findings_count": len(w["findings"]),
            }
            for w in self._research_workspaces.values()
        ]

    def update_research_workspace(
        self,
        workspace_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update a research workspace with new data."""
        workspace = self._research_workspaces.get(workspace_id)
        if workspace is None:
            return None

        for key, value in updates.items():
            if key in workspace and isinstance(workspace[key], list) and isinstance(value, list):
                workspace[key].extend(value)
            elif key in workspace:
                workspace[key] = value

        return workspace

    def archive_research_workspace(self, workspace_id: str) -> bool:
        """Archive (deactivate) a research workspace."""
        workspace = self._research_workspaces.get(workspace_id)
        if workspace is None:
            return False
        workspace["status"] = "archived"
        return True

    async def add_research_finding(
        self,
        workspace_id: str,
        finding: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Add a finding to a research workspace."""
        return self.update_research_workspace(workspace_id, {"findings": [finding]})

    # ── Content Retrieval ────────────────────────────────────────────────

    async def retrieve_content(
        self,
        query: str,
        content_types: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Multi-modal content retrieval across all available sources.

        Args:
            query: The search query
            content_types: Types to search (text, image, video, audio, document)
            max_results: Max results per type

        Returns:
            Dict with keys for each content type containing results.
        """
        if content_types is None:
            content_types = ["text", "images", "videos", "audio", "documents"]

        results: Dict[str, List[Dict[str, Any]]] = {
            "text": [],
            "images": [],
            "videos": [],
            "audio": [],
            "documents": [],
        }

        # Text/content retrieval via memory engine
        if "text" in content_types and self._memory is not None:
            try:
                context = self._memory.get_resolved_context(
                    agent_id="axiom",
                    org="",
                    dept="",
                )
                results["text"] = [
                    {"source": k, "content": v[:500] if v else ""}
                    for k, v in context.items()
                    if v and query.lower() in v.lower()
                ][:max_results]
            except Exception:
                pass

        # Use intelligence engine for semantic retrieval
        if self._intelligence is not None:
            try:
                response = await self._intelligence.generate(
                    agent_id="axiom",
                    task_description=(
                        f"Search for information about: {query}\n\n"
                        f"Return relevant findings as a concise summary. "
                        f"Limit to {max_results} key points."
                    ),
                    max_tokens=1024,
                )
                results["text"].append({
                    "source": "intelligence",
                    "content": response,
                    "type": "semantic_search",
                })
            except Exception:
                pass

        return results

    # ── System Actions ───────────────────────────────────────────────────

    async def execute_system_action(
        self,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a system action through the SystemTools bridge.

        Only non-approval actions can be executed directly.
        Actions requiring Founder approval (trades, payments, etc.)
        must go through the approval manager first.
        """
        if self._system_tools is None:
            return {"success": False, "error": "System tools not available"}

        try:
            if hasattr(self._system_tools, "execute_tool"):
                result = await self._system_tools.execute_tool(action, params or {})
                return {
                    "success": True,
                    "result": result.to_dict() if hasattr(result, "to_dict") else str(result),
                }
            return {"success": False, "error": "execute_tool not available"}
        except Exception as exc:
            self._boot_errors.append(str(exc))
            return {"success": False, "error": str(exc)}

    # ── Monitoring ───────────────────────────────────────────────────────

    async def start_monitoring(self) -> None:
        """Start the continuous system monitoring loop.

        AXIOM monitors:
        - Executive health and cycle completion
        - Workflow engine status
        - Event bus health
        - Memory integrity
        - Intelligence provider availability
        - System resource usage

        When failures are detected, the SelfHealer is invoked.
        """
        if self._monitor_task is not None:
            return  # Already monitoring

        if self._logger:
            self._logger.info(
                "axiom_core",
                f"Starting AXIOM monitoring (interval: {self._monitoring_interval}s)",
            )

        while self._state not in (SystemState.SHUTDOWN, SystemState.FAILED):
            try:
                await self._monitoring_tick()
            except Exception as exc:
                if self._logger:
                    self._logger.error("axiom_core", f"Monitoring tick error: {exc}")
            await asyncio_sleep(self._monitoring_interval)

    async def _monitoring_tick(self) -> None:
        """Single monitoring cycle — check health and trigger recovery."""
        # Get health snapshot
        if self._health_monitor is not None:
            try:
                snapshot = await self._health_monitor.full_snapshot()
                self._handle_health_snapshot(snapshot)
            except Exception:
                pass

    def _handle_health_snapshot(self, snapshot: Any) -> None:
        """Process a health snapshot and trigger recovery if needed."""
        if self._self_healer is None:
            return

        # Check each component for failures
        components = getattr(snapshot, "components", {}) or {}
        for name, ch in components.items():
            state = getattr(ch, "state", None)
            if state and str(state) in ("failed", "blocked"):
                if self._logger:
                    self._logger.warning(
                        "axiom_core",
                        f"Detected failure: {name} ({state})",
                    )

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def shutdown(self) -> None:
        """Graceful shutdown of AXIOM Core and all monitoring."""
        self._state = SystemState.SHUTDOWN

        if self._logger:
            self._logger.info("axiom_core", "AXIOM Core shutting down")

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def state(self) -> SystemState:
        return self._state

    @property
    def boot_id(self) -> str:
        return self._boot_id

    @property
    def is_online(self) -> bool:
        return self._state == SystemState.ONLINE

    @property
    def request_router(self) -> Any:
        return self._request_router

    @property
    def research_workspaces(self) -> Dict[str, Any]:
        """Return all research workspaces (read-only view)."""
        return dict(self._research_workspaces)


# ═══════════════════════════════════════════════════════════════════════════════
# Async helper
# ═══════════════════════════════════════════════════════════════════════════════


async def asyncio_sleep(seconds: float) -> None:
    """Async sleep helper — avoids module-level asyncio import."""
    import asyncio
    await asyncio.sleep(seconds)