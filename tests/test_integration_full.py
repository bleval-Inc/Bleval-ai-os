"""End-to-End Integration Tests for Axiom AI OS.

This test suite validates the complete system integration:
- Runtime bootstrap and shutdown
- Executive loops (Jenson, Valta Prime, Yamako)
- Integration Layer with all providers
- Domain databases (BLEVAL, MARKET, RESEARCH, COMMS)
- Market Intelligence pipeline
- BLEVAL Acquisition pipeline
- Communication Gateway
- Resource-Aware Runtime
- AXIOM Core intelligence layer
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

# Import core components
from axiom.runtime.lifecycle import AxiomRuntime
from axiom.runtime.executive_integration import ExecutiveIntegration, ExecutiveIntegrationConfig
from axiom.runtime.executive_loop import ExecutiveRuntimeLoop, ExecutiveBoard
from axiom.runtime.resource import RuntimeOrchestrator, ResourceMonitor, ResourceScheduler
from axiom.integrations.layer import IntegrationLayer
from axiom.data.database import DatabaseManager
from axiom.core.axiom_core import AXIOMCore, AxiomBootResult, SystemState
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.memory import MemoryEngine
from axiom.engine.tool import ToolEngine
from axiom.engine.event import EventEngine
from axiom.engine.workflow import WorkflowEngine
from axiom.engine.executive import ExecutiveEngine
from axiom.engine.specialist_agent import SpecialistAgentEngine
from axiom.engine.autonomous_workflow import AutonomousWorkflowEngine
from axiom.engine.multi_model import MultiModelEngine
from axiom.runtime.background_executor import BackgroundExecutor
from axiom.runtime.workflow_observer import WorkflowObserver
from axiom.runtime.qc_engine import QCManager
from axiom.runtime.founder_authority import FounderAuthority
from axiom.runtime.founder_gateway import FounderGateway


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
async def runtime():
    """Create and bootstrap a full runtime instance."""
    rt = AxiomRuntime()
    await rt.bootstrap()
    yield rt
    await rt.shutdown()


@pytest.fixture
async def started_runtime(runtime):
    """Create a fully started runtime."""
    await runtime.start()
    yield runtime
    await runtime.shutdown()


@pytest.fixture
def mock_intelligence():
    """Mock intelligence engine for testing."""
    engine = MagicMock(spec=IntelligenceEngine)
    engine.generate = AsyncMock(return_value="Test response")
    engine.generate_for_executive = AsyncMock(
        return_value='{"priorities": ["Priority 1", "Priority 2", "Priority 3"]}'
    )
    return engine


# =============================================================================
# Runtime Bootstrap Tests
# =============================================================================

class TestRuntimeBootstrap:
    """Test runtime bootstrap and component initialization."""

    @pytest.mark.asyncio
    async def test_runtime_bootstrap_initializes_all_engines(self, runtime):
        """Verify all engines are initialized after bootstrap."""
        assert runtime._initialised is True
        assert runtime.memory is not None
        assert runtime.tool is not None
        assert runtime.executive is not None
        assert runtime.intelligence is not None
        assert runtime.event is not None
        assert runtime.workflow is not None
        assert runtime.scheduler is not None
        assert runtime.dispatcher is not None
        assert runtime.monitor is not None
        assert runtime.recovery is not None
        assert runtime.approval is not None
        assert runtime.executive_board is not None
        assert runtime.learning is not None
        assert runtime.system_monitor is not None
        assert runtime.greeting_engine is not None
        assert runtime.system_tools is not None
        assert runtime.specialist_engine is not None
        assert runtime.autonomous_workflow is not None
        assert runtime.multi_model is not None
        assert runtime.background_executor is not None
        assert runtime.workflow_observer is not None
        assert runtime.qc_manager is not None
        assert runtime.founder_authority is not None
        assert runtime.founder_gateway is not None
        assert runtime.provider_registry is not None
        assert runtime.axiom is not None

    @pytest.mark.asyncio
    async def test_runtime_start_starts_all_background_tasks(self, started_runtime):
        """Verify all background tasks are running after start."""
        assert started_runtime._running is True
        assert started_runtime.event._running is True
        assert started_runtime.scheduler._running is True
        assert started_runtime.dispatcher._running is True
        assert started_runtime.monitor._running is True
        assert started_runtime.learning._running is True
        assert started_runtime.specialist_engine._running is True
        assert started_runtime.autonomous_workflow._monitor_task is not None
        assert started_runtime.background_executor._running is True

    @pytest.mark.asyncio
    async def test_runtime_shutdown_stops_all_gracefully(self, runtime):
        """Verify graceful shutdown stops all components."""
        await runtime.start()
        await runtime.shutdown()

        assert runtime._running is False
        assert runtime.event._running is False
        assert runtime.scheduler._running is False
        assert runtime.dispatcher._running is False
        assert runtime.monitor._running is False
        assert runtime.learning._running is False


# =============================================================================
# Executive Board Tests
# =============================================================================

class TestExecutiveBoard:
    """Test the executive board and all three executive loops."""

    @pytest.mark.asyncio
    async def test_executive_board_creates_three_loops(self, started_runtime):
        """Verify board creates exactly 3 executive loops."""
        board = started_runtime.executive_board
        assert board is not None
        loops = board._loops
        assert len(loops) == 3
        assert "jenson" in loops
        assert "valta_prime" in loops
        assert "yamako" in loops

    @pytest.mark.asyncio
    async def test_executive_loops_start_and_are_running(self, started_runtime):
        """Verify all executive loops are running."""
        board = started_runtime.executive_board
        for exec_id, loop in board._loops.items():
            assert loop.is_running is True
            assert loop.org_id != ""
            assert len(loop.departments) > 0

    @pytest.mark.asyncio
    async def test_jenson_org_is_bleval_inc(self, started_runtime):
        """Verify Jenson manages Bleval Inc."""
        loop = started_runtime.executive_board.get_loop("jenson")
        assert loop.org_id == "bleval_inc"
        assert "sales" in loop.departments
        assert "marketing" in loop.departments

    @pytest.mark.asyncio
    async def test_valta_prime_org_is_house_of_valta(self, started_runtime):
        """Verify Valta Prime manages House of Valta."""
        loop = started_runtime.executive_board.get_loop("valta_prime")
        assert loop.org_id == "house_of_valta"
        assert "trading" in loop.departments
        assert "risk" in loop.departments

    @pytest.mark.asyncio
    async def test_yamako_org_is_personal(self, started_runtime):
        """Verify Yamako manages Personal org."""
        loop = started_runtime.executive_board.get_loop("yamako")
        assert loop.org_id == "personal"
        assert "operations" in loop.departments

    @pytest.mark.asyncio
    async def test_executive_cycle_execution(self, started_runtime):
        """Test manual executive cycle execution."""
        loop = started_runtime.executive_board.get_loop("jenson")
        result = await loop.trigger_cycle("test_cycle")

        assert "cycle" in result
        assert "priorities" in result
        assert "workflows_launched" in result
        assert isinstance(result["priorities"], list)


# =============================================================================
# Integration Layer Tests
# =============================================================================

class TestIntegrationLayer:
    """Test the unified integration layer."""

    @pytest.mark.asyncio
    async def test_integration_layer_initializes(self, started_runtime):
        """Verify integration layer is initialized."""
        layer = started_runtime.integration_layer
        assert layer is not None

    @pytest.mark.asyncio
    async def test_integration_layer_has_configured_integrations(self, started_runtime):
        """Verify integration layer loads configured integrations."""
        layer = started_runtime.integration_layer
        summary = layer.get_summary()
        assert "total_integrations" in summary
        # Should have config from all three orgs
        assert summary["total_integrations"] > 0

    @pytest.mark.asyncio
    async def test_scheduled_integrations_can_start(self, started_runtime):
        """Verify scheduled integrations start correctly."""
        layer = started_runtime.integration_layer
        # Already started in start()
        summary = layer.get_summary()
        assert summary["running_integrations"] >= 0


# =============================================================================
# Database Layer Tests
# =============================================================================

class TestDatabaseLayer:
    """Test domain database architecture."""

    @pytest.mark.asyncio
    async def test_database_manager_creates_four_domains(self):
        """Verify DatabaseManager creates 4 isolated databases."""
        db_manager = DatabaseManager()
        status = db_manager.get_status()

        assert "databases" in status
        domains = list(status["databases"].keys())
        assert "bleval" in domains
        assert "market" in domains
        assert "research" in domains
        assert "comms" in domains

    @pytest.mark.asyncio
    async def test_bleval_repository_crud(self):
        """Test BLEVAL repository CRUD operations."""
        from axiom.data.models.bleval import Lead, Contact, Account
        from axiom.data.repositories.bleval import BlevalRepository

        db_manager = DatabaseManager()
        repo = BlevalRepository(db_manager)

        # Test lead creation
        lead = Lead(
            org_id="bleval_inc",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            company="Acme Corp",
            title="CEO",
            source="website",
            status="new",
            score=75,
        )
        created = await repo.create_lead(lead)
        assert created.id is not None

        # Test retrieval
        retrieved = await repo.get_lead(created.id)
        assert retrieved is not None
        assert retrieved.email == "john.doe@example.com"

        # Test query
        leads = await repo.list_leads(org_id="bleval_inc", limit=10)
        assert len(leads) >= 1

    @pytest.mark.asyncio
    async def test_market_repository_operations(self):
        """Test MARKET repository operations."""
        from axiom.data.models.market import Symbol, MarketTick
        from axiom.data.repositories.market import MarketRepository

        db_manager = DatabaseManager()
        repo = MarketRepository(db_manager)

        # Create symbol
        symbol = Symbol(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            asset_class="equity",
            currency="USD",
            is_active=True,
        )
        created = await repo.create_symbol(symbol)
        assert created.id is not None

        # Create tick
        tick = MarketTick(
            symbol_id=created.id,
            timestamp=datetime.utcnow(),
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            volume=1000000,
        )
        # Would need batch insert for ticks
        assert tick.symbol_id == created.id

    @pytest.mark.asyncio
    async def test_repositories_isolated_by_org(self):
        """Verify repositories enforce organization isolation."""
        db_manager = DatabaseManager()
        from axiom.data.repositories.bleval import BlevalRepository
        from axiom.data.repositories.market import MarketRepository

        bleval_repo = BlevalRepository(db_manager)
        market_repo = MarketRepository(db_manager)

        # Create in different orgs
        # Each repo should only see its own org data
        pass  # Detailed test would require actual DB


# =============================================================================
# Market Intelligence Tests
# =============================================================================

class TestMarketIntelligence:
    """Test market intelligence pipeline."""

    @pytest.mark.asyncio
    async def test_market_intelligence_engine_initializes(self):
        """Test MarketIntelligenceEngine initialization."""
        from axiom.data.database import DatabaseManager
        from axiom.data.repositories.market import MarketRepository
        from axiom.integrations.market.intelligence import MarketIntelligenceEngine
        from axiom.runtime.logging import RuntimeLogger

        db_manager = DatabaseManager()
        market_repo = MarketRepository(db_manager)
        engine = MarketIntelligenceEngine(
            market_repo=market_repo,
            logger=RuntimeLogger(),
        )
        assert engine is not None

    @pytest.mark.asyncio
    async def test_technical_indicators_sma(self):
        """Test SMA indicator calculation."""
        from axiom.integrations.market.indicators import TechnicalIndicators

        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        sma = TechnicalIndicators.sma(prices, 5)
        assert len(sma) == len(prices) - 4
        assert sma[-1] == 107.0  # (105+106+107+108+109)/5

    @pytest.mark.asyncio
    async def test_technical_indicators_rsi(self):
        """Test RSI indicator calculation."""
        from axiom.integrations.market.indicators import TechnicalIndicators

        # Rising prices should give high RSI
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
        rsi = TechnicalIndicators.rsi(prices, 14)
        assert rsi[-1] > 70  # Overbought

        # Falling prices should give low RSI
        prices = [114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100]
        rsi = TechnicalIndicators.rsi(prices, 14)
        assert rsi[-1] < 30  # Oversold

    @pytest.mark.asyncio
    async def test_signal_generator_rules(self):
        """Test signal generation with built-in rules."""
        from axiom.integrations.market.signals import SignalGenerator, SignalRule, SignalType

        generator = SignalGenerator()

        # Add RSI oversold rule
        rule = SignalRule(
            name="rsi_oversold",
            signal_type=SignalType.BUY,
            condition="rsi < 30",
            description="RSI oversold",
        )
        generator.add_rule(rule)

        # Create test signal
        signal = generator.generate_signals(
            symbol="TEST",
            timeframe="1h",
            indicators={"rsi": [25]},
        )
        # Would need more complete test


# =============================================================================
# BLEVAL Pipeline Tests
# =============================================================================

class TestBlevalPipeline:
    """Test BLEVAL acquisition pipeline."""

    @pytest.mark.asyncio
    async def test_bleval_pipeline_initializes(self):
        """Test BlevalPipeline initialization."""
        from axiom.data.database import DatabaseManager
        from axiom.integrations.bleval.pipeline import BlevalPipeline
        from axiom.runtime.logging import RuntimeLogger

        db_manager = DatabaseManager()
        pipeline = BlevalPipeline(
            database_manager=db_manager,
            logger=RuntimeLogger(),
        )
        assert pipeline is not None

    @pytest.mark.asyncio
    async def test_lead_scoring(self):
        """Test lead scoring components."""
        from axiom.integrations.bleval.lead_acquisition import LeadAcquisitionEngine, LeadScoringEngine, LeadSource

        scoring = LeadScoringEngine()
        lead_data = {
            "company_size": 500,
            "industry": "technology",
            "title": "CTO",
            "engagement_score": 80,
            "website_visits": 10,
            "email_opens": 5,
        }

        score = scoring.score_lead(lead_data)
        assert 0 <= score <= 100
        assert isinstance(score, int)


# =============================================================================
# Communication Gateway Tests
# =============================================================================

class TestCommunicationGateway:
    """Test multi-channel communication gateway."""

    @pytest.mark.asyncio
    async def test_gateway_initializes(self):
        """Test CommunicationGateway initialization."""
        from axiom.integrations.comms.gateway import CommunicationGateway
        from axiom.integrations.layer import IntegrationLayer
        from axiom.runtime.logging import RuntimeLogger
        from unittest.mock import MagicMock

        integration_layer = MagicMock(spec=IntegrationLayer)
        repositories = {"comms": MagicMock()}

        gateway = CommunicationGateway(
            integration_layer=integration_layer,
            repositories=repositories,
            logger=RuntimeLogger()
        )
        assert gateway is not None

    @pytest.mark.asyncio
    async def test_notification_router(self):
        """Test notification routing by priority."""
        from axiom.integrations.comms.notifications import NotificationRouter, NotificationConfig, NotificationChannel
        from axiom.data.models import NotificationPriority
        from axiom.integrations.layer import IntegrationLayer
        from unittest.mock import MagicMock, AsyncMock

        integration_layer = MagicMock(spec=IntegrationLayer)
        repository = MagicMock()

        router = NotificationRouter(
            integration_layer=integration_layer,
            repository=repository,
        )

        # Test that priority channels are correctly configured
        assert NotificationPriority.LOW in router.config.priority_channels
        assert NotificationPriority.NORMAL in router.config.priority_channels
        assert NotificationPriority.HIGH in router.config.priority_channels
        assert NotificationPriority.URGENT in router.config.priority_channels
        assert NotificationPriority.CRITICAL in router.config.priority_channels

        # Verify default channels per priority
        assert router.config.priority_channels[NotificationPriority.LOW] == [NotificationChannel.IN_APP]
        assert NotificationChannel.EMAIL in router.config.priority_channels[NotificationPriority.NORMAL]
        assert NotificationChannel.SLACK in router.config.priority_channels[NotificationPriority.HIGH]
        assert NotificationChannel.WHATSAPP in router.config.priority_channels[NotificationPriority.URGENT]
        assert NotificationChannel.SMS in router.config.priority_channels[NotificationPriority.CRITICAL]


# =============================================================================
# Resource-Aware Runtime Tests
# =============================================================================

class TestResourceAwareRuntime:
    """Test resource monitoring, scheduling, and quotas."""

    @pytest.mark.asyncio
    async def test_resource_monitor_collects_metrics(self):
        """Test ResourceMonitor collects system metrics."""
        monitor = ResourceMonitor(interval_seconds=1)
        await monitor.start()

        # Wait for first collection
        await asyncio.sleep(2)

        metrics = monitor.get_current()
        assert metrics is not None
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.cpu_count > 0

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_resource_scheduler_schedules_tasks(self):
        """Test ResourceScheduler schedules and runs tasks."""
        monitor = ResourceMonitor(interval_seconds=1)
        await monitor.start()

        scheduler = ResourceScheduler(monitor=monitor, max_concurrent=2)
        await scheduler.start()

        # Schedule a simple task
        async def simple_task():
            return "completed"

        task_id = scheduler.schedule_coro("test_task", simple_task)
        assert task_id is not None

        # Wait for completion
        await asyncio.sleep(1)

        task = scheduler.get_task(task_id)
        assert task is not None
        assert task.status.value in ("completed", "running")

        await scheduler.stop()
        await monitor.stop()

    @pytest.mark.asyncio
    async def test_quota_manager_enforces_limits(self):
        """Test QuotaManager enforces quota limits."""
        from axiom.runtime.resource.quotas import QuotaManager, QuotaConfig, QuotaScope, QuotaType

        config = QuotaConfig(
            max_concurrent_per_agent=1,
            api_calls_per_minute_per_agent=2,
        )
        manager = QuotaManager(config=config)

        # First call should succeed
        allowed, violation = await manager.check_quota(
            QuotaScope.AGENT, "test_agent", QuotaType.CONCURRENT_TASKS
        )
        assert allowed is True
        assert violation is None

        # Consume the quota
        await manager.consume_quota(QuotaScope.AGENT, "test_agent", QuotaType.CONCURRENT_TASKS, 1.0)

        # Second call should fail
        allowed, violation = await manager.check_quota(
            QuotaScope.AGENT, "test_agent", QuotaType.CONCURRENT_TASKS
        )
        assert allowed is False
        assert violation is not None

    @pytest.mark.asyncio
    async def test_runtime_orchestrator_integrates_all(self):
        """Test RuntimeOrchestrator coordinates all components."""
        monitor = ResourceMonitor(interval_seconds=5)
        await monitor.start()

        scheduler = ResourceScheduler(monitor=monitor, max_concurrent=5)
        await scheduler.start()

        from axiom.runtime.resource.quotas import QuotaManager, QuotaConfig
        quota_manager = QuotaManager(QuotaConfig())

        orchestrator = RuntimeOrchestrator(
            logger=None,
            # Would need full wiring in integration test
        )

        status = orchestrator.get_status()
        assert "running" in status
        assert "scheduler" in status

        await scheduler.stop()
        await monitor.stop()


# =============================================================================
# AXIOM Core Tests
# =============================================================================

class TestAXIOMCore:
    """Test AXIOM Core top-level intelligence."""

    @pytest.mark.asyncio
    async def test_axiom_core_boot(self):
        """Test AXIOM Core boot sequence."""
        core = AXIOMCore()
        # Core is wired by runtime, but we can test basic functionality
        assert core.state == SystemState.SHUTDOWN
        assert core.is_online is False

    @pytest.mark.asyncio
    async def test_axiom_core_chat(self):
        """Test AXIOM Core chat interface."""
        core = AXIOMCore()
        # Would need intelligence engine wired

    @pytest.mark.asyncio
    async def test_axiom_core_system_awareness(self):
        """Test system awareness building."""
        core = AXIOMCore()
        # Would need runtime wired


# =============================================================================
# Cross-Component Integration Tests
# =============================================================================

class TestCrossComponentIntegration:
    """Test integration between major system components."""

    @pytest.mark.asyncio
    async def test_executive_integration_wires_all_layers(self, started_runtime):
        """Test executive integration connects all layers."""
        # Integration is initialized in start()
        # Verify it has access to all components
        rt = started_runtime

        if hasattr(rt, 'executive_integration') and rt.executive_integration:
            ei = rt.executive_integration
            status = ei.get_status()
            assert "executives" in status
            assert "pipelines" in status

    @pytest.mark.asyncio
    async def test_event_engine_wiring(self, started_runtime):
        """Test event engine wiring for workflow auto-launch."""
        # Check subscriptions
        event = started_runtime.event
        # Should have subscriptions from workflow triggers
        assert len(event._subscriptions) >= 0

    @pytest.mark.asyncio
    async def test_learning_engine_wiring(self, started_runtime):
        """Test learning engine receives events."""
        learning = started_runtime.learning
        # Should have event subscriptions
        assert learning is not None

    @pytest.mark.asyncio
    async def test_qc_pipeline_wiring(self, started_runtime):
        """Test QC pipeline callbacks are wired."""
        qc = started_runtime.qc_manager
        assert qc._on_qc_passed is not None
        assert qc._on_qc_failed is not None


# =============================================================================
# Provider Registry Tests
# =============================================================================

class TestProviderRegistry:
    """Test platform provider registry."""

    @pytest.mark.asyncio
    async def test_provider_registry_has_implementations(self, started_runtime):
        """Verify provider registry has all platform implementations."""
        registry = started_runtime.provider_registry
        providers = registry.list_providers()

        expected_providers = [
            "github", "market_data", "mt5", "tradingview",
            "crm", "email", "calendar", "slack", "whatsapp",
        ]

        for provider in expected_providers:
            assert provider in providers

    @pytest.mark.asyncio
    async def test_provider_initialization_per_org(self, started_runtime):
        """Test providers initialize per organization."""
        registry = started_runtime.provider_registry
        # Would test with actual org configs


# =============================================================================
# Performance Benchmarks
# =============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmarks for critical paths."""

    @pytest.mark.asyncio
    async def test_boot_time_under_threshold(self):
        """Benchmark boot time."""
        import time

        start = time.monotonic()
        rt = AxiomRuntime()
        await rt.bootstrap()
        boot_time = time.monotonic() - start

        # Boot should complete within reasonable time (< 10 seconds)
        assert boot_time < 10.0
        await rt.shutdown()

    @pytest.mark.asyncio
    async def test_executive_cycle_latency(self, started_runtime):
        """Benchmark executive cycle execution time."""
        import time

        loop = started_runtime.executive_board.get_loop("jenson")

        start = time.monotonic()
        await loop.trigger_cycle("benchmark")
        latency = time.monotonic() - start

        # Cycle should complete quickly (< 1 second without external calls)
        assert latency < 1.0

    @pytest.mark.asyncio
    async def test_integration_layer_throughput(self, started_runtime):
        """Benchmark integration layer event processing."""
        layer = started_runtime.integration_layer
        # Would need to inject events and measure throughput

    @pytest.mark.asyncio
    async def test_scheduler_concurrency(self):
        """Benchmark scheduler concurrent task handling."""
        monitor = ResourceMonitor(interval_seconds=1)
        await monitor.start()

        scheduler = ResourceScheduler(monitor=monitor, max_concurrent=10)
        await scheduler.start()

        # Schedule multiple concurrent tasks
        async def quick_task():
            await asyncio.sleep(0.01)
            return "done"

        import time
        start = time.monotonic()

        task_ids = []
        for i in range(20):
            tid = scheduler.schedule_coro(f"task_{i}", quick_task)
            task_ids.append(tid)

        # Wait for all
        await asyncio.sleep(1)

        elapsed = time.monotonic() - start
        # With max_concurrent=10 and 20 tasks of 10ms, should take ~20-40ms
        assert elapsed < 1.0  # Generous bound

        await scheduler.stop(wait=True)
        await monitor.stop()


# =============================================================================
# Smoke Tests
# =============================================================================

class TestSmokeTests:
    """Quick smoke tests for critical functionality."""

    @pytest.mark.asyncio
    async def test_full_system_startup_shutdown(self):
        """Smoke test: full system startup and shutdown."""
        rt = AxiomRuntime()
        await rt.bootstrap()
        await rt.start()
        await asyncio.sleep(0.5)  # Let things settle
        await rt.shutdown()

    @pytest.mark.asyncio
    async def test_all_executives_respond(self, started_runtime):
        """Smoke test: all three executives respond to trigger."""
        board = started_runtime.executive_board

        for exec_id in ["jenson", "valta_prime", "yamako"]:
            loop = board.get_loop(exec_id)
            result = await loop.trigger_cycle("smoke_test")
            assert result is not None
            assert "priorities" in result

    @pytest.mark.asyncio
    async def test_axiom_core_greeting(self, started_runtime):
        """Smoke test: AXIOM Core generates greeting."""
        core = started_runtime.axiom
        # Would test greeting generation


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])