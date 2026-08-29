"""Lifecycle Manager — system bootstrap, runtime orchestration, and graceful shutdown.

The AxiomRuntime is the central orchestrator.  It initialises all engines and
runtime subsystems, starts background processors, and provides a unified
interface for the API layer and CLI.

Integration wiring performed during bootstrap:
  - WorkflowEngine ← EventEngine (for event emissions)
  - WorkflowEngine ← Dispatcher (for task dispatching on step start)
  - EventEngine → auto-launch workflows on trigger_event matches
  - Dispatcher → auto-advance workflow on task completion

Phase C — Autonomous Workflow + Agent System (§1-§9):
  - SpecialistAgentEngine — specialist agent registry, dispatch, sessions
  - AutonomousWorkflowEngine — full lifecycle (PLAN→LEARN)
  - BackgroundExecutor — persistent background execution (§6)
  - WorkflowObserver — comprehensive observability (§7)
  - MultiModelEngine — capability-aware model routing (§4)
  - Failure handling with auto-recovery (§8)
"""

import asyncio
from typing import Any, Dict, List, Optional

from axiom.config import settings
from axiom.core.axiom_core import AXIOMCore
from axiom.core.research_workspace import ResearchWorkspaceManager
from axiom.engine.event import EventEngine
from axiom.engine.executive import ExecutiveEngine
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.learning import LearningEngine
from axiom.engine.market_intelligence import MarketIntelligenceEngine
from axiom.engine.memory import MemoryEngine
from axiom.engine.tool import ToolEngine
from axiom.engine.workflow import WorkflowEngine
from axiom.executive.fundamental_reporting import FundamentalReportingEngine
from axiom.runtime.approval import ApprovalManager
from axiom.runtime.board_room import BoardRoom
from axiom.runtime.communication import CommunicationCoordinator
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

# PHASE C — Autonomous Workflow + Agent System
from axiom.engine.specialist_agent import SpecialistAgentEngine
from axiom.engine.autonomous_workflow import AutonomousWorkflowEngine
from axiom.engine.multi_model import MultiModelEngine
from axiom.runtime.background_executor import BackgroundExecutor
from axiom.runtime.workflow_observer import WorkflowObserver

# PHASE D — Quality Control + Founder Authority
from axiom.runtime.founder_authority import FounderAuthority
from axiom.runtime.qc_engine import QCManager
from axiom.runtime.qc_handler import QCSpecialistHandler, QCTaskInspector
from axiom.runtime.founder_gateway import FounderGateway

# PHASE E — Executive Intelligence + QC Learning
from axiom.engine.executive_intelligence import ExecutiveIntelligence, ExecutiveGreeter
from axiom.engine.qc_learning_pipeline import QCtoLearningPipeline

# PHASE H — Platform Integrations
# Note: ProviderRegistry and providers imported lazily to avoid circular imports
# from axiom.engine.provider_registry import ProviderRegistry, get_provider_registry
# from axiom.integrations.github import GitHubProvider
# from axiom.integrations.market_data import MarketDataProvider
# from axiom.integrations.mt5 import MT5Provider
# from axiom.integrations.tradingview import TradingViewProvider
# from axiom.integrations.crm import CRMProvider
# from axiom.integrations.email import EmailProvider
# from axiom.integrations.calendar import CalendarProvider
# from axiom.integrations.slack import SlackProvider
# from axiom.integrations.whatsapp import WhatsAppProvider

# PHASE 1 — Unified Integration Layer
# Lazy import to avoid circular dependency with provider registry
# from axiom.integrations.layer import IntegrationLayer

# PHASE 7 — Resource-Aware Runtime
from axiom.runtime.resource import RuntimeOrchestrator, OrchestratorConfig

# PHASE 8 — Executive Integration
from axiom.runtime.executive_integration import ExecutiveIntegration, ExecutiveIntegrationConfig
from axiom.data.database import DatabaseManager
from axiom.engine.intelligence import IntelligenceEngine


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
        self.market_intelligence: Optional[MarketIntelligenceEngine] = None
        self.fundamental_reporting: Optional[FundamentalReportingEngine] = None
        self.data_manager = DatabaseManager()
        self.learning: Optional[LearningEngine] = None

        # Runtime subsystems
        self.scheduler: Optional[Scheduler] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.monitor: Optional[HealthMonitor] = None
        self.recovery: Optional[RecoveryManager] = None
        self.approval: Optional[ApprovalManager] = None
        self.executive_board: Optional[ExecutiveBoard] = None
        self.logger: Optional[RuntimeLogger] = None

        # Phase B — Autonomous Executive Layer
        self.board_room: Optional[BoardRoom] = None
        self.communication: Optional[CommunicationCoordinator] = None

        # JARVIS modules (system telemetry, greetings, function-calling)
        self.system_monitor: Optional[SystemMonitor] = None
        self.greeting_engine: Optional[GreetingEngine] = None
        self.system_tools: Optional[SystemTools] = None

        # PHASE C — Autonomous Workflow + Agent System
        self.specialist_engine: Optional[SpecialistAgentEngine] = None
        self.autonomous_workflow: Optional[AutonomousWorkflowEngine] = None
        self.multi_model: Optional[MultiModelEngine] = None
        self.background_executor: Optional[BackgroundExecutor] = None
        self.workflow_observer: Optional[WorkflowObserver] = None

        # PHASE D — Quality Control + Founder Authority
        self.qc_manager: Optional[QCManager] = None
        self.qc_inspector: Optional[QCTaskInspector] = None
        self.founder_authority: Optional[FounderAuthority] = None
        self.founder_gateway: Optional[FounderGateway] = None

        # AXIOM Core — top-level intelligence layer
        self.axiom: Optional[AXIOMCore] = None
        self.research: Optional[ResearchWorkspaceManager] = None

        # PHASE E — Executive Intelligence + QC Learning
        self.executive_intelligence: Optional[ExecutiveIntelligence] = None
        self.executive_greeter: Optional[ExecutiveGreeter] = None
        self.qc_learning_pipeline: Optional[QCtoLearningPipeline] = None

        # PHASE H — Platform Integrations
        self.provider_registry: Optional[ProviderRegistry] = None

        # PHASE 1 — Unified Integration Layer
        self.integration_layer: Optional[IntegrationLayer] = None

        # PHASE 7 — Resource-Aware Runtime
        self.runtime_orchestrator: Optional[RuntimeOrchestrator] = None

        # PHASE 8 — Executive Integration
        self.executive_integration: Optional[ExecutiveIntegration] = None

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
        # Market intelligence engine
        self.market_intelligence = MarketIntelligenceEngine(
            data_manager=self.data_manager,
            runtime=self,
        )
        # Fundamental reporting engine
        self.fundamental_reporting = FundamentalReportingEngine(
            data_manager=self.data_manager,
            market_intelligence=self.market_intelligence,
            executive_intelligence=self.intelligence,  # Temporary, will be updated after executive intelligence is created
        )

        # ── PHASE H: Provider Registry — Platform Integrations ─────────────

        # Initialise Provider Registry (lazy import to avoid circular deps)
        from axiom.engine.provider_registry import get_provider_registry
        self.provider_registry = get_provider_registry()

        # Register all integration providers (lazy imports)
        from axiom.integrations.github import GitHubProvider
        from axiom.integrations.market_data import MarketDataProvider
        from axiom.integrations.mt5 import MT5Provider
        from axiom.integrations.tradingview import TradingViewProvider
        from axiom.integrations.crm import CRMProvider
        from axiom.integrations.email import EmailProvider
        from axiom.integrations.calendar import CalendarProvider
        from axiom.integrations.slack import SlackProvider
        from axiom.integrations.whatsapp import WhatsAppProvider

        # Register provider implementations
        self.provider_registry.register_implementation("github", GitHubProvider)
        self.provider_registry.register_implementation("market_data", MarketDataProvider)
        self.provider_registry.register_implementation("mt5", MT5Provider)
        self.provider_registry.register_implementation("tradingview", TradingViewProvider)
        self.provider_registry.register_implementation("crm", CRMProvider)
        self.provider_registry.register_implementation("email", EmailProvider)
        self.provider_registry.register_implementation("calendar", CalendarProvider)
        self.provider_registry.register_implementation("slack", SlackProvider)
        self.provider_registry.register_implementation("whatsapp", WhatsAppProvider)

        # ── End PHASE H ───────────────────────────────────────────────────

        # ── PHASE 1: Unified Integration Layer ──────────────────────────────

        # Initialise Integration Layer with event engine (created next)
        # Note: IntegrationLayer will be fully initialized after event engine
        # We create a placeholder and initialize in start()

        # ── End PHASE 1 ────────────────────────────────────────────────────

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

        # Phase B — Board Room & Communication Coordinator
        self.board_room = BoardRoom(runtime=self)
        self.communication = CommunicationCoordinator(runtime=self)

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

        # ── PHASE C: Autonomous Workflow + Agent System ─────────────────

        # Specialist Agent Engine — specialist agent registry and runtime
        self.specialist_engine = SpecialistAgentEngine(
            intelligence=self.intelligence,
            tool=self.tool,
        )

        # Autonomous Workflow Engine — full lifecycle execution (§5)
        self.autonomous_workflow = AutonomousWorkflowEngine(
            base_workflow=self.workflow,
            intelligence=self.intelligence,
            specialist_engine=self.specialist_engine,
        )
        # Set default approval policies
        self.autonomous_workflow.set_default_policies()

        # Multi-Model Engine — capability-aware model routing (§4)
        self.multi_model = MultiModelEngine(
            intelligence_engine=self.intelligence,
        )

        # Workflow Observer — comprehensive observability (§7)
        self.workflow_observer = WorkflowObserver()

        # Background Executor — persistent background execution (§6)
        self.background_executor = BackgroundExecutor(runtime=self)

        # ── End PHASE C ─────────────────────────────────────────────────

        # ── PHASE D: Quality Control + Founder Authority ─────────────────

        # QC Manager — dedicated Quality Control engine
        self.qc_manager = QCManager(
            intelligence=self.intelligence,
        )

        # QC Task Inspector — inspects agent/workflow outputs
        self.qc_inspector = QCTaskInspector(
            qc_manager=self.qc_manager,
        )

        # Founder Authority — enforces Founder's final authority over
        # restricted actions: money, trades, contracts, deletion,
        # irreversible actions, external client comms, high-risk prospect
        # comms, public publishing, production deployment, major strategic
        self.founder_authority = FounderAuthority()

        # Founder Gateway — orchestrates the full approval pipeline:
        #   Executive researches → plans → Founder approves → executes
        #   → tests → QC → executive review → Founder final review → publish
        self.founder_gateway = FounderGateway(
            founder_authority=self.founder_authority,
            qc_manager=self.qc_manager,
            runtime=self,
        )

        # ── Wire QC Handler into Specialist Agent Engine ─────────────────
        if self.specialist_engine:
            qc_handler = QCSpecialistHandler(qc_manager=self.qc_manager)
            from axiom.models.agent_specialist import SpecialistType
            self.specialist_engine.register_handler(
                SpecialistType.QC, qc_handler,
            )

        # ── End PHASE D ─────────────────────────────────────────────────

        # PHASE E — Executive Intelligence + QC Learning
        self.executive_intelligence = ExecutiveIntelligence(
            learning_engine=self.learning,
            runtime=self,
        )

        # Update fundamental reporting engine with the correct executive intelligence reference
        if self.fundamental_reporting:
            self.fundamental_reporting.executive_intelligence = self.executive_intelligence

        self.executive_greeter = ExecutiveGreeter(runtime=self)

        self.qc_learning_pipeline = QCtoLearningPipeline(
            learning_engine=self.learning,
            runtime=self,
        )

        # AXIOM Core — top-level intelligence layer (above all executives)
        self.axiom = AXIOMCore(runtime=self, logger=self.logger)
        self.axiom.wire_components(
            intelligence=self.intelligence,
            event=self.event,
            executive=self.executive,
            executive_board=self.executive_board,
            workflow=self.workflow,
            memory=self.memory,
            tool=self.tool,
            learning=self.learning,
            greeting=self.greeting_engine,
            system_monitor=self.system_monitor,
            system_tools=self.system_tools,
            approval=self.approval,
        )

        # Research Workspace Manager
        self.research = ResearchWorkspaceManager(logger=self.logger)

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

        # ── PHASE C: Start Autonomous Components ────────────────────────

        # Start Specialist Agent Engine (background task processors)
        if self.specialist_engine:
            await self.specialist_engine.start()

        # Start Autonomous Workflow Monitor (background monitoring loop)
        if self.autonomous_workflow:
            await self.autonomous_workflow.start_monitor()

        # Start Background Executor (persistent background execution §6)
        if self.background_executor:
            await self.background_executor.start()

        if self.logger:
            self.logger.info(
                "lifecycle",
                "PHASE C — Autonomous Workflow + Agent System started: "
                "SpecialistEngine + AutonomousWorkflow + MultiModel + BackgroundExecutor + Observer"
            )

        # ── End PHASE C ─────────────────────────────────────────────────

        # ── PHASE D: Start Quality Control + Founder Authority ──────────

        # QC Manager doesn't need background tasks — it runs on demand.
        if self.qc_manager:
            # Wire QC callbacks
            if self.qc_learning_pipeline:
                self.qc_manager.set_on_qc_passed(self._on_qc_passed_for_learning)
                self.qc_manager.set_on_qc_failed(self._on_qc_failed_for_learning)

            if self.logger:
                self.logger.info(
                    "lifecycle",
                    "PHASE D — Quality Control + Founder Authority initialised: "
                    "QCManager + FounderAuthority + FounderGateway + QCHandler"
                )

        # ── PHASE E: Wire Executive Intelligence + QC Learning ─────────

        if self.logger:
            self.logger.info(
                "lifecycle",
                "PHASE E — Executive Intelligence + QC Learning initialised: "
                "ExecutiveIntelligence + ExecutiveGreeter + QCtoLearningPipeline"
            )

        # ── End PHASE E ─────────────────────────────────────────────────

        # ── PHASE 1: Initialize Integration Layer ───────────────────────────

        # Now that event engine is started, initialize the integration layer
        from axiom.integrations.layer import IntegrationLayer
        self.integration_layer = IntegrationLayer(logger=self.logger)
        await self.integration_layer.initialize(event_engine=self.event)

        # Start scheduled integrations
        started = await self.integration_layer.start_all_scheduled()
        if self.logger:
            self.logger.info(
                "lifecycle",
                f"PHASE 1 — Unified Integration Layer started: {started} scheduled integrations running"
            )

        # ── End PHASE 1 ────────────────────────────────────────────────────

        # ── PHASE 7: Initialize Resource-Aware Runtime ──────────────────────

        # Initialize orchestrator with all components
        self.runtime_orchestrator = RuntimeOrchestrator(
            logger=self.logger,
            event_engine=self.event,
            integration_layer=self.integration_layer,
            executive_loops={
                exec_id: self.executive_board.get_loop(exec_id)
                for exec_id in self.executive_board.EXECUTIVE_IDS
            } if self.executive_board else {},
        )
        await self.runtime_orchestrator.start()

        if self.logger:
            self.logger.info(
                "lifecycle",
                "PHASE 7 — Resource-Aware Runtime started: Monitor + Scheduler + Quotas + Orchestrator"
            )

        # ── End PHASE 7 ────────────────────────────────────────────────────

        # Start Board Room (autonomous meeting scheduling)
        if self.board_room:
            await self.board_room.start()

        # Wire communication coordinator into executive board loops
        if self.executive_board and self.communication:
            self.executive_board.set_communication_coordinator(self.communication)
            # Wire board room into executive board for meeting triggers
            self.executive_board.set_board_room(self.board_room)

        # Start Executive Board (autonomous executive runtime loops)
        if self.executive_board:
            await self.executive_board.start_all()

        # Execute AXIOM Core boot sequence (greeting, system awareness init)
        if self.axiom:
            boot_result = await self.axiom.boot()
            if self.logger:
                self.logger.info(
                    "lifecycle",
                    f"AXIOM boot: {boot_result.system_state.value} "
                    f"({len(boot_result.stages_completed)}/{len(boot_result.stage_timings)} stages in "
                    f"{boot_result.duration_ms:.0f}ms)",
                )

        # ── PHASE 8: Initialize Executive Integration ────────────────────────

        # Market intelligence engine
        self.market_intelligence = MarketIntelligenceEngine(
            data_manager=self.data_manager,
            runtime=self,
        )
        # Fundamental reporting engine
        self.fundamental_reporting = FundamentalReportingEngine(
            data_manager=self.data_manager,
            market_intelligence=self.market_intelligence,
            executive_intelligence=self.intelligence,  # Temporary, will be updated after executive intelligence is created
        )

        # Initialize Executive Integration with all system components
        self.executive_integration = ExecutiveIntegration(
            runtime=self,
            config=ExecutiveIntegrationConfig(),
            logger=self.logger,
        )
        await self.executive_integration.initialize(
            executive_board=self.executive_board,
            axiom_core=self.axiom,
            resource_orchestrator=self.runtime_orchestrator,
            integration_layer=self.integration_layer,
            database_manager=self.data_manager,
            intelligence_engine=self.intelligence,
        )

        # Start executive sync loop
        await self.executive_integration.start_sync_loop()

        if self.logger:
            self.logger.info(
                "lifecycle",
                "PHASE 8 — Executive Integration started: Jenson/Bleval + Valta Prime/Trading + Yamako/Personal fully integrated"
            )

        # ── End PHASE 8 ────────────────────────────────────────────────────

        self._running = True

        if self.logger:
            self.logger.info("lifecycle", "Axiom OS runtime started")

    async def shutdown(self) -> None:
        """Graceful shutdown of all background processors."""
        self._running = False

        if self.logger:
            self.logger.info("lifecycle", "Axiom OS runtime shutting down")

        # Stop in reverse order
        # ── PHASE 8: Shutdown Executive Integration ───────────────────────────
        if self.executive_integration:
            await self.executive_integration.stop_sync_loop()
            if self.logger:
                self.logger.info("lifecycle", "PHASE 8 — Executive Integration shutdown complete")

        # ── End PHASE 8 ───────────────────────────────────────────────────

        # ── PHASE 7: Shutdown Resource-Aware Runtime ───────────────────────────
        if self.runtime_orchestrator:
            await self.runtime_orchestrator.stop()
            if self.logger:
                self.logger.info("lifecycle", "PHASE 7 — Resource-Aware Runtime shutdown complete")

        # ── End PHASE 7 ───────────────────────────────────────────────────

        # ── PHASE 1: Shutdown Integration Layer ──────────────────────────────
        if self.integration_layer:
            await self.integration_layer.shutdown()
            if self.logger:
                self.logger.info("lifecycle", "PHASE 1 — Unified Integration Layer shutdown complete")

        # ── End PHASE 1 ───────────────────────────────────────────────────

        # ── PHASE H: Shutdown Platform Integrations ────────────────────────────
        if self.provider_registry:
            await self.provider_registry.shutdown_all()
            if self.logger:
                self.logger.info("lifecycle", "PHASE H — Platform Integrations shutdown complete")

        # ── End PHASE H ─────────────────────────────────────────────────

        # ── PHASE D: Shutdown Quality Control + Founder Authority ──────
        # No background tasks to stop — all on-demand execution.

        # ── End PHASE D ─────────────────────────────────────────────────

        # ── PHASE C: Shutdown Autonomous Components ────────────────────
        if self.background_executor:
            await self.background_executor.stop()

        if self.autonomous_workflow:
            await self.autonomous_workflow.stop_monitor()

        if self.specialist_engine:
            await self.specialist_engine.stop()

        # ── End PHASE C ─────────────────────────────────────────────────

        if self.system_monitor:
            await self.system_monitor.shutdown()

        # AXIOM Core shutdown
        if self.axiom:
            await self.axiom.shutdown()

        if self.executive_board:
            await self.executive_board.stop_all()

        if self.board_room:
            await self.board_room.stop()

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

    
        # Initialize providers for each organization
        await self._initialize_providers_for_organizations()

        if self.logger:
            providers = self.provider_registry.list_providers()
            self.logger.info("lifecycle", f"PHASE H — Platform Integrations registered: {len(providers)} providers initialized")

    async def _initialize_providers_for_organizations(self) -> None:
        """Initialize providers for all known organizations."""
        import os
        from pathlib import Path

        # Known organizations
        orgs_path = Path("organizations")
        if not orgs_path.exists():
            orgs_path = Path("../organizations")
        if not orgs_path.exists():
            if self.logger:
                self.logger.warning("lifecycle", "Organizations directory not found, skipping provider initialization")
            return

        org_ids = [d.name for d in orgs_path.iterdir() if d.is_dir()]

        for org_id in org_ids:
            try:
                providers = await self.provider_registry.initialize_providers(org_id)
                if self.logger:
                    self.logger.info("lifecycle", f"Initialized {len(providers)} providers for org {org_id}")
            except Exception as e:
                if self.logger:
                    self.logger.error("lifecycle", f"Failed to initialize providers for org {org_id}: {e}")

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
                "market_intelligence": self.market_intelligence is not None,
                "fundamental_reporting": self.fundamental_reporting is not None,
                "scheduler": self.scheduler is not None,
                "dispatcher": self.dispatcher is not None,
                "monitor": self.monitor is not None,
                "recovery": self.recovery is not None,
                "approval": self.approval is not None,
                "executive_board": self.executive_board is not None,
                "board_room": self.board_room is not None,
                "communication": self.communication is not None,
                "logger": self.logger is not None,
                "learning": self.learning is not None,
                "axiom_core": self.axiom is not None,
                "research": self.research is not None,
                # PHASE C Components
                "specialist_engine": self.specialist_engine is not None,
                "autonomous_workflow": self.autonomous_workflow is not None,
                "multi_model": self.multi_model is not None,
                "background_executor": self.background_executor is not None,
                "workflow_observer": self.workflow_observer is not None,
                # PHASE D Components
                "qc_manager": self.qc_manager is not None,
                "founder_authority": self.founder_authority is not None,
                "founder_gateway": self.founder_gateway is not None,
                # PHASE H Components
                "provider_registry": self.provider_registry is not None,
                # PHASE 1 Components
                "integration_layer": self.integration_layer is not None,
            },
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return a rich summary of the runtime state."""
        status = self.get_status()
        monitor_summary = self.monitor.get_summary() if self.monitor else {}
        workflows = self.workflow.list_workflows() if self.workflow else {}
        agents = self.executive.list_executives() if self.executive else []
        orgs = self.executive.list_organizations() if self.executive else []

        axiom_state = self.axiom.state.value if self.axiom else "unavailable"
        res_count = len(self.research.list_all()) if self.research else 0

        # PHASE C summaries
        specialist_summary = self.specialist_engine.get_summary() if self.specialist_engine else {}
        autonomous_summary = self.autonomous_workflow.get_summary() if self.autonomous_workflow else {}
        multi_model_summary = self.multi_model.get_summary() if self.multi_model else {}
        bg_executor_status = self.background_executor.get_status() if self.background_executor else {}
        observer_stats = self.workflow_observer.get_aggregate_stats() if self.workflow_observer else {}

        # PHASE D summaries
        qc_summary = self.qc_manager.get_summary() if self.qc_manager else {}
        authority_status = self.founder_authority.get_status() if self.founder_authority else {}
        gateway_summary = self.founder_gateway.get_summary() if self.founder_gateway else {}

        # Fundamental Reporting summaries
        fund_report_status = {}
        if self.fundamental_reporting:
            fund_report_status = {
                "engine": "operational",
                "cached_reports": len(self.fundamental_reporting._reports_cache),
                "last_report_times": {
                    session.value: time.isoformat()
                    for session, time in self.fundamental_reporting._last_report_times.items()
                }
            }

        # Market Intelligence summaries
        market_intel_status = {}
        if self.market_intelligence:
            # Can add market intelligence status here
            pass

        # PHASE E summaries
        ei_status = {}
        if self.executive_intelligence:
            # Can add executive intelligence status here
            pass
        qc_lp_status = self.qc_learning_pipeline.get_status() if hasattr(self.qc_learning_pipeline, 'get_status') else {}

        # PHASE H summaries
        phase_h_status = {}
        if self.provider_registry:
            providers = self.provider_registry.list_providers()
            phase_h_status = {
                "providers_count": len(providers),
                "providers": {pid: p.get_schema() for pid, p in providers.items()},
            }

        return {
            **status,
            "health": monitor_summary,
            "workflows_defined": len(workflows),
            "executives": len(agents),
            "org_count": len(orgs),
            "axiom": {
                "state": axiom_state,
                "boot_id": self.axiom.boot_id if self.axiom else "",
                "is_online": self.axiom.is_online if self.axiom else False,
            },
            "research_workspaces": res_count,
            # PHASE C Status
            "phase_c": {
                "specialist_engine": specialist_summary,
                "autonomous_workflows": autonomous_summary,
                "multi_model": multi_model_summary,
                "background_executor": bg_executor_status,
                "workflow_observer": observer_stats,
            },
            # PHASE D Status
            "phase_d": {
                "qc_manager": qc_summary,
                "founder_authority": authority_status,
                "founder_gateway": gateway_summary,
            },
            # Fundamental Reporting Status
            "fundamental_reporting": {
                "engine": fund_report_status,
            },
            # Market Intelligence Status
            "market_intelligence": {
                "engine": market_intel_status,
            },
            # PHASE E Status
            "phase_e": {
                "executive_intelligence": ei_status,
                "qc_learning_pipeline": qc_lp_status,
            },
            # PHASE H Status
            "phase_h": phase_h_status,
            # PHASE 1 Status
            "phase_1": self.integration_layer.get_summary() if self.integration_layer else {},
        }

    # ── QC Learning Pipeline Callbacks ──────────────────────────────────────

    async def _on_qc_passed_for_learning(self, qc_id: str, result: Any) -> None:
        """Callback when QC passes — feed into learning pipeline."""
        if not self.qc_learning_pipeline:
            return

        await self.qc_learning_pipeline.process_qc_result(
            qc_id=qc_id,
            artifact_name=result.artifact_name,
            artifact_type=result.artifact_type,
            passed=True,
            scope=result.scope.value if hasattr(result.scope, 'value') else str(result.scope),
            findings=[],  # No findings on pass
            retry_count=result.retry_count,
            workflow_id=getattr(result, 'workflow_id', ''),
            workflow_instance_id=getattr(result, 'workflow_instance_id', ''),
        )

        if self.logger:
            self.logger.info(
                "qc.learning",
                f"QC passed signal sent to learning pipeline: {qc_id}"
            )

    async def _on_qc_failed_for_learning(self, qc_id: str, result: Any, rework: Any) -> None:
        """Callback when QC fails — feed into learning pipeline."""
        if not self.qc_learning_pipeline:
            return

        # Convert findings to dict format
        findings = []
        for f in getattr(result, 'findings', []):
            findings.append({
                "check_type": f.check_type.value if hasattr(f.check_type, 'value') else str(f.check_type),
                "severity": f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
                "message": f.description,
                "location": getattr(f, 'location', ''),
                "detail": getattr(f, 'detail', ''),
                "suggested_fix": getattr(f, 'suggested_fix', ''),
            })

        await self.qc_learning_pipeline.process_qc_result(
            qc_id=qc_id,
            artifact_name=result.artifact_name,
            artifact_type=result.artifact_type,
            passed=False,
            scope=result.scope.value if hasattr(result.scope, 'value') else str(result.scope),
            findings=findings,
            retry_count=result.retry_count,
            workflow_id=getattr(result, 'workflow_id', ''),
            workflow_instance_id=getattr(result, 'workflow_instance_id', ''),
        )

        if self.logger:
            self.logger.info(
                "qc.learning",
                f"QC failed signal sent to learning pipeline: {qc_id} ({len(findings)} findings)"
            )