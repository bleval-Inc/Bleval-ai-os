"""Scheduler — cron-based event scheduling.

The scheduler reads scheduled event definitions and fires events on a
configurable interval.  It uses a simple polling loop rather than an
external cron daemon.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class Scheduler:
    """Schedules recurring events and triggers workflows on a timer."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._schedules: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the scheduler background loop."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def add_schedule(
        self,
        event_type: str,
        cron_expression: str,
        payload: Optional[Dict[str, Any]] = None,
        workflow_to_trigger: Optional[str] = None,
    ) -> None:
        """Register a recurring scheduled event.

        cron_expression format: "second minute hour day month weekday"
        (all fields required, space-separated).
        """
        self._schedules.append({
            "event_type": event_type,
            "cron_expression": cron_expression,
            "payload": payload or {},
            "workflow_to_trigger": workflow_to_trigger,
            "last_fired": None,
        })

    def remove_schedule(self, event_type: str) -> None:
        """Remove all schedules for a given event type."""
        self._schedules = [s for s in self._schedules if s["event_type"] != event_type]

    def list_schedules(self) -> List[Dict[str, Any]]:
        """Return all registered schedules."""
        return list(self._schedules)

    async def _run_loop(self) -> None:
        """Background loop that checks schedules every 60 seconds."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                for schedule in self._schedules:
                    if self._should_fire(schedule, now):
                        await self._fire(schedule, now)
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)

    def _should_fire(self, schedule: Dict[str, Any], now: datetime) -> bool:
        """Check if a schedule should fire at the given time.

        Uses a simple minute-level check.  Full cron parsing is a future
        enhancement.
        """
        last_fired = schedule.get("last_fired")
        if last_fired is None:
            # First run — fire immediately
            return True
        elapsed = (now - last_fired).total_seconds()
        return elapsed >= 3600  # Default: once per hour

    async def _fire(self, schedule: Dict[str, Any], now: datetime) -> None:
        """Execute a scheduled event."""
        schedule["last_fired"] = now

        event_engine = getattr(self._runtime, "event", None)
        if event_engine is not None and hasattr(event_engine, "publish"):
            try:
                await event_engine.publish(
                    event_type=schedule["event_type"],
                    source="scheduler",
                    payload=schedule["payload"],
                )
            except Exception:
                pass

        # Also trigger a workflow if configured
        wf_id = schedule.get("workflow_to_trigger")
        if wf_id:
            wf_engine = getattr(self._runtime, "workflow", None)
            if wf_engine is not None and hasattr(wf_engine, "create_instance"):
                try:
                    instance = wf_engine.create_instance(
                        workflow_id=wf_id,
                        context={"trigger": "scheduler", "scheduled_at": now.isoformat()},
                    )
                    # Fire-and-forget start
                    asyncio.create_task(wf_engine.start(instance.instance_id))
                except Exception:
                    pass