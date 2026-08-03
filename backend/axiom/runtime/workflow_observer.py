"""Workflow Observability System — PHASE C §7.

Every workflow exposes:
  - state / phase
  - current step
  - assigned agents
  - duration
  - progress %
  - errors
  - retries
  - output
  - dependencies
  - approval state
  - QC state
  - history

This observer watches all workflow activity and provides a unified
observability interface for the API layer and dashboard UI.
"""

import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from axiom.models.workflow_autonomous import (
    AutonomousLifecyclePhase,
    AutonomousWorkflowManifest,
    AutonomousWorkflowPhaseState,
)


class WorkflowObserver:
    """Observability hub for all workflow executions (§7).

    Aggregates state from:
      - AutonomousWorkflowEngine
      - Base WorkflowEngine
      - BackgroundExecutor
      - SpecialistAgentEngine

    Provides a unified observability interface for:
      - API layer (REST endpoints)
      - Dashboard UI (WebSocket subscriptions)
      - CLI (status commands)
      - Learning Engine (post-execution analysis)
    """

    def __init__(self) -> None:
        # Runtime snapshots: instance_id -> Dict
        self._snapshots: Dict[str, Dict[str, Any]] = {}

        # Event history
        self._events: List[Dict[str, Any]] = []

        # Active subscriptions for live updates
        self._subscriptions: Dict[str, List[Any]] = defaultdict(list)

        # Phase duration tracking
        self._phase_timings: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Max events to retain
        self._max_events = 10_000

    # ── Snapshot Management ─────────────────────────────────────────

    def record_snapshot(
        self,
        instance_id: str,
        manifest: AutonomousWorkflowManifest,
    ) -> None:
        """Record an observability snapshot for a workflow instance.

        Called periodically by the monitor loop and on phase transitions.
        """
        self._snapshots[instance_id] = manifest.model_dump()

        # Record phase timing
        if manifest.phase not in self._phase_timings[instance_id]:
            self._phase_timings[instance_id][manifest.phase] = 0.0

    def get_snapshot(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest observability snapshot for an instance."""
        return self._snapshots.get(instance_id)

    def get_all_snapshots(
        self,
        status: Optional[str] = None,
        workflow_id: Optional[str] = None,
        org: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all snapshots, optionally filtered."""
        snapshots = list(self._snapshots.values())
        if status:
            snapshots = [s for s in snapshots if s.get("status") == status]
        if workflow_id:
            snapshots = [s for s in snapshots if s.get("workflow_id") == workflow_id]
        if org:
            snapshots = [s for s in snapshots if s.get("org") == org]
        return sorted(
            snapshots,
            key=lambda s: s.get("created_at", ""),
            reverse=True,
        )

    def delete_snapshot(self, instance_id: str) -> bool:
        """Remove a snapshot (e.g., workflow completed and cleaned up)."""
        return self._snapshots.pop(instance_id, None) is not None

    # ── Event Logging ──────────────────────────────────────────────

    def log_event(
        self,
        instance_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log a workflow event for the event history.

        Events include:
          - phase transitions
          - step starts/completions
          - errors
          - retries
          - approval requests
          - QC evaluations
        """
        event_id = str(uuid.uuid4())
        event = {
            "event_id": event_id,
            "instance_id": instance_id,
            "event_type": event_type,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._events.append(event)

        # Enforce max events
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        # Notify subscribers
        self._notify_subscribers(instance_id, event)

        return event_id

    def get_events(
        self,
        instance_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get event history, optionally filtered."""
        events = self._events
        if instance_id:
            events = [e for e in events if e.get("instance_id") == instance_id]
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        return events[-limit:]

    # ── Phase Timing ───────────────────────────────────────────────

    def record_phase_duration(
        self,
        instance_id: str,
        phase: str,
        duration_seconds: float,
    ) -> None:
        """Record how long a phase took."""
        self._phase_timings[instance_id][phase] = duration_seconds

    def get_phase_timings(
        self, instance_id: str
    ) -> Dict[str, float]:
        """Get phase timings for an instance."""
        return dict(self._phase_timings.get(instance_id, {}))

    def get_average_phase_time(self, phase: str) -> float:
        """Get average duration for a phase across all instances."""
        durations = []
        for instance_timings in self._phase_timings.values():
            d = instance_timings.get(phase)
            if d is not None:
                durations.append(d)
        return sum(durations) / len(durations) if durations else 0.0

    # ── Live Subscriptions ──────────────────────────────────────────

    def subscribe(self, subscriber_id: str, callback: Any) -> None:
        """Subscribe to live workflow events.

        The callback is called for every event that occurs.
        """
        instance_id = "all"
        self._subscriptions[instance_id].append({
            "id": subscriber_id,
            "callback": callback,
        })

    def subscribe_to_instance(
        self, instance_id: str, subscriber_id: str, callback: Any
    ) -> None:
        """Subscribe to events for a specific workflow instance."""
        self._subscriptions[instance_id].append({
            "id": subscriber_id,
            "callback": callback,
        })

    def unsubscribe(self, subscriber_id: str) -> bool:
        """Remove a subscriber."""
        for instance_id in list(self._subscriptions.keys()):
            self._subscriptions[instance_id] = [
                s for s in self._subscriptions[instance_id]
                if s["id"] != subscriber_id
            ]
        return True

    def _notify_subscribers(
        self, instance_id: str, event: Dict[str, Any]
    ) -> None:
        """Notify all subscribers of a new event."""
        # Notify instance-specific subscribers
        for sub in self._subscriptions.get(instance_id, []):
            try:
                sub["callback"](event)
            except Exception:
                pass

        # Notify global subscribers
        for sub in self._subscriptions.get("all", []):
            try:
                sub["callback"](event)
            except Exception:
                pass

    # ── Aggregation & Analytics ─────────────────────────────────────

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Get aggregate observability stats across all workflows."""
        snapshots = list(self._snapshots.values())

        status_counts: Dict[str, int] = defaultdict(int)
        total_duration = 0.0
        total_errors = 0
        phase_counts: Dict[str, int] = defaultdict(int)

        for snap in snapshots:
            status_counts[snap.get("status", "unknown")] += 1
            total_duration += snap.get("duration_seconds", 0.0)
            total_errors += len(snap.get("errors", []))
            phase_counts[snap.get("phase", "unknown")] += 1

        return {
            "total_workflows": len(snapshots),
            "by_status": dict(status_counts),
            "by_phase": dict(phase_counts),
            "total_duration_seconds": round(total_duration, 2),
            "total_errors": total_errors,
            "avg_duration_per_workflow": (
                round(total_duration / len(snapshots), 2)
                if snapshots else 0.0
            ),
            "event_count": len(self._events),
            "active_instances": len([
                s for s in snapshots
                if s.get("status") not in ("completed", "failed", "cancelled")
            ]),
        }

    def get_workflow_summary(
        self, workflow_id: str
    ) -> Dict[str, Any]:
        """Get a summary of all executions of a specific workflow."""
        snapshots = [
            s for s in self._snapshots.values()
            if s.get("workflow_id") == workflow_id
        ]

        if not snapshots:
            return {"workflow_id": workflow_id, "executions": 0}

        completed = [s for s in snapshots if s.get("status") == "completed"]
        failed = [s for s in snapshots if s.get("status") == "failed"]

        return {
            "workflow_id": workflow_id,
            "executions": len(snapshots),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": (
                round(len(completed) / len(snapshots) * 100, 1)
                if snapshots else 0.0
            ),
            "avg_duration": (
                round(
                    sum(s.get("duration_seconds", 0.0) for s in snapshots)
                    / len(snapshots), 2
                ) if snapshots else 0.0
            ),
            "last_execution": snapshots[-1].get("completed_at") if snapshots else None,
            "total_errors": sum(len(s.get("errors", [])) for s in snapshots),
        }

    # ── Dashboard Helpers ──────────────────────────────────────────

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Return a dashboard-ready data structure."""
        active = self.get_all_snapshots(
            status="running",
        ) if "running" in {s.get("status") for s in self._snapshots.values()} else []

        return {
            "stats": self.get_aggregate_stats(),
            "active_workflows": active[:20],
            "recent_events": self.get_events(limit=50),
            "phase_averages": {
                phase.value: round(self.get_average_phase_time(phase.value), 2)
                for phase in AutonomousLifecyclePhase
                if self.get_average_phase_time(phase.value) > 0
            },
        }

    # ── Reset ──────────────────────────────────────────────────────

    def reset(self) -> None:
        """Clear all observability data."""
        self._snapshots.clear()
        self._events.clear()
        self._phase_timings.clear()
        self._subscriptions.clear()