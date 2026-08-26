"""Executive Integration — Full integration of executive loops with all system layers.

This module provides the complete integration layer that connects the three
executives (Jenson/Bleval, Valta Prime/Trading, Yamako/Personal) with:
- Unified Integration Layer (all platform integrations)
- Domain Database Repositories (BLEVAL, MARKET, RESEARCH, COMMS)
- Market Intelligence Engine
- Communication Gateway
- Resource-Aware Runtime
- AXIOM Core (top-level intelligence)
- QC Pipeline and Learning Feedback Loop

This is the "glue" that makes the system genuinely autonomous and live.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

from pydantic import BaseModel, Field

from axiom.runtime.logging import RuntimeLogger
from axiom.runtime.executive_loop import ExecutiveRuntimeLoop, ExecutiveBoard, EXECUTIVE_DEFAULT_SCHEDULES
# Lazy import to avoid circular dependency
# from axiom.integrations.layer import IntegrationLayer

# Import repository types for Pydantic model
from axiom.data.repositories.bleval import BlevalRepository
from axiom.data.repositories.market import MarketRepository
from axiom.data.repositories.research import ResearchRepository
from axiom.data.repositories.comms import CommsRepository

# Import pipeline types for Pydantic model
from axiom.integrations.research.pipeline import ResearchPipeline
from axiom.integrations.market.pipeline import MarketPipeline
from axiom.integrations.bleval.pipeline import BlevalPipeline
from axiom.integrations.comms.gateway import CommunicationGateway
from axiom.integrations.market.intelligence import MarketIntelligenceEngine

# Runtime types
from axiom.runtime.resource import RuntimeOrchestrator
from axiom.data.database import DatabaseManager
from axiom.core.axiom_core import AXIOMCore
from axiom.engine.intelligence import IntelligenceEngine


class ExecutiveContext(BaseModel):
    """Runtime context for an executive."""

    exec_id: str
    org_id: str
    departments: List[str]

    # Repositories
    bleval_repo: Optional[BlevalRepository] = None
    market_repo: Optional[MarketRepository] = None
    research_repo: Optional[ResearchRepository] = None
    comms_repo: Optional[CommsRepository] = None

    # Pipelines
    research_pipeline: Optional[ResearchPipeline] = None
    market_pipeline: Optional[MarketPipeline] = None
    bleval_pipeline: Optional[BlevalPipeline] = None
    comms_gateway: Optional[CommunicationGateway] = None

    # Intelligence
    market_intelligence: Optional[MarketIntelligenceEngine] = None

    # Runtime
    resource_orchestrator: Optional[RuntimeOrchestrator] = None
    integration_layer: Optional["IntegrationLayer"] = None
    axiom_core: Optional[AXIOMCore] = None
    intelligence_engine: Optional[IntelligenceEngine] = None

    # Executive-specific
    custom_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def _find_matching_workflow(self, priority: str, available_workflows: List[str]) -> Optional[str]:
        """Find a matching workflow for a priority."""
        priority_lower = priority.lower()

        # Direct match
        for wf in available_workflows:
            if wf.lower() in priority_lower or priority_lower in wf.lower():
                return wf

        # Keyword matching
        keywords_to_workflows = {
            "prospect": "sales/prospect-research",
            "outreach": "sales/outreach-campaign",
            "deal": "sales/deal-closing",
            "content": "marketing/content-production",
            "campaign": "marketing/campaign-launch",
            "signal": "trading/signal-generation",
            "position": "trading/position-management",
            "risk": "risk/portfolio-review",
            "market": "market/market-analysis",
            "schedule": "personal/schedule-management",
            "task": "personal/task-capture",
            "daily": "operations/daily-report",
            "sync": "cross-org/executive-sync",
        }

        for keyword, wf in keywords_to_workflows.items():
            if keyword in priority_lower and wf in available_workflows:
                return wf

        return None


class ExecutiveIntegrationConfig(BaseModel):
    """Configuration for executive integration."""

    # Enable/disable integrations per executive
    jenson_integrations: Dict[str, bool] = Field(default_factory=lambda: {
        "bleval": True,
        "market": False,
        "research": True,
        "comms": True,
    })
    valta_prime_integrations: Dict[str, bool] = Field(default_factory=lambda: {
        "bleval": False,
        "market": True,
        "research": True,
        "comms": True,
    })
    yamako_integrations: Dict[str, bool] = Field(default_factory=lambda: {
        "bleval": False,
        "market": False,
        "research": True,
        "comms": True,
    })

    # Default workflow triggers
    jenson_workflows: List[str] = Field(default_factory=lambda: [
        "sales/prospect-research",
        "sales/outreach-campaign",
        "sales/deal-closing",
        "marketing/content-production",
        "marketing/campaign-launch",
    ])
    valta_prime_workflows: List[str] = Field(default_factory=lambda: [
        "trading/signal-generation",
        "trading/position-management",
        "risk/portfolio-review",
        "market/market-analysis",
    ])
    yamako_workflows: List[str] = Field(default_factory=lambda: [
        "personal/schedule-management",
        "personal/task-capture",
        "operations/daily-report",
        "cross-org/executive-sync",
    ])

    # Reporting
    daily_report_enabled: bool = True
    executive_sync_enabled: bool = True
    sync_interval_minutes: int = 60


class ExecutiveIntegration:
    """Full integration manager for all executives."""

    def __init__(
        self,
        runtime: Any,  # AxiomRuntime
        config: Optional[ExecutiveIntegrationConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.runtime = runtime
        self.config = config or ExecutiveIntegrationConfig()
        self.logger = logger or RuntimeLogger()

        # Core references (wired during setup)
        self._executive_board: Optional[ExecutiveBoard] = None
        self._axiom_core: Optional[AXIOMCore] = None
        self._resource_orchestrator: Optional[RuntimeOrchestrator] = None
        self._integration_layer: Optional[IntegrationLayer] = None
        self._database_manager: Optional[DatabaseManager] = None
        self._intelligence_engine: Optional[IntelligenceEngine] = None

        # Domain repositories
        self._bleval_repo: Optional[BlevalRepository] = None
        self._market_repo: Optional[MarketRepository] = None
        self._research_repo: Optional[ResearchRepository] = None
        self._comms_repo: Optional[CommsRepository] = None

        # Pipelines
        self._research_pipeline: Optional[ResearchPipeline] = None
        self._market_pipeline: Optional[MarketPipeline] = None
        self._bleval_pipeline: Optional[BlevalPipeline] = None
        self._comms_gateway: Optional[CommunicationGateway] = None
        self._market_intelligence: Optional[MarketIntelligenceEngine] = None

        # Executive contexts
        self._contexts: Dict[str, ExecutiveContext] = {}

        # Running state
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None

    async def initialize(
        self,
        executive_board: ExecutiveBoard,
        axiom_core: AXIOMCore,
        resource_orchestrator: RuntimeOrchestrator,
        integration_layer: "IntegrationLayer",
        database_manager: DatabaseManager,
        intelligence_engine: IntelligenceEngine,
    ) -> None:
        """Initialize all integration components."""
        self._executive_board = executive_board
        self._axiom_core = axiom_core
        self._resource_orchestrator = resource_orchestrator
        self._integration_layer = integration_layer
        self._database_manager = database_manager
        self._intelligence_engine = intelligence_engine

        # Initialize domain repositories
        await self._initialize_repositories()

        # Initialize pipelines
        await self._initialize_pipelines()

        # Create executive contexts
        await self._create_executive_contexts()

        # Wire executive loops with integrations
        await self._wire_executive_loops()

        self.logger.info("executive_integration", "Executive integration initialized")

    async def _initialize_repositories(self) -> None:
        """Initialize domain-specific repositories."""
        self._bleval_repo = BlevalRepository(self._database_manager)
        self._market_repo = MarketRepository(self._database_manager)
        self._research_repo = ResearchRepository(self._database_manager)
        self._comms_repo = CommsRepository(self._database_manager)

    async def _initialize_pipelines(self) -> None:
        """Initialize all pipelines."""
        from axiom.integrations.research.pipeline import ResearchPipeline
        from axiom.integrations.market.pipeline import MarketPipeline
        from axiom.integrations.bleval.pipeline import BlevalPipeline
        from axiom.integrations.comms.gateway import CommunicationGateway
        from axiom.integrations.market.intelligence import MarketIntelligenceEngine
        from axiom.integrations.research import NewsProviderConfig, WebProviderConfig, ProcessingConfig, SynthesisConfig
        from axiom.integrations.market import MarketProviderConfig, IntelligenceConfig
        from axiom.integrations.bleval import CRMSyncConfig, LeadAcquisitionConfig, DealTrackerConfig, CampaignConfig

        # Research pipeline - needs integration_layer, repository, and configs
        self._research_pipeline = ResearchPipeline(
            integration_layer=self._integration_layer,
            repository=self._research_repo,
            news_configs=[],  # Would be configured from settings
            web_config=None,
            processing_config=ProcessingConfig(),
            synthesis_config=SynthesisConfig(),
            logger=self.logger,
        )

        # Market pipeline - needs integration_layer, repository, provider configs, tracked symbols
        self._market_pipeline = MarketPipeline(
            integration_layer=self._integration_layer,
            repository=self._market_repo,
            provider_configs=[],
            tracked_symbols=[],
            config=IntelligenceConfig(),
            logger=self.logger,
        )

        # BLEVAL pipeline
        self._bleval_pipeline = BlevalPipeline(
            integration_layer=self._integration_layer,
            repository=self._bleval_repo,
            crm_config=CRMSyncConfig(provider="custom", base_url="", enabled=False),
            lead_config=LeadAcquisitionConfig(),
            deal_config=DealTrackerConfig(),
            campaign_config=CampaignConfig(),
            logger=self.logger,
        )

        # Communication gateway
        self._comms_gateway = CommunicationGateway(
            integration_layer=self._integration_layer,
            repositories={
                "comms": self._comms_repo,
                "bleval": self._bleval_repo,
                "market": self._market_repo,
                "research": self._research_repo,
            },
            logger=self.logger,
        )

        # Market intelligence engine
        self._market_intelligence = MarketIntelligenceEngine(
            integration_layer=self._integration_layer,
            repository=self._market_repo,
            config=IntelligenceConfig(),
            logger=self.logger,
        )

    async def _create_executive_contexts(self) -> None:
        """Create runtime contexts for each executive."""
        from axiom.models.executive_constants import EXECUTIVE_ORGS, EXECUTIVE_DEPTS

        executive_configs = {
            "jenson": self.config.jenson_integrations,
            "valta_prime": self.config.valta_prime_integrations,
            "yamako": self.config.yamako_integrations,
        }

        for exec_id, integrations in executive_configs.items():
            org_id = EXECUTIVE_ORGS.get(exec_id, "")
            departments = EXECUTIVE_DEPTS.get(exec_id, [])

            context = ExecutiveContext(
                exec_id=exec_id,
                org_id=org_id,
                departments=departments,
            )

            # Assign relevant repositories
            if integrations.get("bleval") and self._bleval_repo:
                context.bleval_repo = self._bleval_repo
            if integrations.get("market") and self._market_repo:
                context.market_repo = self._market_repo
            if integrations.get("research") and self._research_repo:
                context.research_repo = self._research_repo
            if integrations.get("comms") and self._comms_repo:
                context.comms_repo = self._comms_repo

            # Assign pipelines
            if integrations.get("research") and self._research_pipeline:
                context.research_pipeline = self._research_pipeline
            if integrations.get("market") and self._market_pipeline:
                context.market_pipeline = self._market_pipeline
            if integrations.get("bleval") and self._bleval_pipeline:
                context.bleval_pipeline = self._bleval_pipeline
            if integrations.get("comms") and self._comms_gateway:
                context.comms_gateway = self._comms_gateway

            # Assign market intelligence
            if self._market_intelligence:
                context.market_intelligence = self._market_intelligence

            # Assign runtime components
            context.resource_orchestrator = self._resource_orchestrator
            context.integration_layer = self._integration_layer
            context.axiom_core = self._axiom_core
            context.intelligence_engine = self._intelligence_engine

            # Executive-specific data
            context.custom_data = {
                "workflows": getattr(self.config, f"{exec_id}_workflows", []),
            }

            self._contexts[exec_id] = context

    async def _wire_executive_loops(self) -> None:
        """Wire executive loops with their contexts and custom cycle handlers."""
        for exec_id, context in self._contexts.items():
            loop = self._executive_board.get_loop(exec_id)
            if not loop:
                continue

            # Replace the default _execute_cycle with our integrated version
            loop._execute_cycle = self._create_integrated_cycle(exec_id, context)

            # Inject context into loop for access during cycles
            loop._integration_context = context

    def _create_integrated_cycle(
        self,
        exec_id: str,
        context: ExecutiveContext,
    ) -> Callable:
        """Create an integrated cycle handler for an executive."""

        async def _integrated_cycle(cycle_type: str) -> Dict[str, Any]:
            """Enhanced cycle with full system integration."""
            start_time = datetime.utcnow()

            # ============================================================
            # PHASE 1: SYSTEM INSPECTION (via all integrated layers)
            # ============================================================

            # 1. Organization state (with live integration data)
            org_state = await self._inspect_organization_integrated(exec_id, context)

            # 2. Memory (now includes integration data)
            memory_state = self._inspect_memory(exec_id)

            # 3. Active workflows (from workflow engine)
            active_workflows = self._inspect_workflows(exec_id)

            # 4. Completed work
            completed_work = self._review_completed(exec_id)

            # 5. Integration health (new!)
            integration_health = await self._check_integration_health(context)

            # 6. Resource status (new!)
            resource_status = self._get_resource_status(context)

            # 7. Market snapshot (Valta Prime)
            market_snapshot = None
            if exec_id == "valta_prime" and context.market_intelligence:
                market_snapshot = await self._get_market_snapshot(context)

            # 7. BLEVAL pipeline status (Jenson)
            bleval_status = None
            if exec_id == "jenson" and context.bleval_pipeline:
                bleval_status = await context.bleval_pipeline.get_status()

            # ============================================================
            # PHASE 2: BUILD COMPREHENSIVE OBSERVATIONS
            # ============================================================

            observations = {
                "org_state": org_state,
                "memory_topics": list(memory_state.keys()) if memory_state else [],
                "active_workflows": len(active_workflows),
                "completed_work_this_cycle": len(completed_work),
                "integration_health": integration_health,
                "resource_status": resource_status,
            }

            if market_snapshot:
                observations["market_snapshot"] = {
                    "timestamp": market_snapshot.timestamp.isoformat(),
                    "symbols_tracked": len(market_snapshot.symbols),
                    "signals_active": len(market_snapshot.signals),
                    "regime": market_snapshot.regime.value,
                }

            if bleval_status:
                observations["bleval_pipeline"] = bleval_status

            # ============================================================
            # PHASE 3: PRIORITY DECISION (with full context)
            # ============================================================

            priorities = await self._decide_priorities_integrated(
                exec_id=exec_id,
                cycle_type=cycle_type,
                context=context,
                org_state=org_state,
                memory_state=memory_state,
                active_workflows=active_workflows,
                completed_work=completed_work,
                market_snapshot=market_snapshot,
                bleval_status=bleval_status,
                integration_health=integration_health,
                resource_status=resource_status,
            )

            # ============================================================
            # PHASE 4: WORKFLOW LAUNCHING (with resource awareness)
            # ============================================================

            workflows_launched = await self._launch_priority_workflows_integrated(
                exec_id=exec_id,
                context=context,
                priorities=priorities,
            )

            # ============================================================
            # PHASE 5: REPORTING AND LEARNING
            # ============================================================

            report = self._format_cycle_report(
                exec_id=exec_id,
                org_id=context.org_id,
                cycle_type=cycle_type,
                observations=observations,
                priorities=priorities,
                workflows_launched=workflows_launched,
                completed_work=completed_work,
            )

            # Log cycle
            if self.logger:
                self.logger.workflow_event(
                    instance_id=f"exec-{exec_id}-cycle",
                    event=f"executive_cycle_{cycle_type}",
                    details={
                        "executive": exec_id,
                        "type": cycle_type,
                        "workflows_launched": workflows_launched,
                        "active_workflows": len(active_workflows),
                        "priorities": priorities,
                        "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    },
                )

            # Record in executive memory
            if context.axiom_core:
                from axiom.runtime.executive_memory import ExecutiveMemoryManager
                memory_mgr = ExecutiveMemoryManager(exec_id=exec_id, runtime=self.runtime)
                memory_mgr.load()
                memory_mgr.record_decision(
                    decision_type=f"cycle_{cycle_type}",
                    description=f"Cycle completed: {workflows_launched} workflows launched",
                    reasoning=f"Based on {len(active_workflows)} active workflows, {len(completed_work)} completed",
                    tags=[cycle_type, context.org_id],
                )

            # Report to Founder (daily/afternoon)
            is_daily_report = cycle_type in ("daily_report", "afternoon_review")
            if is_daily_report and context.axiom_core:
                await self._report_to_founder(exec_id, report)

            # Publish KPIs to board room
            if context.axiom_core and context.axiom_core._executive_board:
                try:
                    board_room = context.axiom_core._executive_board._board_room
                    if board_room:
                        snapshot = self._get_kpi_snapshot(context)
                        board_room.publish_kpi_snapshot(exec_id, snapshot)
                except Exception:
                    pass

            # ============================================================
            # PHASE 6: EVENT EMISSION (for learning pipeline)
            # ============================================================

            if self._resource_orchestrator and self._resource_orchestrator.event_engine:
                import uuid
                await self._resource_orchestrator.event_engine.publish(
                    event_type="executive.cycle_completed",
                    source=f"executive.{exec_id}",
                    payload={
                        "exec_id": exec_id,
                        "cycle_type": cycle_type,
                        "cycle_count": loop._cycle_count if hasattr(loop, '_cycle_count') else 0,
                        "workflows_launched": workflows_launched,
                        "priorities": priorities,
                        "resource_usage": resource_status,
                    },
                    correlation_id=str(uuid.uuid4()),
                )

            return {
                "cycle": cycle_type,
                "priorities": priorities,
                "workflows_launched": workflows_launched,
                "active_workflows": len(active_workflows),
                "completed_work": len(completed_work),
                "resource_status": resource_status,
                "integration_health": integration_health,
            }

        # Need reference to loop for cycle_count
        loop = self._executive_board.get_loop(exec_id) if self._executive_board else None

        return _integrated_cycle

    async def _inspect_organization_integrated(
        self,
        exec_id: str,
        context: ExecutiveContext,
    ) -> Dict[str, Any]:
        """Inspect organization with integration layer data."""
        # Get the loop and call its inspection method
        loop = self._executive_board.get_loop(exec_id) if self._executive_board else None
        if loop and hasattr(loop, '_inspect_organization'):
            state = loop._inspect_organization()
        else:
            state = {"org_id": context.org_id}

        # Add integration layer stats
        if self._integration_layer:
            summary = self._integration_layer.get_summary()
            state["integrations"] = summary.get("integrations", {})

        return state

    def _inspect_memory(self, exec_id: str) -> Dict[str, str]:
        """Inspect memory."""
        if self.runtime.memory:
            try:
                return self.runtime.memory.get_resolved_context(
                    agent_id=exec_id,
                    org_id=self._contexts[exec_id].org_id,
                )
            except Exception:
                pass
        return {}

    def _inspect_workflows(self, exec_id: str) -> List[Dict[str, Any]]:
        """Inspect active workflows."""
        if self.runtime.workflow:
            try:
                from axiom.models.workflows import WorkflowStatus
                instances = self.runtime.workflow.list_instances(status=WorkflowStatus.RUNNING)
                return [
                    {
                        "instance_id": i.instance_id,
                        "workflow_id": i.workflow_id,
                        "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                        "current_step": i.current_step_index,
                    }
                    for i in instances
                ]
            except Exception:
                pass
        return []

    def _review_completed(self, exec_id: str) -> List[Dict[str, Any]]:
        """Review completed work."""
        if self.runtime.workflow:
            try:
                from axiom.models.workflows import WorkflowStatus
                instances = self.runtime.workflow.list_instances(status=WorkflowStatus.COMPLETED)
                return [
                    {
                        "instance_id": i.instance_id,
                        "workflow_id": i.workflow_id,
                        "completed_at": i.completed_at.isoformat() if i.completed_at else "",
                    }
                    for i in instances[-5:]
                ]
            except Exception:
                pass
        return []

    async def _check_integration_health(self, context: ExecutiveContext) -> Dict[str, Any]:
        """Check integration layer health."""
        if not self._integration_layer:
            return {"status": "unavailable"}

        summary = self._integration_layer.get_summary()
        return {
            "status": "healthy" if summary.get("running_integrations", 0) > 0 else "degraded",
            "total_integrations": summary.get("total_integrations", 0),
            "running": summary.get("running_integrations", 0),
            "failed": summary.get("failed_integrations", 0),
        }

    def _get_resource_status(self, context: ExecutiveContext) -> Dict[str, Any]:
        """Get resource orchestrator status."""
        if not self._resource_orchestrator:
            return {"status": "unavailable"}

        return self._resource_orchestrator.get_status()

    async def _get_market_snapshot(self, context: ExecutiveContext) -> Any:
        """Get market intelligence snapshot."""
        if context.market_intelligence:
            return await context.market_intelligence.get_snapshot()
        return None

    async def _decide_priorities_integrated(
        self,
        exec_id: str,
        cycle_type: str,
        context: ExecutiveContext,
        org_state: Dict[str, Any],
        memory_state: Dict[str, str],
        active_workflows: List[Dict[str, Any]],
        completed_work: List[Dict[str, Any]],
        market_snapshot: Any,
        bleval_status: Any,
        integration_health: Dict[str, Any],
        resource_status: Dict[str, Any],
    ) -> List[str]:
        """Decide priorities with full system context."""
        intelligence = self._intelligence_engine

        if intelligence and exec_id in ["jenson", "valta_prime", "yamako"]:
            # Build rich context for intelligence engine
            task_context = {
                "cycle_type": cycle_type,
                "exec_id": exec_id,
                "org_id": context.org_id,
                "departments": context.departments,
                "org_state": org_state,
                "memory_state": memory_state,
                "active_workflows": active_workflows,
                "completed_work": completed_work,
                "integration_health": integration_health,
                "resource_status": resource_status,
                "available_workflows": context.custom_data.get("workflows", []),
            }

            if market_snapshot:
                task_context["market_snapshot"] = {
                    "regime": market_snapshot.regime.value,
                    "signals": len(market_snapshot.signals),
                    "total_symbols": len(market_snapshot.symbols),
                }

            if bleval_status:
                task_context["bleval_status"] = bleval_status

            try:
                # Use intelligence engine with specialized executive prompt
                response = await intelligence.generate_for_executive(
                    exec_id=exec_id,
                    task_description=f"Prioritize actions for {cycle_type} cycle",
                    org_id=context.org_id,
                    context=task_context,
                )
                priorities = self._parse_priorities(response)
                if priorities:
                    return priorities
            except Exception as e:
                if self.logger:
                    self.logger.warning("executive_integration", f"Priority decision failed for {exec_id}: {e}")

        # Fallback to default priorities
        return self._get_default_priorities(exec_id, cycle_type)

    def _get_default_priorities(self, exec_id: str, cycle_type: str) -> List[str]:
        """Get default priorities by executive and cycle type."""
        defaults = {
            "jenson": {
                "morning_review": [
                    "Review Bleval Inc pipeline and active deals",
                    "Check new leads from CRM sync",
                    "Launch prospect research workflows",
                    "Review marketing campaign performance",
                ],
                "midday_check": [
                    "Monitor active outreach campaigns",
                    "Check deal progress and blockers",
                    "Review content production status",
                ],
                "afternoon_review": [
                    "Review completed sales activities",
                    "Update pipeline forecast",
                    "Prepare daily report for Founder",
                ],
                "daily_report": [
                    "Compile daily Bleval Inc summary",
                    "Identify deals needing attention",
                    "Recommend next-day priorities",
                ],
            },
            "valta_prime": {
                "morning_review": [
                    "Review overnight market moves",
                    "Check POI alerts and positions",
                    "Analyze market regime and signals",
                    "Review risk exposure",
                ],
                "midday_check": [
                    "Monitor active positions",
                    "Check for signal changes",
                    "Review intraday P&L",
                ],
                "afternoon_review": [
                    "Review closed positions",
                    "Update portfolio snapshot",
                    "Prepare trading report for Founder",
                ],
                "daily_report": [
                    "Compile daily trading summary",
                    "Document lessons learned",
                    "Recommend next session focus",
                ],
            },
            "yamako": {
                "morning_review": [
                    "Review Founder schedule and commitments",
                    "Capture any overnight tasks",
                    "Check personal project priorities",
                    "Sync with other executives",
                ],
                "midday_check": [
                    "Monitor schedule changes",
                    "Check task progress",
                    "Handle time-sensitive items",
                ],
                "afternoon_review": [
                    "Review completed tasks",
                    "Prepare evening wind-down",
                    "Sync tomorrow's priorities",
                ],
                "daily_report": [
                    "Compile personal productivity summary",
                    "Identify scheduling conflicts",
                    "Recommend optimization",
                ],
            },
        }

        return defaults.get(exec_id, {}).get(cycle_type, [
            f"Monitor {exec_id} operations",
            "Review organization status",
        ])

    def _parse_priorities(self, response: str) -> Optional[List[str]]:
        """Parse priorities from intelligence response."""
        import json
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "priorities" in data:
                return data["priorities"]
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting numbered items
        lines = response.strip().split("\n")
        priorities = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("- ")):
                cleaned = line[2:].strip() if line.startswith("- ") else line[line.index(".")+1:].strip() if "." in line[:4] else line
                if cleaned:
                    priorities.append(cleaned)
                if len(priorities) >= 5:
                    break
        return priorities if priorities else None

    async def _launch_priority_workflows_integrated(
        self,
        exec_id: str,
        context: ExecutiveContext,
        priorities: List[str],
    ) -> int:
        """Launch workflows with resource awareness and approval routing."""
        if not self.runtime.workflow:
            return 0

        launched = 0
        available_workflows = context.custom_data.get("workflows", [])

        for priority in priorities[:3]:  # Top 3
            wf_id = context._find_matching_workflow(priority, available_workflows)
            if not wf_id:
                continue

            # Check resource quota before launching
            if context.resource_orchestrator:
                allowed = await context.resource_orchestrator.execute_with_quota(
                    scope=context.resource_orchestrator.quota_manager.QuotaScope.AGENT,
                    scope_id=exec_id,
                    quota_type=context.resource_orchestrator.quota_manager.QuotaType.CONCURRENT_TASKS,
                    amount=1.0,
                    coro=lambda: None,  # Just check
                )
                if not allowed:
                    if self.logger:
                        self.logger.warning(
                            "executive_integration",
                            f"{exec_id}: Resource quota exceeded, deferring {wf_id}"
                        )
                    continue

            try:
                workflow_context = {
                    "trigger": "executive_cycle",
                    "executive": exec_id,
                    "priority": priority,
                    "org_id": context.org_id,
                    "departments": context.departments,
                    "integration_context": {
                        "has_bleval": context.bleval_repo is not None,
                        "has_market": context.market_repo is not None,
                        "has_research": context.research_repo is not None,
                        "has_comms": context.comms_repo is not None,
                    },
                }

                instance = self.runtime.workflow.create_instance(wf_id, context=workflow_context)
                await self.runtime.workflow.start(instance.instance_id)
                launched += 1

                if self.logger:
                    self.logger.info("executive_integration", f"{exec_id} launched {wf_id} ({instance.instance_id})")

            except Exception as e:
                if self.logger:
                    self.logger.warning("executive_integration", f"{exec_id} failed to launch {wf_id}: {e}")

        return launched

    def _format_cycle_report(
        self,
        exec_id: str,
        org_id: str,
        cycle_type: str,
        observations: Dict[str, Any],
        priorities: List[str],
        workflows_launched: int,
        completed_work: List[Dict[str, Any]],
    ) -> str:
        """Format executive cycle report."""
        from axiom.runtime.executive_loop import _format_report
        return _format_report(
            exec_id=exec_id,
            org_id=org_id,
            cycle_type=cycle_type,
            observations=observations,
            priorities=priorities,
            workflows_launched=workflows_launched,
            completed_work=completed_work,
            report_to_founder=cycle_type in ("daily_report", "afternoon_review"),
        )

    async def _report_to_founder(self, exec_id: str, report: str) -> None:
        """Report to Founder via AXIOM Core."""
        if self._axiom_core:
            try:
                self._axiom_core._memory.write_agent_memory(
                    agent_id=exec_id,
                    key=f"founder-report-{datetime.utcnow().isoformat()}",
                    content=report,
                )
            except Exception:
                pass

    def _get_kpi_snapshot(self, context: ExecutiveContext) -> Dict[str, Any]:
        """Get KPI snapshot for board room."""
        return {
            "exec_id": context.exec_id,
            "timestamp": datetime.utcnow().isoformat(),
            "kpis": {
                "active_workflows": len(self._inspect_workflows(context.exec_id)),
                "integrations_healthy": True,
            },
        }

    async def start_sync_loop(self) -> None:
        """Start the executive sync loop for cross-executive coordination."""
        if self._running:
            return

        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        self.logger.info("executive_integration", "Executive sync loop started")

    async def stop_sync_loop(self) -> None:
        """Stop the sync loop."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        self.logger.info("executive_integration", "Executive sync loop stopped")

    async def _sync_loop(self) -> None:
        """Cross-executive synchronization loop."""
        while self._running:
            try:
                if self.config.executive_sync_enabled:
                    await self._sync_executives()

                await asyncio.sleep(self.config.sync_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("executive_integration", f"Sync loop error: {e}")
                await asyncio.sleep(60)

    async def _sync_executives(self) -> None:
        """Synchronize state across executives."""
        if not self._executive_board:
            return

        # Get status from all executives
        statuses = {}
        for exec_id in ["jenson", "valta_prime", "yamako"]:
            loop = self._executive_board.get_loop(exec_id)
            if loop:
                statuses[exec_id] = loop.get_status()

        # Publish cross-exec sync event
        if self._resource_orchestrator and self._resource_orchestrator.event_engine:
            from axiom.models.events import Event
            await self._resource_orchestrator.event_engine.publish(
                Event(
                    name="executive.board.sync",
                    payload={"executives": statuses, "timestamp": datetime.utcnow().isoformat()},
                    source="executive.board",
                )
            )

        if self.logger:
            self.logger.debug("executive_integration", f"Cross-executive sync: {list(statuses.keys())}")

    async def trigger_executive_workflow(
        self,
        exec_id: str,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Trigger a workflow for a specific executive."""
        loop = self._executive_board.get_loop(exec_id) if self._executive_board else None
        if not loop:
            return None

        ctx = context or {}
        ctx["executive"] = exec_id
        ctx["trigger"] = "manual"

        try:
            instance = self.runtime.workflow.create_instance(workflow_id, context=ctx)
            await self.runtime.workflow.start(instance.instance_id)
            return instance.instance_id
        except Exception as e:
            if self.logger:
                self.logger.error("executive_integration", f"Failed to trigger {workflow_id} for {exec_id}: {e}")
            return None

    def get_executive_context(self, exec_id: str) -> Optional[ExecutiveContext]:
        """Get the integration context for an executive."""
        return self._contexts.get(exec_id)

    def get_all_contexts(self) -> Dict[str, ExecutiveContext]:
        """Get all executive contexts."""
        return dict(self._contexts)

    def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        return {
            "running": self._running,
            "executives": {
                exec_id: {
                    "org_id": ctx.org_id,
                    "departments": ctx.departments,
                    "integrations": {
                        "bleval": ctx.bleval_repo is not None,
                        "market": ctx.market_repo is not None,
                        "research": ctx.research_repo is not None,
                        "comms": ctx.comms_repo is not None,
                    },
                    "pipelines": {
                        "research": ctx.research_pipeline is not None,
                        "market": ctx.market_pipeline is not None,
                        "bleval": ctx.bleval_pipeline is not None,
                        "comms": ctx.comms_gateway is not None,
                    },
                }
                for exec_id, ctx in self._contexts.items()
            },
            "pipelines": {
                "research": self._research_pipeline is not None,
                "market": self._market_pipeline is not None,
                "bleval": self._bleval_pipeline is not None,
                "comms": self._comms_gateway is not None,
                "market_intelligence": self._market_intelligence is not None,
            },
        }


# Rebuild ExecutiveContext now that IntegrationLayer is available
# This must be called after all modules are imported to resolve forward references
try:
    from axiom.integrations.layer import IntegrationLayer
    ExecutiveContext.model_rebuild()
except ImportError:
    # IntegrationLayer not yet available, will be rebuilt when imported
    pass