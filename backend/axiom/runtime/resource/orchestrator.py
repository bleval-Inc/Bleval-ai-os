"""Runtime Orchestrator — Coordinates resource-aware runtime with executive loops and integration layer."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from pydantic import BaseModel, Field

from axiom.runtime.logging import RuntimeLogger
from axiom.runtime.resource.monitor import ResourceMonitor, ResourceMetrics, AlertRule
from axiom.runtime.resource.scheduler import ResourceScheduler, TaskPriority, ScheduledTask
from axiom.runtime.resource.quotas import QuotaManager, QuotaConfig, QuotaScope, QuotaType


class OrchestratorConfig(BaseModel):
    """Orchestrator configuration."""

    # Resource monitoring
    monitor_interval: int = 30
    alert_rules: List[AlertRule] = Field(default_factory=list)

    # Scheduler
    max_concurrent_tasks: int = 10
    default_task_timeout: int = 3600  # seconds

    # Quotas
    quota_config: QuotaConfig = Field(default_factory=QuotaConfig)

    # Executive integration
    executive_refresh_interval: int = 60  # seconds
    executive_max_concurrent: int = 3

    # Integration layer
    integration_health_check_interval: int = 300  # seconds

    # Auto-scaling
    auto_scale_enabled: bool = True
    scale_up_threshold: float = 80.0  # CPU %
    scale_down_threshold: float = 30.0  # CPU %


class RuntimeState(BaseModel):
    """Runtime state snapshot."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    healthy: bool = True

    # Resource state
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    gpu_available: bool = False

    # Scheduler state
    queued_tasks: int = 0
    running_tasks: int = 0
    available_slots: int = 0

    # Quota state
    quota_violations: int = 0

    # Executive state
    executive_status: Dict[str, str] = Field(default_factory=dict)

    # Integration state
    integration_health: Dict[str, bool] = Field(default_factory=dict)


class RuntimeOrchestrator:
    """Orchestrates the resource-aware runtime."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        logger: Optional[RuntimeLogger] = None,
        event_engine=None,
        integration_layer=None,
        database_manager=None,
        executive_loops=None,  # Dict of executive name -> loop instance
    ):
        self.config = config or OrchestratorConfig()
        self.logger = logger or RuntimeLogger()

        self.event_engine = event_engine
        self.integration_layer = integration_layer
        self.database_manager = database_manager
        self.executive_loops = executive_loops or {}

        # Core components
        self.monitor = ResourceMonitor(
            interval_seconds=self.config.monitor_interval,
            alert_rules=self.config.alert_rules,
        )
        self.scheduler = ResourceScheduler(
            monitor=self.monitor,
            max_concurrent=self.config.max_concurrent_tasks,
        )
        self.quota_manager = QuotaManager(config=self.config.quota_config)

        # State
        self._running = False
        self._orchestrator_task: Optional[asyncio.Task] = None
        self._state_history: List[RuntimeState] = []
        self._max_history = 100

        # Callbacks
        self._on_state_change: List[Callable[[RuntimeState], Any]] = []

        # Setup scheduler callbacks
        self.scheduler.on_task_start(self._on_scheduler_task_start)
        self.scheduler.on_task_complete(self._on_scheduler_task_complete)
        self.scheduler.on_task_failed(self._on_scheduler_task_failed)

        # Setup monitor callbacks
        self.monitor.add_callback(self._on_resource_alert)

    def on_state_change(self, callback: Callable[[RuntimeState], Any]):
        """Register state change callback."""
        self._on_state_change.append(callback)

    async def start(self):
        """Start the orchestrator."""
        if self._running:
            return

        self.logger.info("runtime_orchestrator", "Starting Runtime Orchestrator...")

        # Start components
        await self.monitor.start()
        await self.scheduler.start()

        # Start orchestrator loop
        self._running = True
        self._orchestrator_task = asyncio.create_task(self._orchestrator_loop())

        self.logger.info("runtime_orchestrator", "Runtime Orchestrator started")

    async def stop(self):
        """Stop the orchestrator."""
        self.logger.info("runtime_orchestrator", "Stopping Runtime Orchestrator...")
        self._running = False

        if self._orchestrator_task:
            self._orchestrator_task.cancel()
            try:
                await self._orchestrator_task
            except asyncio.CancelledError:
                pass

        await self.scheduler.stop(wait=True)
        await self.monitor.stop()

        self.logger.info("runtime_orchestrator", "Runtime Orchestrator stopped")

    async def _orchestrator_loop(self):
        """Main orchestrator loop."""
        while self._running:
            try:
                # Collect state
                state = await self._collect_state()
                self._state_history.append(state)
                if len(self._state_history) > self._max_history:
                    self._state_history.pop(0)

                # Trigger state change callbacks
                for cb in self._on_state_change:
                    try:
                        cb(state)
                    except Exception as e:
                        self.logger.error("runtime_orchestrator", f"State change callback error: {e}")

                # Check quotas for executives
                await self._check_executive_quotas()

                # Health check integrations
                await self._check_integration_health()

                # Auto-scaling
                if self.config.auto_scale_enabled:
                    await self._auto_scale(state)

                # Refresh executives
                await self._refresh_executives()

                # Emit state event
                if self.event_engine:
                    from axiom.models.events import Event
                    import uuid
                    await self.event_engine.publish(
                        Event(
                            event_id=str(uuid.uuid4()),
                            event_type="runtime.state",
                            source="runtime.orchestrator",
                            channel="system",
                            payload=state.model_dump(),
                            timestamp=datetime.utcnow(),
                        )
                    )

                await asyncio.sleep(self.config.executive_refresh_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("runtime_orchestrator", f"Orchestrator loop error: {e}")
                await asyncio.sleep(5)

    async def _collect_state(self) -> RuntimeState:
        """Collect current runtime state."""
        metrics = self.monitor.get_current()
        scheduler_status = self.scheduler.get_queue_status()

        # Count recent quota violations
        violations = self.quota_manager.get_violations(since=datetime.utcnow() - timedelta(minutes=5))

        # Get executive statuses
        executive_status = {}
        for name, loop in self.executive_loops.items():
            executive_status[name] = "running" if getattr(loop, "_running", False) else "stopped"

        # Get integration health
        integration_health = {}
        if self.integration_layer:
            # Would check each integration
            pass

        return RuntimeState(
            timestamp=datetime.utcnow(),
            healthy=metrics.cpu_percent < 90 and metrics.memory_percent < 90 if metrics else True,
            cpu_percent=metrics.cpu_percent if metrics else 0.0,
            memory_percent=metrics.memory_percent if metrics else 0.0,
            disk_percent=metrics.disk_percent if metrics else 0.0,
            gpu_available=metrics.gpu_available if metrics else False,
            queued_tasks=scheduler_status["queued"],
            running_tasks=scheduler_status["running"],
            available_slots=scheduler_status["available_slots"],
            quota_violations=len(violations),
            executive_status=executive_status,
            integration_health=integration_health,
        )

    async def _check_executive_quotas(self):
        """Check and enforce quotas for executive loops."""
        for name, loop in self.executive_loops.items():
            # Check org-level quota
            allowed, violation = await self.quota_manager.check_quota(
                QuotaScope.ORGANIZATION,
                name,
                QuotaType.CONCURRENT_TASKS,
                1.0,
            )
            if not allowed:
                self.logger.warning("runtime_orchestrator", f"Executive {name} quota exceeded: {violation}")

    async def _check_integration_health(self):
        """Check health of all integrations."""
        if not self.integration_layer:
            return

        # Would call integration_layer.health_check()
        pass

    async def _auto_scale(self, state: RuntimeState):
        """Auto-scale based on resource usage."""
        # Scale up scheduler concurrency
        if state.cpu_percent > self.config.scale_up_threshold:
            if self.scheduler.max_concurrent < 50:  # Max limit
                self.scheduler.max_concurrent += 1
                self.logger.info("runtime_orchestrator", f"Scaled up: max_concurrent={self.scheduler.max_concurrent}")

        # Scale down
        elif state.cpu_percent < self.config.scale_down_threshold:
            if self.scheduler.max_concurrent > 5:  # Min limit
                self.scheduler.max_concurrent -= 1
                self.logger.info("runtime_orchestrator", f"Scaled down: max_concurrent={self.scheduler.max_concurrent}")

    async def _refresh_executives(self):
        """Trigger executive loop refresh if needed."""
        for name, loop in self.executive_loops.items():
            if hasattr(loop, "trigger_refresh"):
                try:
                    await loop.trigger_refresh()
                except Exception as e:
                    self.logger.error("runtime_orchestrator", f"Executive {name} refresh failed: {e}")

    def _on_scheduler_task_start(self, task: ScheduledTask):
        """Handle task start."""
        # Consume concurrent task quota
        asyncio.create_task(
            self.quota_manager.consume_quota(
                QuotaScope.AGENT,
                getattr(task, "agent_id", "default"),
                QuotaType.CONCURRENT_TASKS,
                1.0,
            )
        )

        if self.event_engine:
            from axiom.runtime.events import Event
            asyncio.create_task(
                self.event_engine.publish(
                    Event(
                        name="task.started",
                        payload={"task_id": task.id, "name": task.name},
                        source="runtime.orchestrator",
                    )
                )
            )

    def _on_scheduler_task_complete(self, task: ScheduledTask):
        """Handle task completion."""
        # Release concurrent task quota
        asyncio.create_task(
            self.quota_manager.release_quota(
                QuotaScope.AGENT,
                getattr(task, "agent_id", "default"),
                QuotaType.CONCURRENT_TASKS,
                1.0,
            )
        )

        if self.event_engine:
            from axiom.runtime.events import Event
            asyncio.create_task(
                self.event_engine.publish(
                    Event(
                        name="task.completed",
                        payload={"task_id": task.id, "name": task.name, "result": str(task.result)[:100]},
                        source="runtime.orchestrator",
                    )
                )
            )

    def _on_scheduler_task_failed(self, task: ScheduledTask, error: Exception):
        """Handle task failure."""
        # Release concurrent task quota
        asyncio.create_task(
            self.quota_manager.release_quota(
                QuotaScope.AGENT,
                getattr(task, "agent_id", "default"),
                QuotaType.CONCURRENT_TASKS,
                1.0,
            )
        )

        if self.event_engine:
            from axiom.runtime.events import Event
            asyncio.create_task(
                self.event_engine.publish(
                    Event(
                        name="task.failed",
                        payload={"task_id": task.id, "name": task.name, "error": str(error)},
                        source="runtime.orchestrator",
                    )
                )
            )

    def _on_resource_alert(self, alert):
        """Handle resource alert."""
        self.logger.warning("runtime_orchestrator", f"Resource alert: {alert.level} - {alert.message}")

        if self.event_engine:
            from axiom.runtime.events import Event
            asyncio.create_task(
                self.event_engine.publish(
                    Event(
                        name="resource.alert",
                        payload=alert.model_dump(),
                        source="runtime.orchestrator",
                    )
                )
            )

        # Throttle/halt on critical
        if alert.level == "critical":
            self.logger.error("runtime_orchestrator", f"Critical resource alert: {alert.message}")
            # Could trigger emergency actions

    # Public API for scheduling tasks

    def schedule_task(
        self,
        name: str,
        coro: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        agent_id: Optional[str] = None,
        org_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Schedule a task with resource awareness."""
        # Check quotas before scheduling
        # This is async but we schedule sync; actual check happens at execution

        task = ScheduledTask(
            name=name,
            coro=coro,
            priority=priority,
            **kwargs
        )
        if agent_id:
            task.metadata["agent_id"] = agent_id
        if org_id:
            task.metadata["org_id"] = org_id

        return self.scheduler.schedule(task)

    def schedule_executive_task(
        self,
        executive: str,
        name: str,
        coro: Callable,
        priority: TaskPriority = TaskPriority.HIGH,
        **kwargs
    ) -> str:
        """Schedule a task for an executive loop."""
        return self.schedule_task(
            name=f"{executive}:{name}",
            coro=coro,
            priority=priority,
            agent_id=executive,
            org_id=executive,
            **kwargs
        )

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "running": self._running,
            "monitor": {
                "running": self.monitor._running,
                "interval": self.monitor.interval,
            },
            "scheduler": self.scheduler.get_queue_status(),
            "quotas": {
                "violations_recent": len(
                    self.quota_manager.get_violations(since=datetime.utcnow() - timedelta(hours=1))
                ),
            },
            "executives": {
                name: "running" if getattr(loop, "_running", False) else "stopped"
                for name, loop in self.executive_loops.items()
            },
        }

    def get_state_history(self, limit: int = 50) -> List[RuntimeState]:
        """Get recent state history."""
        return self._state_history[-limit:]

    async def get_quota_status(self, scope: QuotaScope, scope_id: str) -> Dict[str, Any]:
        """Get quota status for scope."""
        return await self.quota_manager.get_quota_status(scope, scope_id)

    async def execute_with_quota(
        self,
        scope: QuotaScope,
        scope_id: str,
        quota_type: QuotaType,
        amount: float,
        coro: Callable,
    ) -> Any:
        """Execute coroutine with quota check."""
        allowed, violation = await self.quota_manager.check_quota(scope, scope_id, quota_type, amount)
        if not allowed:
            raise RuntimeError(f"Quota exceeded: {violation}")

        await self.quota_manager.consume_quota(scope, scope_id, quota_type, amount)
        try:
            return await coro()
        finally:
            if quota_type == QuotaType.CONCURRENT_TASKS:
                await self.quota_manager.release_quota(scope, scope_id, quota_type, amount)