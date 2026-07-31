"""Lifecycle Manager — system bootstrap, runtime orchestration, and graceful shutdown.

The AxiomRuntime is the central orchestrator.  It initialises all engines and
runtime subsystems, starts background processors, and provides a unified
interface for the API layer and CLI.

Integration wiring performed during bootstrap:
  - WorkflowEngine ← EventEngine (for event emissions)
  - WorkflowEngine ← Dispatcher (for task dispatching on step start)
  - EventEngine → auto-launch workflows on trigger_event matches
  - Dispatcher → auto-advance workflow on task completion
"""

import asyncio
from typing import Any, Dict, List, Optional

from axiom.config import settings
from axiom.engine.event import EventEngine
from axiom.engine.executive import ExecutiveEngine
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.learning import LearningEngine
from axiom.engine.memory import MemoryEngine
from axiom.engine.tool import ToolEngine
from axiom.engine.workflow import WorkflowEngine
from axiom.runtime.approval import ApprovalManager
from axiom.runtime.dispatcher import Dispatcher
from axiom.runtime.executive_loop import ExecutiveBoard
from axiom.runtime.logging import RuntimeLogger
from axiom.runtime.monitor import HealthMonitor
from axiom.runtime.recovery import RecoveryManager
from axiom.runtime.scheduler import Scheduler

# JARVIS modules — system telemetry, adaptive greetings, function-calling tools
from axiom.runtime.system_monitor import SystemMonitor
from axiom.runtime.greeting_engine import GreetingEngine
from axiom.runtime.system_tools import SystemTools


class AxiomRuntime:
    """Central runtime orchestrator for Axiom OS.

    Initialises all engines, wires cross-component integration,
    manages background tasks, and provides a unified interface
    for the API and CLI layers.
    """

    def __init__(self) -> None:
        self._initialised = False
        self._running = False

        # Engines (lazily initialised)
        self.memory: Optional[MemoryEngine] = None
        self.event: Optional[EventEngine] = None
        self.tool: Optional[ToolEngine] = None
        self.workflow: Optional[WorkflowEngine] = None
        self.executive: Optional[ExecutiveEngine] = None
        self.intelligence: Optional[IntelligenceEngine] = None
        self.learning: Optional[LearningEngine] = None

        # Runtime subsystems
        self.scheduler: Optional[Scheduler] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.monitor: Optional[HealthMonitor] = None
        self.recovery: Optional[RecoveryManager] = None
        self.approval: Optional[ApprovalManager] = None
        self.executive_board: Optional[ExecutiveBoard] = None
        self.logger: Optional[RuntimeLogger] = None

        # JARVIS modules (system telemetry, greetings, function-calling)
        self.system_monitor: Optional[SystemMonitor] = None
        self.greeting_engine: Optional[GreetingEngine] = None
        self.system_tools: Optional[SystemTools] = None

    # ── Bootstrap ────────────────────────────────────────────────────────

    async def bootstrap(self) -> None:
        """Initialise all engines and wire cross-component integration.

        Called once at system startup.
        """
        if self._initialised:
            return

        # Ensure runtime directories exist
        settings.ensure_dirs()

        # Logger first (used by all other components)
        self.logger = RuntimeLogger()

        # Initialise engines in dependency order
        self.memory = MemoryEngine()
        self.tool = ToolEngine()
        self.executive = ExecutiveEngine()
        # Intelligence engine with memory + tool integration
        self.intelligence = IntelligenceEngine(
            memory=self.memory,
            tool=self.tool,
        )

        # Event engine (must be created before WorkflowEngine so we can wire it)
        self.event = EventEngine()

        # Workflow engine with event + dispatcher wiring
        self.workflow = WorkflowEngine(
            event_engine=self.event,
            dispatcher=None,  # Set after dispatcher is created (circular ref)
        )

        # Runtime subsystems (get runtime reference)
        self.scheduler = Scheduler(self)
        self.dispatcher = Dispatcher(self)
        self.monitor = HealthMonitor(self)
        self.recovery = RecoveryManager(self)
        self.approval = ApprovalManager(self)

        # Wire cross-references after all components exist
        self.workflow.set_dispatcher(self.dispatcher)

        # Wire approval manager two-way with workflow engine
        self.approval.set_workflow_engine(self.workflow)
        self.workflow.set_approval_manager(self.approval)

        # Executive Board — autonomous executive runtime loops
        self.executive_board = ExecutiveBoard(self)

        # Learning Engine — continuous learning (observes all executions)
        self.learning = LearningEngine(runtime=self)

        # JARVIS modules — system telemetry, adaptive greetings, function-calling tools
        self.system_monitor = SystemMonitor(logger=self.logger)
        self.greeting_engine = GreetingEngine(
            monitor=self.system_monitor,
            logger=self.logger,
        )
        self.system_tools = SystemTools(
            runtime=self,
            logger=self.logger,
        )

        self._initialised = True

        if self.logger:
            self.logger.info("lifecycle", "Axiom OS runtime initialised")

    async def start(self) -> None:
        """Start all background processors and wire event subscriptions."""
        if self._running:
            return

        await self.bootstrap()

        # Start event engine first (background pub/sub processor)
        if self.event:
            await self.event.start()
            # Wire event → workflow auto-launch subscriptions
            await self._wire_event_workflow_auto_launch()

        # Start scheduler (background cron loop)
        if self.scheduler:
            await self.scheduler.start()

        # Start dispatcher (background task processing)
        if self.dispatcher:
            await self.dispatcher.start()

        # Start learning engine (background consolidation loop + event subscriptions)
        if self.learning:
            await self._wire_learning_engine()
            await self.learning.start()

        # Start health monitor (background health checks)
        if self.monitor:
            await self.monitor.start()

        # Initialise system monitor (JARVIS telemetry — async sensor detection)
        if self.system_monitor:
            await self.system_monitor.initialise()

        # Wire system tools into the intelligence engine for function-calling
        if self.system_tools and self.intelligence:
            await self._wire_system_tools()

        # Load any persisted workflow state from disk
        if self.workflow:
            persisted = self.workflow.load_all_persisted()
            if self.logger:
                self.logger.info(
                    "lifecycle",
                    f"Loaded {len(persisted)} persisted workflow instances",
                )

        # Start Executive Board (autonomous executive runtime loops)
        if self.executive_board:
            await self.executive_board.start_all()

        self._running = True

        if self.logger:
            self.logger.info("lifecycle", "Axiom OS runtime started")

    async def shutdown(self) -> None:
        """Graceful shutdown of all background processors."""
        self._running = False

        if self.logger:
            self.logger.info("lifecycle", "Axiom OS runtime shutting down")

        # Stop in reverse order
        if self.system_monitor:
            await self.system_monitor.shutdown()

        if self.executive_board:
            await self.executive_board.stop_all()

        if self.monitor:
            await self.monitor.stop()

        if self.learning:
            await self.learning.stop()

        if self.scheduler:
            await self.scheduler.stop()

        if self.dispatcher:
            await self.dispatcher.stop()

        if self.event:
            await self.event.stop()

        if self.logger:
            self.logger.info("lifecycle", "Axiom OS runtime stopped")

    # ── Event → Workflow Auto-Launch ────────────────────────────────────

    async def _wire_event_workflow_auto_launch(self) -> None:
        """Subscribe to all event types that have matching workflow triggers.

        When a matching event fires, auto-create and start a workflow instance.
        """
        if not self.event or not self.workflow:
            return

        workflows = self.workflow.list_workflows()
        subscribed = 0

        for wf_id, wf_def in workflows.items():
            trigger = getattr(wf_def, "trigger_event", None) or getattr(wf_def, "triggers_on", None)
            if not trigger:
                continue

            # Capture wf_id and wf_def in the closure via default arguments
            async def _on_event(
                event: Any,
                _wf_id: str = wf_id,
                _wf_def: Any = wf_def,
            ) -> None:
                """Callback: auto-launch workflow when trigger event fires."""
                await self._auto_launch_workflow(_wf_id, _wf_def, event)

            try:
                self.event.subscribe_to_event(trigger, _on_event)
                subscribed += 1
            except ValueError:
                continue

        if self.logger:
            self.logger.info(
                "lifecycle",
                f"Subscribed {subscribed} workflow triggers (event → auto-launch)",
            )

    async def _auto_launch_workflow(
        self,
        wf_id: str,
        wf_def: Any,
        event: Any,
    ) -> None:
        """Create and start a workflow instance triggered by an event."""
        if not self.workflow:
            return
        try:
            context = {
                "trigger": "event",
                "trigger_event": event.event_type if hasattr(event, "event_type") else "",
                "event_id": event.event_id if hasattr(event, "event_id") else "",
                "event_payload": event.payload if hasattr(event, "payload") else {},
            }
            instance = self.workflow.create_instance(wf_id, context=context)
            await self.workflow.start(instance.instance_id)
            if self.logger:
                self.logger.info(
                    "workflow",
                    f"Auto-launched {wf_id} from event {event.event_type} "
                    f"(instance: {instance.instance_id})",
                )
        except Exception as exc:
            if self.logger:
                self.logger.error(
                    "workflow",
                    f"Failed to auto-launch {wf_id} from event: {exc}",
                )

    # ── Learning Engine Wiring ──────────────────────────────────────────

    async def _wire_learning_engine(self) -> None:
        """Wire the Learning Engine to observe all execution events.

        The Learning Engine subscribes to workflow lifecycle events (started,
        completed, failed) and agent task events through the Event Engine.
        This is event-driven observation — no direct component coupling.

        Additionally, the dispatcher is instrumented to notify the Learning
        Engine on task completion, and the executive board records cycles.
        """
        if not self.event or not self.learning:
            return

        engine = self.learning

        async def _on_workflow_completed(event: Any) -> None:
            """Record learning data when a workflow completes."""
            if not event or not hasattr(event, "event_type"):
                return
            wf_status = ""
            if event.event_type == "workflow-completed":
                wf_status = "completed"
            elif event.event_type == "workflow-failed":
                wf_status = "failed"
            elif event.event_type == "workflow-cancelled":
                wf_status = "cancelled"

            payload = getattr(event, "payload", {}) or {}
            instance_id = payload.get("instance_id", "")
            workflow_id = payload.get("workflow_id", "unknown")

            # Look up the workflow instance for detailed data
            wf_instance = None
            if self.workflow:
                try:
                    wf_instance = self.workflow.get_instance(instance_id)
                except Exception:
                    pass

            total_steps = 0
            completed_steps = 0
            failed_steps = 0
            retries = 0
            approval_requests = 0
            agents_involved = []
            error = payload.get("error", "")

            if wf_instance:
                total_steps = len(wf_instance.steps)
                completed_steps = sum(
                    1 for s in wf_instance.steps
                    if hasattr(s, "status") and s.status in ("completed", "COMPLETED")
                )
                failed_steps = sum(
                    1 for s in wf_instance.steps
                    if hasattr(s, "status") and s.status in ("failed", "FAILED")
                )
                retries = sum(
                    getattr(s, "retry_count", 0) for s in wf_instance.steps
                ) if wf_instance.steps else 0

            await engine.record_workflow_execution(
                workflow_id=workflow_id,
                instance_id=instance_id or event.event_id,
                status=wf_status,
                total_steps=max(total_steps, 1),
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                retries=retries,
                agents_involved=agents_involved,
                org=payload.get("org", ""),
                department=payload.get("department", ""),
                error=error,
            )

        async def _on_workflow_started(event: Any) -> None:
            """Track workflow start time."""
            pass  # Learning happens on completion, not start

        # Subscribe to workflow lifecycle events through the event engine
        for event_type in ("workflow-completed", "workflow-failed", "workflow-cancelled"):
            try:
                self.event.subscribe_to_event(event_type, _on_workflow_completed)
            except ValueError:
                pass  # Event type may not be registered yet

        # Also wire the dispatcher for agent task learning
        if self.dispatcher:
            original_execute = self.dispatcher._execute_task

            async def _instrumented_execute(task: Any) -> None:
                """Execute a task and record learning data."""
                import time
                start_time = time.monotonic()
                original_retries = getattr(task, "retry_count", 0)

                try:
                    await original_execute(task)
                    duration = time.monotonic() - start_time
                    success = getattr(task, "status", None) in (
                        "completed", "COMPLETED",
                    ) if hasattr(task, "status") else True
                    await engine.record_agent_task(
                        agent_id=getattr(task, "agent_id", ""),
                        success=success,
                        duration=duration,
                        retries=original_retries,
                        action=getattr(task, "action", ""),
                        task_id=getattr(task, "task_id", ""),
                        workflow_instance_id=getattr(task, "workflow_instance_id", ""),
                        error=getattr(task, "error", None),
                    )
                except Exception:
                    duration = time.monotonic() - start_time
                    await engine.record_agent_task(
                        agent_id=getattr(task, "agent_id", ""),
                        success=False,
                        duration=duration,
                        retries=original_retries,
                        action=getattr(task, "action", ""),
                        task_id=getattr(task, "task_id", ""),
                        workflow_instance_id=getattr(task, "workflow_instance_id", ""),
                        error="Task execution raised exception",
                    )
                    raise

            self.dispatcher._execute_task = _instrumented_execute  # type: ignore[method-assign]

        # Wire executive board for learning
        if self.executive_board:
            for exec_id in self.executive_board.EXECUTIVE_IDS:
                loop = self.executive_board.get_loop(exec_id)
                if loop:
                    original_cycle = loop._execute_cycle

                    async def _make_instrumented_cycle(
                        _exec_id: str = exec_id,
                        _orig: Any = original_cycle,
                    ) -> Any:
                        """Execute a cycle and record learning data."""
                        import time
                        start = time.monotonic()
                        try:
                            result = await _orig(exec_id) if callable(_orig) else None
                            # Re-derive the exec_id from closure; _exec_id is stable
                            duration = time.monotonic() - start
                            await engine.record_executive_cycle(
                                exec_id=_exec_id,
                                decision_type="cycle",
                                outcome="success",
                                duration=duration,
                                reasoning="Executive cycle completed successfully",
                            )
                            return result
                        except Exception as exc:
                            duration = time.monotonic() - start
                            await engine.record_executive_cycle(
                                exec_id=_exec_id,
                                decision_type="cycle",
                                outcome="failure",
                                duration=duration,
                                reasoning=f"Executive cycle failed: {exc}",
                            )
                            raise

                    loop._execute_cycle = _make_instrumented_cycle

        if self.logger:
            self.logger.info(
                "lifecycle",
                "Learning Engine wired to observe workflow, agent, and executive events",
            )

    async def _wire_system_tools(self) -> None:
        """Wire system tools into the intelligence engine's context builder.

        This enables the AI to access OS-level function-calling tools
        (get_telemetry, launch_application, execute_shell, etc.) during
        reasoning cycles — forming the JARVIS-like agentic bridge.
        """
        if not self.system_tools or not self.intelligence:
            return

        # Add tool schemas to the context builder for prompt assembly
        if hasattr(self.intelligence, "_context_builder"):
            cb = self.intelligence._context_builder
            tool_schemas = self.system_tools.get_tool_schemas()
            if hasattr(cb, "set_tool_schemas"):
                cb.set_tool_schemas(tool_schemas)

        if self.logger:
            tools_count = len(self.system_tools.list_tools())
            self.logger.info(
                "lifecycle",
                f"System tools wired: {tools_count} tools available for AI function-calling",
            )

    # ── Status ───────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_initialised(self) -> bool:
        return self._initialised

    def get_status(self) -> Dict[str, Any]:
        """Return a status summary of the runtime and all components."""
        return {
            "version": "3.0.0",
            "initialised": self._initialised,
            "running": self._running,
            "components": {
                "memory": self.memory is not None,
                "event": self.event is not None,
                "tool": self.tool is not None,
                "workflow": self.workflow is not None,
                "executive": self.executive is not None,
                "intelligence": self.intelligence is not None,
                "scheduler": self.scheduler is not None,
                "dispatcher": self.dispatcher is not None,
                "monitor": self.monitor is not None,
                "recovery": self.recovery is not None,
                "approval": self.approval is not None,
                "executive_board": self.executive_board is not None,
                "logger": self.logger is not None,
                "learning": self.learning is not None,
            },
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return a rich summary of the runtime state."""
        status = self.get_status()
        monitor_summary = self.monitor.get_summary() if self.monitor else {}
        workflows = self.workflow.list_workflows() if self.workflow else {}
        agents = self.executive.list_executives() if self.executive else []
        orgs = self.executive.list_organizations() if self.executive else []

        return {
            **status,
            "health": monitor_summary,
            "workflows_defined": len(workflows),
            "executives": len(agents),
            "org_count": len(orgs),
        }