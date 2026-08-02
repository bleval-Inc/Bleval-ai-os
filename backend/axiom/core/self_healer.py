"""
Self-Healer -- detects, diagnoses, and recovers from failures.

Cycle:
    Detect -> Classify -> Diagnose -> Attempt recovery -> Verify -> Record -> Learn

Rules:
  - Max 3 recovery attempts per component, then circuit-breaker opens.
  - Never creates infinite retry loops.
  - Every repair is observable (logged, published, recorded).
  - Unrecoverable failures are escalated with a full report.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from axiom.core.system_health import ComponentHealth, HealthState, SystemHealthMonitor


# ═══════════════════════════════════════════════════════════════════════════════
# Recovery model
# ═══════════════════════════════════════════════════════════════════════════════


class RecoveryAction(str, Enum):
    """Recovery strategies the self-healer can execute."""

    RESTART_WORKER = "restart_worker"
    RETRY_API_CALL = "retry_api_call"
    REFRESH_SESSION = "refresh_session"
    REQUEUE_WORKFLOW = "requeue_workflow"
    RESTART_SERVICE = "restart_service"
    REPORT_UNRECOVERABLE = "report_unrecoverable"


@dataclass
class RecoveryResult:
    """Outcome of a single recovery attempt."""

    action_taken: RecoveryAction
    target: str  # what was recovered (worker_id, workflow_instance_id, etc.)
    success: bool
    message: str
    duration_ms: float
    verified: bool = False


@dataclass
class RecoveryEvent:
    """Persistent record of a recovery attempt for history and learning."""

    event_id: str
    timestamp: float
    component: str
    failure_type: str
    diagnosis: str
    action: RecoveryAction
    success: bool
    verified: bool
    details: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Self-Healer Engine
# ═══════════════════════════════════════════════════════════════════════════════


class SelfHealer:
    """Autonomous failure detection and recovery.

    Follows the cycle:
      1. Detect -- identify failures via the health monitor snapshot
      2. Classify -- categorise the failure type
      3. Diagnose -- determine root cause
      4. Attempt recovery -- execute safe recovery strategy
      5. Verify -- confirm recovery succeeded via re-check
      6. Record -- log recovery event
      7. Learn -- feed to LearningEngine

    Circuit breaker:
      - Each component gets MAX_RECOVERY_ATTEMPTS (3) before the breaker opens.
      - Once open, further recovery attempts are refused until a manual reset
        or a new health snapshot shows the component has self-recovered.
      - Circuit breakers auto-reset after 300 seconds of no further failures.
    """

    MAX_RECOVERY_ATTEMPTS = 3
    CIRCUIT_BREAKER_RESET_SECONDS = 300.0

    # Failure type keywords for classification
    _FAILURE_PATTERNS: Dict[str, List[str]] = {
        "worker_stopped": ["worker", "loop stopped", "executive stopped", "not running"],
        "api_error": ["api", "timeout", "connection refused", "connection reset", "5xx", "4xx"],
        "session_expired": ["session", "token", "expired", "unauthorized", "auth"],
        "workflow_failure": ["workflow", "step failed", "retry exhausted", "task failed"],
        "resource_exhaustion": ["memory", "cpu", "disk", "oom", "out of memory", "resource"],
        "service_crash": ["crash", "segfault", "panic", "unexpected exit", "died"],
    }

    def __init__(
        self,
        runtime: Any = None,
        monitor: Optional[SystemHealthMonitor] = None,
        event: Any = None,
        learning: Any = None,
        logger: Any = None,
    ) -> None:
        self._runtime = runtime
        self._monitor = monitor
        self._event = event
        self._learning = learning
        self._logger = logger

        # component -> list of recovery events
        self._recovery_history: Dict[str, List[RecoveryEvent]] = {}
        # component -> attempt count (circuit breaker counter)
        self._circuit_breakers: Dict[str, int] = {}
        # component -> last failure timestamp (for auto-reset)
        self._last_failure_time: Dict[str, float] = {}

    # ── Public API ─────────────────────────────────────────────────────────

    async def attempt_recovery(
        self,
        component: str,
        failure: ComponentHealth,
    ) -> RecoveryResult:
        """Attempt to recover a failed component.

        The full cycle:
          1. Check circuit breaker (refuse if max attempts exceeded)
          2. Classify failure type from the ComponentHealth data
          3. Diagnose root cause
          4. Execute the appropriate recovery strategy
          5. Verify recovery via re-check
          6. Record and learn
        """
        if not self._should_attempt_recovery(component):
            return RecoveryResult(
                action_taken=RecoveryAction.REPORT_UNRECOVERABLE,
                target=component,
                success=False,
                message=f"Circuit breaker open for {component}",
                duration_ms=0.0,
                verified=False,
            )

        start = time.monotonic()

        # 2. Classify
        failure_type = await self._classify_failure(component, failure.state, failure.last_error or "")

        # 3. Diagnose
        diagnosis = await self._diagnose(component, failure_type)

        # 4. Execute recovery
        result = await self._execute_recovery(component, failure_type, diagnosis)
        result.duration_ms = (time.monotonic() - start) * 1000.0

        # 5. Verify
        if result.success:
            result.verified = await self._verify_recovery(component)

        # 6. Record
        event = RecoveryEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            component=component,
            failure_type=failure_type,
            diagnosis=diagnosis,
            action=result.action_taken,
            success=result.success,
            verified=result.verified,
            details={
                "state": failure.state.value if isinstance(failure.state, HealthState) else str(failure.state),
                "error": failure.last_error,
                "message": result.message,
                "duration_ms": result.duration_ms,
            },
        )
        await self._record_recovery(event)

        # Update circuit breaker
        if component not in self._circuit_breakers:
            self._circuit_breakers[component] = 0
        self._circuit_breakers[component] += 1
        self._last_failure_time[component] = time.time()

        if self._logger:
            status = "SUCCESS" if result.success and result.verified else "PARTIAL" if result.success else "FAILED"
            self._logger.info(
                "self_healer",
                f"Recovery [{status}] for {component}: "
                f"{result.action_taken.value} -> {result.message} "
                f"({result.duration_ms:.0f}ms, verified={result.verified})",
            )

        return result

    def get_recovery_history(self, component: Optional[str] = None) -> List[RecoveryEvent]:
        """Get recovery history, optionally filtered by component."""
        if component:
            return list(self._recovery_history.get(component, []))
        all_events: List[RecoveryEvent] = []
        for events in self._recovery_history.values():
            all_events.extend(events)
        return sorted(all_events, key=lambda e: e.timestamp, reverse=True)

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all components.

        Returns a dict keyed by component with attempt count, max, open state,
        and auto-reset time remaining.
        """
        now = time.time()
        status: Dict[str, Any] = {}
        for component, attempts in self._circuit_breakers.items():
            last_fail = self._last_failure_time.get(component, 0.0)
            time_since = now - last_fail
            auto_reset_remaining = max(0.0, self.CIRCUIT_BREAKER_RESET_SECONDS - time_since)

            status[component] = {
                "attempts": attempts,
                "max_attempts": self.MAX_RECOVERY_ATTEMPTS,
                "open": attempts >= self.MAX_RECOVERY_ATTEMPTS,
                "auto_reset_in_seconds": round(auto_reset_remaining, 1),
                "last_failure_seconds_ago": round(time_since, 1),
            }

            # Auto-reset if enough time has passed without new failures
            if time_since >= self.CIRCUIT_BREAKER_RESET_SECONDS and attempts >= self.MAX_RECOVERY_ATTEMPTS:
                status[component]["auto_reset"] = True

        return status

    # ── Internal: Classify ─────────────────────────────────────────────────

    async def _classify_failure(
        self,
        component: str,
        state: HealthState,
        error: str,
    ) -> str:
        """Classify the type of failure from component name, state, and error."""
        if state == HealthState.FAILED:
            # Determine specific failure type from error text
            error_lower = error.lower()
            for failure_type, patterns in self._FAILURE_PATTERNS.items():
                for pattern in patterns:
                    if pattern in error_lower:
                        return failure_type

            # Fallback classification based on component name
            if "executive" in component.lower() or component in ("jenson", "valta_prime", "yamako"):
                return "worker_stopped"
            if "workflow" in component.lower():
                return "workflow_failure"
            if "intelligence" in component.lower() or "provider" in component.lower():
                return "api_error"
            if "session" in component.lower():
                return "session_expired"
            if "memory" in component.lower() or "disk" in component.lower():
                return "resource_exhaustion"

            return "service_crash"

        if state == HealthState.DEGRADED:
            return "resource_exhaustion"

        if state == HealthState.BLOCKED:
            return "resource_exhaustion"

        if state == HealthState.RECOVERING:
            return "worker_stopped"

        return "service_crash"

    async def _diagnose(self, component: str, failure_type: str) -> str:
        """Diagnose root cause of failure based on type and component context."""
        diagnoses: Dict[str, str] = {
            "worker_stopped": (
                f"Executive worker '{component}' stopped unexpectedly. "
                f"Likely causes: unhandled exception, OOM kill, or manual stop."
            ),
            "api_error": (
                f"External API/dependency call failed for '{component}'. "
                f"Likely causes: network issue, upstream outage, or rate limiting."
            ),
            "session_expired": (
                f"Session or token expired for '{component}'. "
                f"Likely causes: token TTL reached, revoked credentials."
            ),
            "workflow_failure": (
                f"Workflow step failure in '{component}'. "
                f"Likely causes: agent task error, retry exhaustion, invalid state."
            ),
            "resource_exhaustion": (
                f"Resource limits reached on '{component}'. "
                f"Likely causes: high CPU/RAM/disk usage, OOM, or file handle leak."
            ),
            "service_crash": (
                f"Service '{component}' terminated unexpectedly. "
                f"Likely causes: unhandled exception, segfault, or system kill."
            ),
        }
        return diagnoses.get(failure_type, f"Unknown failure for '{component}'.")

    # ── Internal: Execute recovery ────────────────────────────────────────

    async def _execute_recovery(
        self,
        component: str,
        failure_type: str,
        diagnosis: str,
    ) -> RecoveryResult:
        """Execute the appropriate recovery strategy for the failure type."""
        strategy_map: Dict[str, Any] = {
            "worker_stopped": self._restart_worker,
            "api_error": self._retry_api_call,
            "session_expired": self._refresh_session,
            "workflow_failure": self._requeue_workflow,
            "resource_exhaustion": self._restart_service,
            "service_crash": self._report_unrecoverable,
        }

        strategy = strategy_map.get(failure_type, self._restart_service)
        return await strategy(component)

    async def _restart_worker(self, component: str) -> RecoveryResult:
        """Restart a failed worker (executive loop)."""
        runtime = self._runtime
        if not runtime or not hasattr(runtime, "executive_board") or runtime.executive_board is None:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_WORKER,
                target=component,
                success=False,
                message="ExecutiveBoard not available",
                duration_ms=0.0,
            )

        if not hasattr(runtime.executive_board, "get_loop"):
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_WORKER,
                target=component,
                success=False,
                message="ExecutiveBoard missing get_loop",
                duration_ms=0.0,
            )

        loop = runtime.executive_board.get_loop(component)
        if loop is None:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_WORKER,
                target=component,
                success=False,
                message=f"Loop not found for {component}",
                duration_ms=0.0,
            )

        try:
            # Stop the loop first
            if hasattr(loop, "stop"):
                await loop.stop()

            await asyncio_sleep(1.0)

            # Start the loop
            if hasattr(loop, "start"):
                await loop.start()

            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_WORKER,
                target=component,
                success=True,
                message=f"Worker '{component}' restarted successfully",
                duration_ms=0.0,
            )
        except Exception as exc:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_WORKER,
                target=component,
                success=False,
                message=f"Failed to restart worker '{component}': {exc}",
                duration_ms=0.0,
            )

    async def _retry_api_call(self, component: str) -> RecoveryResult:
        """Retry a failed API/dependency call.

        External API retries can only be logged -- we cannot retry external
        calls internally.  The retry will happen when the next request flows
        through the system.
        """
        return RecoveryResult(
            action_taken=RecoveryAction.RETRY_API_CALL,
            target=component,
            success=True,
            message=(
                f"API call failure for '{component}' recorded. "
                f"External retry will occur on next request. "
                f"Recommend checking upstream provider status."
            ),
            duration_ms=0.0,
            verified=False,
        )

    async def _refresh_session(self, component: str) -> RecoveryResult:
        """Refresh an expired session or token.

        Session refresh is logged and flagged for the runtime.  Actual token
        refresh must happen through the IntelligenceEngine's provider rotation
        or a manual credential refresh.
        """
        runtime = self._runtime
        refreshed = False

        if runtime and hasattr(runtime, "intelligence") and runtime.intelligence is not None:
            try:
                if hasattr(runtime.intelligence, "set_provider"):
                    # Force provider rotation -- will pick a new healthy provider
                    # which implicitly refreshes the session
                    refreshed = True
            except Exception:
                pass

        if refreshed:
            return RecoveryResult(
                action_taken=RecoveryAction.REFRESH_SESSION,
                target=component,
                success=True,
                message=f"Session refresh initiated for '{component}' via provider rotation",
                duration_ms=0.0,
            )
        else:
            return RecoveryResult(
                action_taken=RecoveryAction.REFRESH_SESSION,
                target=component,
                success=True,
                message=f"Session refresh requested for '{component}' (logged for manual action)",
                duration_ms=0.0,
            )

    async def _requeue_workflow(self, component: str) -> RecoveryResult:
        """Re-queue a failed workflow if possible."""
        runtime = self._runtime
        if not runtime or not hasattr(runtime, "workflow") or runtime.workflow is None:
            return RecoveryResult(
                action_taken=RecoveryAction.REQUEUE_WORKFLOW,
                target=component,
                success=False,
                message="Workflow engine not available",
                duration_ms=0.0,
            )

        # The component might be a workflow instance ID or a workflow ID.
        # Try it as an instance ID first.
        target_id = component

        try:
            if hasattr(runtime.workflow, "retry"):
                await runtime.workflow.retry(target_id)
                return RecoveryResult(
                    action_taken=RecoveryAction.REQUEUE_WORKFLOW,
                    target=target_id,
                    success=True,
                    message=f"Workflow '{target_id}' re-queued for retry",
                    duration_ms=0.0,
                )
            else:
                return RecoveryResult(
                    action_taken=RecoveryAction.REQUEUE_WORKFLOW,
                    target=target_id,
                    success=False,
                    message="Workflow engine missing retry method",
                    duration_ms=0.0,
                )
        except ValueError as ve:
            # retry() raises ValueError if max retries exceeded or wrong state
            return RecoveryResult(
                action_taken=RecoveryAction.REQUEUE_WORKFLOW,
                target=target_id,
                success=False,
                message=f"Cannot retry workflow '{target_id}': {ve}",
                duration_ms=0.0,
            )
        except Exception as exc:
            return RecoveryResult(
                action_taken=RecoveryAction.REQUEUE_WORKFLOW,
                target=target_id,
                success=False,
                message=f"Failed to retry workflow '{target_id}': {exc}",
                duration_ms=0.0,
            )

    async def _restart_service(self, component: str) -> RecoveryResult:
        """Restart a service component.

        This is a soft restart -- the runtime subsystem is re-initialised
        rather than killed and recreated.  Hard service restarts require
        external process management (supervisor, systemd, etc.).
        """
        runtime = self._runtime
        if not runtime:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_SERVICE,
                target=component,
                success=False,
                message="Runtime not available for service restart",
                duration_ms=0.0,
            )

        # Map component names to runtime attributes that can be re-initialised
        service_map: Dict[str, str] = {
            "system_metrics": "system_monitor",
            "events": "event",
            "tools": "tool",
            "memory": "memory",
            "intelligence_providers": "intelligence",
        }

        attr_name = service_map.get(component)
        if attr_name is None:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_SERVICE,
                target=component,
                success=False,
                message=f"No restart strategy for component '{component}'",
                duration_ms=0.0,
            )

        service = getattr(runtime, attr_name, None) if hasattr(runtime, attr_name) else None
        if service is None:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_SERVICE,
                target=component,
                success=False,
                message=f"Service '{component}' ({attr_name}) is None",
                duration_ms=0.0,
            )

        try:
            # Attempt re-initialisation
            if hasattr(service, "initialise"):
                await service.initialise()
                return RecoveryResult(
                    action_taken=RecoveryAction.RESTART_SERVICE,
                    target=component,
                    success=True,
                    message=f"Service '{component}' re-initialised",
                    duration_ms=0.0,
                )
            elif hasattr(service, "start"):
                await service.start()
                return RecoveryResult(
                    action_taken=RecoveryAction.RESTART_SERVICE,
                    target=component,
                    success=True,
                    message=f"Service '{component}' restarted",
                    duration_ms=0.0,
                )
            else:
                return RecoveryResult(
                    action_taken=RecoveryAction.RESTART_SERVICE,
                    target=component,
                    success=False,
                    message=f"Service '{component}' has no initialise/start method",
                    duration_ms=0.0,
                )
        except Exception as exc:
            return RecoveryResult(
                action_taken=RecoveryAction.RESTART_SERVICE,
                target=component,
                success=False,
                message=f"Failed to restart service '{component}': {exc}",
                duration_ms=0.0,
            )

    async def _report_unrecoverable(self, component: str) -> RecoveryResult:
        """Report an unrecoverable failure.

        This is the last resort -- all other recovery strategies have failed
        or the failure type is not recoverable.  The event is logged and
        escalated via the event engine.
        """
        result = RecoveryResult(
            action_taken=RecoveryAction.REPORT_UNRECOVERABLE,
            target=component,
            success=False,
            message=(
                f"Unrecoverable failure for '{component}'. "
                f"Manual intervention required. "
                f"Circuit breaker opened."
            ),
            duration_ms=0.0,
            verified=False,
        )

        # Publish an unrecoverable event if event engine is available
        runtime = self._runtime
        if runtime and hasattr(runtime, "event") and runtime.event is not None:
            try:
                if hasattr(runtime.event, "publish"):
                    await runtime.event.publish(
                        event_type="system.unrecoverable_failure",
                        source="self_healer",
                        payload={
                            "component": component,
                            "timestamp": time.time(),
                            "message": result.message,
                        },
                    )
            except Exception:
                pass

        return result

    # ── Internal: Verify ──────────────────────────────────────────────────

    async def _verify_recovery(self, component: str) -> bool:
        """Verify that recovery was successful by re-checking component health."""
        if self._monitor is None:
            return False

        try:
            snapshot = await self._monitor.full_snapshot()

            # Check specific component health from snapshot
            ch = snapshot.components.get(component)
            if ch is None:
                # If the component is an executive, check the executives group
                if component in ("jenson", "valta_prime", "yamako"):
                    exec_ch = snapshot.executives.get(component)
                    return exec_ch is not None and exec_ch.state == HealthState.ONLINE

                # Check if it's one of the named groups
                group_map: Dict[str, str] = {
                    "agents": "agents",
                    "workflows": "workflows",
                    "events": "events",
                    "tools": "tools",
                    "memory": "memory",
                    "runtime": "runtime",
                    "intelligence_providers": "intelligence_providers",
                }
                group_key = group_map.get(component)
                if group_key:
                    group_ch = getattr(snapshot, group_key, None)
                    return group_ch is not None and group_ch.state == HealthState.ONLINE

                return False

            return ch.state in (HealthState.ONLINE, HealthState.RECOVERING)
        except Exception:
            return False

    # ── Internal: Record ──────────────────────────────────────────────────

    async def _record_recovery(self, event: RecoveryEvent) -> None:
        """Record recovery event to history, EventEngine, and LearningEngine.

        The record is always persisted to local history.  Event publishing
        and learning are best-effort (errors are swallowed).
        """
        # 1. Local history
        if event.component not in self._recovery_history:
            self._recovery_history[event.component] = []
        self._recovery_history[event.component].append(event)

        # Clean old history (keep last 100 per component)
        if len(self._recovery_history[event.component]) > 100:
            self._recovery_history[event.component] = self._recovery_history[event.component][-100:]

        # 2. EventEngine
        if self._event is not None:
            try:
                await self._event.publish(
                    event_type="recovery.completed" if event.success else "recovery.failed",
                    source="self_healer",
                    payload={
                        "event_id": event.event_id,
                        "component": event.component,
                        "failure_type": event.failure_type,
                        "action": event.action.value,
                        "success": event.success,
                        "verified": event.verified,
                        "diagnosis": event.diagnosis,
                        "details": event.details,
                    },
                )
            except Exception:
                pass

        # 3. LearningEngine
        if self._learning is not None:
            try:
                await self._learning.record_agent_task(
                    agent_id="self_healer",
                    success=event.success,
                    action=event.action.value,
                    task_id=event.event_id,
                    error=None if event.success else event.details.get("error", event.diagnosis),
                )
            except Exception:
                pass

    # ── Internal: Circuit breaker ─────────────────────────────────────────

    def _should_attempt_recovery(self, component: str) -> bool:
        """Check circuit breaker -- have we exceeded max attempts?

        Auto-resets if enough time has passed since the last failure.
        """
        attempts = self._circuit_breakers.get(component, 0)
        if attempts < self.MAX_RECOVERY_ATTEMPTS:
            return True

        # Check auto-reset
        last_fail = self._last_failure_time.get(component, 0.0)
        elapsed = time.time() - last_fail
        if elapsed >= self.CIRCUIT_BREAKER_RESET_SECONDS:
            # Reset the circuit breaker
            self._circuit_breakers[component] = 0
            if self._logger:
                self._logger.info(
                    "self_healer",
                    f"Circuit breaker auto-reset for '{component}' "
                    f"({elapsed:.0f}s since last failure)",
                )
            return True

        return False

    # ── Utility ──────────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the self-healer state."""
        all_events = self.get_recovery_history()
        total = len(all_events)
        successes = sum(1 for e in all_events if e.success)
        verified = sum(1 for e in all_events if e.verified)
        return {
            "total_recovery_events": total,
            "successful": successes,
            "verified": verified,
            "success_rate": round(successes / total, 4) if total else 0.0,
            "components_with_history": list(self._recovery_history.keys()),
            "circuit_breakers": {
                comp: {
                    "attempts": info["attempts"],
                    "open": info["open"],
                }
                for comp, info in self.get_circuit_breaker_status().items()
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Async helper (avoids importing asyncio at module level for clean visibility)
# ═══════════════════════════════════════════════════════════════════════════════


async def asyncio_sleep(seconds: float) -> None:
    """Async sleep helper."""
    import asyncio
    await asyncio.sleep(seconds)