"""
System Health Model -- live operational awareness for AXIOM Core.

Health states: ONLINE, DEGRADED, BLOCKED, FAILED, RECOVERING, OFFLINE

The SystemHealthMonitor polls every component group and produces a
SystemHealthSnapshot that the runtime, API, and self-healer use for
system awareness and autonomous recovery.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Health model
# ═══════════════════════════════════════════════════════════════════════════════


class HealthState(str, Enum):
    """Operational state of a system component or the system as a whole."""

    ONLINE = "online"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    FAILED = "failed"
    RECOVERING = "recovering"
    OFFLINE = "offline"


@dataclass
class ComponentHealth:
    """Health state of a single system component."""

    name: str
    state: HealthState
    label: str = "All systems nominal"
    details: Dict[str, Any] = field(default_factory=dict)
    last_checked: float = 0.0
    last_error: Optional[str] = None
    recovery_attempts: int = 0


@dataclass
class SystemHealthSnapshot:
    """Complete health model of the AXIOM system at a point in time."""

    timestamp: float
    overall: HealthState
    health_score: float  # 0.0-1.0
    components: Dict[str, ComponentHealth]  # keyed by component name

    # Component groups (convenience aliases)
    executives: Dict[str, ComponentHealth] = field(default_factory=dict)
    agents: ComponentHealth = field(default_factory=lambda: ComponentHealth(name="agents", state=HealthState.OFFLINE))
    workflows: ComponentHealth = field(
        default_factory=lambda: ComponentHealth(name="workflows", state=HealthState.OFFLINE)
    )
    events: ComponentHealth = field(default_factory=lambda: ComponentHealth(name="events", state=HealthState.OFFLINE))
    tools: ComponentHealth = field(default_factory=lambda: ComponentHealth(name="tools", state=HealthState.OFFLINE))
    memory: ComponentHealth = field(default_factory=lambda: ComponentHealth(name="memory", state=HealthState.OFFLINE))
    runtime: ComponentHealth = field(default_factory=lambda: ComponentHealth(name="runtime", state=HealthState.OFFLINE))
    intelligence_providers: ComponentHealth = field(
        default_factory=lambda: ComponentHealth(name="intelligence_providers", state=HealthState.OFFLINE)
    )

    # System metrics
    active_workflow_count: int = 0
    running_executive_count: int = 0
    pending_approval_count: int = 0
    uptime_seconds: float = 0.0

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full health snapshot to a dict for API responses."""
        return {
            "timestamp": self.timestamp,
            "overall": self.overall.value if isinstance(self.overall, HealthState) else str(self.overall),
            "health_score": round(self.health_score, 4),
            "components": {
                name: {
                    "name": ch.name,
                    "state": ch.state.value if isinstance(ch.state, HealthState) else str(ch.state),
                    "label": ch.label,
                    "details": ch.details,
                    "last_checked": ch.last_checked,
                    "last_error": ch.last_error,
                    "recovery_attempts": ch.recovery_attempts,
                }
                for name, ch in self.components.items()
            },
            "executives": {
                name: {
                    "state": ch.state.value if isinstance(ch.state, HealthState) else str(ch.state),
                    "label": ch.label,
                    "details": ch.details,
                    "last_error": ch.last_error,
                }
                for name, ch in self.executives.items()
            },
            "workflows": {
                "state": self.workflows.state.value if isinstance(self.workflows.state, HealthState) else str(self.workflows.state),
                "label": self.workflows.label,
                "details": self.workflows.details,
            },
            "events": {
                "state": self.events.state.value if isinstance(self.events.state, HealthState) else str(self.events.state),
                "label": self.events.label,
                "details": self.events.details,
            },
            "tools": {
                "state": self.tools.state.value if isinstance(self.tools.state, HealthState) else str(self.tools.state),
                "label": self.tools.label,
            },
            "memory": {
                "state": self.memory.state.value if isinstance(self.memory.state, HealthState) else str(self.memory.state),
                "label": self.memory.label,
            },
            "intelligence_providers": {
                "state": self.intelligence_providers.state.value
                if isinstance(self.intelligence_providers.state, HealthState)
                else str(self.intelligence_providers.state),
                "label": self.intelligence_providers.label,
                "details": self.intelligence_providers.details,
            },
            "runtime": {
                "state": self.runtime.state.value if isinstance(self.runtime.state, HealthState) else str(self.runtime.state),
                "label": self.runtime.label,
                "details": self.runtime.details,
            },
            "metrics": {
                "active_workflow_count": self.active_workflow_count,
                "running_executive_count": self.running_executive_count,
                "pending_approval_count": self.pending_approval_count,
                "uptime_seconds": round(self.uptime_seconds, 1),
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# System Health Monitor
# ═══════════════════════════════════════════════════════════════════════════════


class SystemHealthMonitor:
    """Monitors all system components and maintains live health state.

    Polls each component group and assigns health states.
    Used by AXIOM Core for system awareness and by SelfHealer for recovery.

    Checks:
      - 3 executives (jenson, valta_prime, yamako)   via executive_board.get_loop()
      - Agent engine                                    via executive.list_all_agents()
      - Workflow engine                                  via workflow.list_instances()
      - Event engine                                     via event.is_running
      - Tool engine                                      via tool state
      - Memory                                           via memory state
      - Runtime                                          via runtime.get_status()
      - Intelligence providers                           via intelligence.list_providers()
      - System metrics (CPU/RAM/disk)                    via system_monitor.snapshot()
    """

    HEALTHY_THRESHOLD = 0.8
    DEGRADED_THRESHOLD = 0.5

    def __init__(self, runtime: Any = None, logger: Any = None) -> None:
        self._runtime = runtime
        self._logger = logger
        self._components: Dict[str, ComponentHealth] = {}
        self._initialised = False

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def initialise(self) -> None:
        """Register all components and perform initial health check."""
        self._components.clear()
        self._initialised = True
        if self._logger:
            self._logger.info("system_health", "SystemHealthMonitor initialised")

    # ── Snapshot ───────────────────────────────────────────────────────────

    async def full_snapshot(self) -> SystemHealthSnapshot:
        """Take a complete health snapshot of all system components.

        Every check is wrapped in try/except so an error in one component
        never prevents the rest of the snapshot from completing.
        """
        now = time.time()
        runtime = self._runtime

        # Gather component checks in parallel semantics (sequential async is fine)
        executives = await self._check_executives()
        agents = await self._check_agents()
        workflows = await self._check_workflows()
        events = await self._check_events()
        tools = await self._check_tools()
        memory = await self._check_memory()
        runtime_health = await self._check_runtime()
        intelligence = await self._check_intelligence()
        system_metrics = await self._check_system_metrics()

        # Assemble the full components dict
        components: Dict[str, ComponentHealth] = {
            "executives": _aggregate_component("executives", executives),
            "agents": agents,
            "workflows": workflows,
            "events": events,
            "tools": tools,
            "memory": memory,
            "runtime": runtime_health,
            "intelligence_providers": intelligence,
            "system_metrics": system_metrics,
        }

        # Build snapshot
        snapshot = SystemHealthSnapshot(
            timestamp=now,
            overall=HealthState.OFFLINE,
            health_score=0.0,
            components=components,
            executives=executives,
            agents=agents,
            workflows=workflows,
            events=events,
            tools=tools,
            memory=memory,
            runtime=runtime_health,
            intelligence_providers=intelligence,
        )

        # Compute runtime metrics
        snapshot.active_workflow_count = self._get_active_workflow_count()
        snapshot.running_executive_count = sum(
            1 for ch in executives.values() if ch.state == HealthState.ONLINE
        )
        snapshot.pending_approval_count = self._get_pending_approval_count()
        snapshot.uptime_seconds = self._get_uptime()

        # Compute aggregate health
        snapshot.overall = self._compute_overall(snapshot)
        snapshot.health_score = self._compute_health_score(snapshot)

        return snapshot

    # ── Component checks ──────────────────────────────────────────────────

    async def _check_executives(self) -> Dict[str, ComponentHealth]:
        """Check health of all 3 executives via ExecutiveBoard."""
        results: Dict[str, ComponentHealth] = {}
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "executive_board") or runtime.executive_board is None:
            for eid in ("jenson", "valta_prime", "yamako"):
                results[eid] = ComponentHealth(
                    name=eid,
                    state=HealthState.OFFLINE,
                    label="Executive board not available",
                    last_checked=now,
                )
            return results

        board = runtime.executive_board
        for exec_id in getattr(board, "EXECUTIVE_IDS", ["jenson", "valta_prime", "yamako"]):
            try:
                loop = board.get_loop(exec_id)
                if loop is None:
                    results[exec_id] = ComponentHealth(
                        name=exec_id,
                        state=HealthState.OFFLINE,
                        label=f"Executive {exec_id} loop not created",
                        last_checked=now,
                    )
                    continue

                status = loop.get_status() if hasattr(loop, "get_status") else {}
                running = status.get("running", False)
                cycle_count = status.get("cycle_count", 0)

                if running:
                    results[exec_id] = ComponentHealth(
                        name=exec_id,
                        state=HealthState.ONLINE,
                        label=f"Executive {exec_id} running ({cycle_count} cycles)",
                        details={"running": True, "cycle_count": cycle_count, "org_id": status.get("org_id", "")},
                        last_checked=now,
                    )
                else:
                    results[exec_id] = ComponentHealth(
                        name=exec_id,
                        state=HealthState.DEGRADED,
                        label=f"Executive {exec_id} not running",
                        details={"running": False, "cycle_count": cycle_count},
                        last_checked=now,
                    )
            except Exception as exc:
                results[exec_id] = ComponentHealth(
                    name=exec_id,
                    state=HealthState.FAILED,
                    label=f"Executive {exec_id} check failed",
                    last_error=str(exc),
                    last_checked=now,
                )

        return results

    async def _check_agents(self) -> ComponentHealth:
        """Check agent engine health via ExecutiveEngine."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "executive") or runtime.executive is None:
            return ComponentHealth(
                name="agents", state=HealthState.OFFLINE,
                label="Agent engine not available", last_checked=now,
            )

        try:
            agents = runtime.executive.list_executives() if hasattr(runtime.executive, "list_executives") else []
            agent_count = len(agents)
            return ComponentHealth(
                name="agents",
                state=HealthState.ONLINE,
                label=f"{agent_count} agent(s) registered",
                details={"agent_count": agent_count},
                last_checked=now,
            )
        except Exception as exc:
            return ComponentHealth(
                name="agents", state=HealthState.FAILED,
                label="Agent engine check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_workflows(self) -> ComponentHealth:
        """Check workflow engine health and count instances."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "workflow") or runtime.workflow is None:
            return ComponentHealth(
                name="workflows", state=HealthState.OFFLINE,
                label="Workflow engine not available", last_checked=now,
            )

        try:
            instances = runtime.workflow.list_instances() if hasattr(runtime.workflow, "list_instances") else []
            active = sum(1 for i in instances if getattr(i, "status", None) in ("running", "RUNNING", "active", "ACTIVE"))
            total = len(instances)
            return ComponentHealth(
                name="workflows",
                state=HealthState.ONLINE,
                label=f"Workflow engine ready ({active} active, {total} total)",
                details={"active_instances": active, "total_instances": total},
                last_checked=now,
            )
        except Exception as exc:
            return ComponentHealth(
                name="workflows", state=HealthState.FAILED,
                label="Workflow engine check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_events(self) -> ComponentHealth:
        """Check event engine health."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "event") or runtime.event is None:
            return ComponentHealth(
                name="events", state=HealthState.OFFLINE,
                label="Event engine not available", last_checked=now,
            )

        try:
            engine = runtime.event
            running = getattr(engine, "_running", False)
            if running:
                channel_count = len(getattr(engine, "_queues", {}) or {})
                return ComponentHealth(
                    name="events",
                    state=HealthState.ONLINE,
                    label=f"Event engine running ({channel_count} channel(s))",
                    details={"channels": channel_count, "running": True},
                    last_checked=now,
                )
            else:
                return ComponentHealth(
                    name="events",
                    state=HealthState.DEGRADED,
                    label="Event engine not running",
                    details={"running": False},
                    last_checked=now,
                )
        except Exception as exc:
            return ComponentHealth(
                name="events", state=HealthState.FAILED,
                label="Event engine check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_tools(self) -> ComponentHealth:
        """Check tool engine health."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "tool") or runtime.tool is None:
            return ComponentHealth(
                name="tools", state=HealthState.OFFLINE,
                label="Tool engine not available", last_checked=now,
            )

        try:
            tool_count = 0
            if hasattr(runtime.tool, "list_tools"):
                tools = runtime.tool.list_tools()
                tool_count = len(tools) if tools else 0
            return ComponentHealth(
                name="tools",
                state=HealthState.ONLINE,
                label=f"Tool engine ready ({tool_count} tool(s))",
                details={"tool_count": tool_count},
                last_checked=now,
            )
        except Exception as exc:
            return ComponentHealth(
                name="tools", state=HealthState.FAILED,
                label="Tool engine check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_memory(self) -> ComponentHealth:
        """Check memory engine health."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "memory") or runtime.memory is None:
            return ComponentHealth(
                name="memory", state=HealthState.OFFLINE,
                label="Memory engine not available", last_checked=now,
            )

        try:
            has_agent_memory = hasattr(runtime.memory, "read_agent_memory") or hasattr(runtime.memory, "write_agent_memory")
            has_org_memory = hasattr(runtime.memory, "write_org_memory")
            return ComponentHealth(
                name="memory",
                state=HealthState.ONLINE,
                label="Memory engine ready",
                details={"agent_memory": has_agent_memory, "org_memory": has_org_memory},
                last_checked=now,
            )
        except Exception as exc:
            return ComponentHealth(
                name="memory", state=HealthState.FAILED,
                label="Memory engine check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_runtime(self) -> ComponentHealth:
        """Check overall runtime health."""
        now = time.time()
        runtime = self._runtime

        if runtime is None:
            return ComponentHealth(
                name="runtime", state=HealthState.OFFLINE,
                label="Runtime not available", last_checked=now,
            )

        try:
            running = getattr(runtime, "_running", False)
            initialised = getattr(runtime, "_initialised", False)
            if running and initialised:
                status = runtime.get_status() if hasattr(runtime, "get_status") else {}
                components_loaded = sum(1 for v in status.get("components", {}).values() if v)
                return ComponentHealth(
                    name="runtime",
                    state=HealthState.ONLINE,
                    label=f"Runtime running ({components_loaded} components loaded)",
                    details={"running": True, "initialised": True, "components_loaded": components_loaded},
                    last_checked=now,
                )
            elif initialised and not running:
                return ComponentHealth(
                    name="runtime",
                    state=HealthState.DEGRADED,
                    label="Runtime initialised but not running",
                    details={"running": False, "initialised": True},
                    last_checked=now,
                )
            else:
                return ComponentHealth(
                    name="runtime",
                    state=HealthState.OFFLINE,
                    label="Runtime not initialised",
                    details={"running": False, "initialised": False},
                    last_checked=now,
                )
        except Exception as exc:
            return ComponentHealth(
                name="runtime", state=HealthState.FAILED,
                label="Runtime check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_intelligence(self) -> ComponentHealth:
        """Check intelligence provider availability."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "intelligence") or runtime.intelligence is None:
            return ComponentHealth(
                name="intelligence_providers", state=HealthState.OFFLINE,
                label="Intelligence engine not available", last_checked=now,
            )

        try:
            providers = runtime.intelligence.list_providers() if hasattr(runtime.intelligence, "list_providers") else []
            provider_count = len(providers)
            available = sum(1 for p in providers if isinstance(p, dict) and p.get("available", True))

            if available > 0:
                return ComponentHealth(
                    name="intelligence_providers",
                    state=HealthState.ONLINE,
                    label=f"{available}/{provider_count} provider(s) available",
                    details={"total": provider_count, "available": available, "providers": providers},
                    last_checked=now,
                )
            else:
                return ComponentHealth(
                    name="intelligence_providers",
                    state=HealthState.DEGRADED,
                    label="No intelligence providers available",
                    details={"total": provider_count, "available": 0},
                    last_checked=now,
                )
        except Exception as exc:
            return ComponentHealth(
                name="intelligence_providers", state=HealthState.FAILED,
                label="Intelligence provider check failed",
                last_error=str(exc), last_checked=now,
            )

    async def _check_system_metrics(self) -> ComponentHealth:
        """Check CPU/RAM/disk health via SystemMonitor."""
        now = time.time()
        runtime = self._runtime

        if not runtime or not hasattr(runtime, "system_monitor") or runtime.system_monitor is None:
            return ComponentHealth(
                name="system_metrics", state=HealthState.OFFLINE,
                label="System monitor not available", last_checked=now,
            )

        try:
            snapshot = await runtime.system_monitor.snapshot()
            health_score = getattr(snapshot, "health_score", 1.0)
            health_label = getattr(snapshot, "health_label", "healthy")

            if health_score >= self.HEALTHY_THRESHOLD:
                state = HealthState.ONLINE
            elif health_score >= self.DEGRADED_THRESHOLD:
                state = HealthState.DEGRADED
            else:
                state = HealthState.BLOCKED

            return ComponentHealth(
                name="system_metrics",
                state=state,
                label=f"System metrics: {health_label.upper()} (score: {health_score:.2f})",
                details={
                    "health_score": health_score,
                    "health_label": health_label,
                    "cpu": getattr(snapshot, "cpu", None),
                    "memory": getattr(snapshot, "memory", None),
                    "disk": getattr(snapshot, "disk", None),
                },
                last_checked=now,
            )
        except Exception as exc:
            return ComponentHealth(
                name="system_metrics", state=HealthState.DEGRADED,
                label="System metrics check failed",
                last_error=str(exc), last_checked=now,
            )

    # ── Aggregate computation ──────────────────────────────────────────────

    def _compute_overall(self, snapshot: SystemHealthSnapshot) -> HealthState:
        """Compute overall health state from all component states.

        - Any FAILED -> DEGRADED (AXIOM keeps running, but not at full capacity)
        - Any BLOCKED -> DEGRADED
        - More than 2 DEGRADED -> DEGRADED
        - Any RECOVERING -> DEGRADED
        - All ONLINE -> ONLINE
        - Default -> DEGRADED
        """
        has_failed = False
        has_blocked = False
        has_recovering = False
        degraded_count = 0
        online_count = 0
        offline_count = 0

        for ch in snapshot.components.values():
            if ch.state == HealthState.FAILED:
                has_failed = True
            elif ch.state == HealthState.BLOCKED:
                has_blocked = True
            elif ch.state == HealthState.RECOVERING:
                has_recovering = True
            elif ch.state == HealthState.DEGRADED:
                degraded_count += 1
            elif ch.state == HealthState.ONLINE:
                online_count += 1
            elif ch.state == HealthState.OFFLINE:
                offline_count += 1

        if has_failed:
            return HealthState.DEGRADED

        if has_blocked:
            return HealthState.DEGRADED

        if has_recovering:
            return HealthState.DEGRADED

        if degraded_count > 2:
            return HealthState.DEGRADED

        if online_count == len(snapshot.components):
            return HealthState.ONLINE

        # Some components offline but no failures -> DEGRADED
        if offline_count > 0:
            return HealthState.DEGRADED

        return HealthState.DEGRADED

    def _compute_health_score(self, snapshot: SystemHealthSnapshot) -> float:
        """Compute weighted health score 0.0-1.0.

        Weights:
          - executives (3): 25%
          - agents: 10%
          - workflows: 15%
          - events: 10%
          - tools: 10%
          - memory: 10%
          - runtime: 10%
          - intelligence_providers: 10%
        """
        weights = {
            "executives": 0.25,
            "agents": 0.10,
            "workflows": 0.15,
            "events": 0.10,
            "tools": 0.10,
            "memory": 0.10,
            "runtime": 0.10,
            "intelligence_providers": 0.10,
        }

        total_score = 0.0
        total_weight = 0.0

        for comp_key, ch in snapshot.components.items():
            weight = weights.get(comp_key, 0.05)
            state_score = self._state_to_score(ch.state)
            total_score += weight * state_score
            total_weight += weight

        # If executives is an aggregated component, unpack it for the actual 3 executives
        if "executives" in snapshot.components and snapshot.executives:
            exec_weight = weights.get("executives", 0.25)
            total_score -= exec_weight * self._state_to_score(snapshot.components["executives"].state)

            # Average the 3 individual executive states
            exec_scores = [self._state_to_score(ch.state) for ch in snapshot.executives.values()]
            avg_exec_score = sum(exec_scores) / len(exec_scores) if exec_scores else 0.0
            total_score += exec_weight * avg_exec_score

        return max(0.0, min(1.0, total_score / total_weight if total_weight > 0 else 0.0))

    # ── Helpers ────────────────────────────────────────────────────────────

    def _get_active_workflow_count(self) -> int:
        """Count active workflow instances."""
        runtime = self._runtime
        if not runtime or not hasattr(runtime, "workflow") or runtime.workflow is None:
            return 0
        try:
            instances = runtime.workflow.list_instances() if hasattr(runtime.workflow, "list_instances") else []
            return sum(1 for i in instances if getattr(i, "status", None) in ("running", "RUNNING", "active", "ACTIVE"))
        except Exception:
            return 0

    def _get_pending_approval_count(self) -> int:
        """Count pending approval requests."""
        runtime = self._runtime
        if not runtime or not hasattr(runtime, "approval") or runtime.approval is None:
            return 0
        try:
            if hasattr(runtime.approval, "pending_count"):
                return runtime.approval.pending_count()
            if hasattr(runtime.approval, "list_pending"):
                return len(runtime.approval.list_pending())
            return 0
        except Exception:
            return 0

    def _get_uptime(self) -> float:
        """Get runtime uptime in seconds."""
        runtime = self._runtime
        if not runtime or not hasattr(runtime, "system_monitor") or runtime.system_monitor is None:
            return 0.0
        try:
            boot = getattr(runtime.system_monitor, "_boot_time", 0.0)
            if boot:
                return time.time() - boot
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _state_to_score(state: HealthState) -> float:
        """Convert a HealthState to a numeric score 0.0-1.0."""
        mapping = {
            HealthState.ONLINE: 1.0,
            HealthState.RECOVERING: 0.7,
            HealthState.DEGRADED: 0.4,
            HealthState.BLOCKED: 0.2,
            HealthState.FAILED: 0.1,
            HealthState.OFFLINE: 0.0,
        }
        return mapping.get(state, 0.0)

    # ── Status ────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return a lightweight status summary."""
        return {
            "initialised": self._initialised,
            "components_monitored": len(self._components),
        }

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        self._initialised = False
        self._components.clear()
        if self._logger:
            self._logger.info("system_health", "SystemHealthMonitor shut down")


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _aggregate_component(name: str, sub_components: Dict[str, ComponentHealth]) -> ComponentHealth:
    """Aggregate a group of sub-components into a single ComponentHealth."""
    if not sub_components:
        return ComponentHealth(name=name, state=HealthState.OFFLINE, label=f"No {name} registered")

    worst_state = HealthState.ONLINE
    errors = []
    for ch in sub_components.values():
        if _state_rank(ch.state) > _state_rank(worst_state):
            worst_state = ch.state
        if ch.last_error:
            errors.append(f"{ch.name}: {ch.last_error}")

    total = len(sub_components)
    online = sum(1 for ch in sub_components.values() if ch.state == HealthState.ONLINE)

    label = f"{online}/{total} {name} online"
    if errors:
        label += f" ({len(errors)} error(s))"

    return ComponentHealth(
        name=name,
        state=worst_state,
        label=label,
        last_error=errors[0] if errors else None,
    )


def _state_rank(state: HealthState) -> int:
    """Return severity rank: higher = worse."""
    ranks = {
        HealthState.ONLINE: 0,
        HealthState.RECOVERING: 1,
        HealthState.DEGRADED: 2,
        HealthState.BLOCKED: 3,
        HealthState.FAILED: 4,
        HealthState.OFFLINE: 5,
    }
    return ranks.get(state, 10)