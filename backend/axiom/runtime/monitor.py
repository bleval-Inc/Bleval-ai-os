"""Health Monitor — component health checks and system observability.

Periodically checks the health of all runtime components and reports
status.  Integrates with the logging system for observability.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.models.runtime import ComponentHealth, HealthStatus


class HealthMonitor:
    """Monitors the health of all runtime components."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._components: Dict[str, ComponentHealth] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._interval = 60  # seconds

    async def start(self) -> None:
        """Start the health check background loop."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the health monitor."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def set_interval(self, seconds: int) -> None:
        """Set the health check interval."""
        self._interval = max(10, seconds)

    def report_health(self, component: str, status: HealthStatus, details: Optional[Dict[str, Any]] = None) -> None:
        """Manually report component health."""
        self._components[component] = ComponentHealth(
            component=component,
            status=status,
            last_check=datetime.now(timezone.utc),
            details=details or {},
        )

    def get_component_health(self, component: str) -> Optional[ComponentHealth]:
        """Get the health status of a specific component."""
        return self._components.get(component)

    def get_all_health(self) -> List[ComponentHealth]:
        """Get the health status of all components."""
        return list(self._components.values())

    def is_healthy(self) -> bool:
        """Return True if all components are healthy or degraded (not unhealthy)."""
        for component in self._components.values():
            if component.status == HealthStatus.UNHEALTHY:
                return False
        return True

    def get_summary(self) -> Dict[str, Any]:
        """Return a health summary."""
        total = len(self._components)
        healthy = sum(1 for c in self._components.values() if c.status == HealthStatus.HEALTHY)
        degraded = sum(1 for c in self._components.values() if c.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for c in self._components.values() if c.status == HealthStatus.UNHEALTHY)
        return {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "overall": HealthStatus.HEALTHY if unhealthy == 0 else HealthStatus.UNHEALTHY,
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

    async def _run_loop(self) -> None:
        """Background loop that periodically checks component health."""
        while self._running:
            try:
                self._check_all()
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self._interval)

    def _check_all(self) -> None:
        """Check the health of all registered components."""
        runtime = self._runtime
        now = datetime.now(timezone.utc)

        components_to_check = [
            ("memory", runtime.memory if hasattr(runtime, "memory") else None),
            ("event", runtime.event if hasattr(runtime, "event") else None),
            ("tool", runtime.tool if hasattr(runtime, "tool") else None),
            ("workflow", runtime.workflow if hasattr(runtime, "workflow") else None),
            ("executive", runtime.executive if hasattr(runtime, "executive") else None),
            ("intelligence", runtime.intelligence if hasattr(runtime, "intelligence") else None),
            ("scheduler", runtime.scheduler if hasattr(runtime, "scheduler") else None),
            ("dispatcher", runtime.dispatcher if hasattr(runtime, "dispatcher") else None),
        ]

        for name, engine in components_to_check:
            status = HealthStatus.HEALTHY if engine is not None else HealthStatus.UNHEALTHY
            self._components[name] = ComponentHealth(
                component=name,
                status=status,
                last_check=now,
            )