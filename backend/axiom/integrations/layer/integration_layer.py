"""Unified Integration Layer — Main entry point for managed integrations.

This is the primary interface for running integrations with full lifecycle management.
It coordinates the Provider Registry, Integration Lifecycle, and all supporting components.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from axiom.runtime.logging import RuntimeLogger

from .models import (
    IntegrationConfig,
    IntegrationState,
    IntegrationStatus,
    IntegrationResult,
    ConnectionConfig,
    AuthConfig,
    FetchConfig,
    ValidationConfig,
    NormalizationConfig,
    DeduplicationConfig,
    CacheConfig,
    PersistenceConfig,
    MonitoringConfig,
    ConnectionProtocol,
    AuthStrategy,
    ValidationMode,
    DeduplicationStrategy,
    CacheStrategy,
    PersistenceTarget,
)
from .lifecycle import IntegrationLifecycle
from .cache import IntegrationCache
from .monitor import IntegrationMonitor
from .events import IntegrationEventPublisher, IntegrationEventSubscriber


class IntegrationLayer:
    """Unified Integration Layer - governs all external data connections.

    Provides:
    - Configuration management (YAML-based)
    - Lifecycle orchestration per integration
    - Multi-tier caching
    - Comprehensive monitoring
    - Event publishing
    - Scheduled execution
    """

    def __init__(
        self,
        config_dir: Optional[str] = None,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        self.config_dir = Path(config_dir) if config_dir else Path("config/integrations")
        self.logger = logger or RuntimeLogger()

        # Core components
        self._lifecycles: Dict[str, IntegrationLifecycle] = {}
        self._configs: Dict[str, IntegrationConfig] = {}
        self._event_publisher = IntegrationEventPublisher()
        self._event_subscriber = None  # Initialized when event engine available

        # Shared cache and monitor
        self._global_cache = IntegrationCache(CacheConfig())
        self._global_monitor = IntegrationMonitor(MonitoringConfig())

        # State
        self._running = False
        self._scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self, event_engine: Optional[Any] = None) -> None:
        """Initialize the integration layer."""
        # Initialize event publisher
        if event_engine:
            await self._event_publisher.initialize(event_engine)
            # Initialize subscriber
            from .events import IntegrationEventSubscriber
            self._event_subscriber = IntegrationEventSubscriber(event_engine, self.logger)
            await self._event_subscriber.start()

        # Start shared components
        await self._global_cache.start()
        await self._global_monitor.start()

        # Load configurations
        await self._load_configurations()

        self.logger.info("integration_layer", "IntegrationLayer initialized")

    async def shutdown(self) -> None:
        """Shutdown the integration layer."""
        self._running = False

        # Stop scheduled tasks
        for task in self._scheduled_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._scheduled_tasks.clear()

        # Stop lifecycles
        for lifecycle in self._lifecycles.values():
            await lifecycle.stop_scheduled()

        # Stop shared components
        await self._global_cache.stop()
        await self._global_monitor.stop()

        self.logger.info("integration_layer", "IntegrationLayer shutdown complete")

    async def _load_configurations(self) -> None:
        """Load integration configurations from YAML files."""
        if not self.config_dir.exists():
            self.logger.warning("integration_layer", f"Integration config directory not found: {self.config_dir}")
            return

        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file) as f:
                    data = yaml.safe_load(f) or {}

                for integration_data in data.get("integrations", []):
                    config = self._parse_config(integration_data)
                    self._configs[config.integration_id] = config

                    # Create lifecycle
                    lifecycle = IntegrationLifecycle(
                        config=config,
                        logger=self.logger,
                        event_publisher=self._event_publisher,
                    )
                    self._lifecycles[config.integration_id] = lifecycle

            except Exception as e:
                self.logger.error("integration_layer", f"Failed to load integration config from {config_file}: {e}")

        self.logger.info("integration_layer", f"Loaded {len(self._configs)} integration configurations")

    def _parse_config(self, data: Dict[str, Any]) -> IntegrationConfig:
        """Parse integration configuration from dict."""
        # Parse nested configs
        connection = ConnectionConfig(**data.get("connection", {}))
        auth = AuthConfig(**data.get("auth", {}))
        fetch = FetchConfig(**data.get("fetch", {}))
        validation = ValidationConfig(**data.get("validation", {}))
        normalization = NormalizationConfig(**data.get("normalization", {}))
        deduplication = DeduplicationConfig(**data.get("deduplication", {}))
        cache = CacheConfig(**data.get("cache", {}))
        persistence = PersistenceConfig(**data.get("persistence", {}))
        monitoring = MonitoringConfig(**data.get("monitoring", {}))

        return IntegrationConfig(
            integration_id=data["integration_id"],
            name=data["name"],
            description=data.get("description", ""),
            provider_id=data["provider_id"],
            org_id=data["org_id"],
            connection=connection,
            auth=auth,
            fetch=fetch,
            validation=validation,
            normalization=normalization,
            deduplication=deduplication,
            cache=cache,
            persistence=persistence,
            monitoring=monitoring,
            enabled=data.get("enabled", True),
            schedule=data.get("schedule"),
            tags=data.get("tags", []),
        )

    # ── Public API ─────────────────────────────────────────────────────────

    async def execute_integration(
        self,
        integration_id: str,
        correlation_id: Optional[str] = None,
    ) -> IntegrationResult:
        """Execute a single integration cycle."""
        lifecycle = self._lifecycles.get(integration_id)
        if not lifecycle:
            return IntegrationResult(
                integration_id=integration_id,
                success=False,
                state=IntegrationState.ERROR,
                errors=[f"Integration {integration_id} not found"],
                correlation_id=correlation_id or str(uuid.uuid4()),
            )

        if not lifecycle.config.enabled:
            return IntegrationResult(
                integration_id=integration_id,
                success=False,
                state=IntegrationState.DISABLED,
                errors=[f"Integration {integration_id} is disabled"],
                correlation_id=correlation_id or str(uuid.uuid4()),
            )

        return await lifecycle.execute_full_cycle(correlation_id)

    async def execute_integration_by_provider(
        self,
        provider_id: str,
        correlation_id: Optional[str] = None,
    ) -> List[IntegrationResult]:
        """Execute all integrations for a provider."""
        results = []
        for lifecycle in self._lifecycles.values():
            if lifecycle.config.provider_id == provider_id:
                result = await lifecycle.execute_full_cycle(correlation_id)
                results.append(result)
        return results

    async def execute_integration_by_org(
        self,
        org_id: str,
        correlation_id: Optional[str] = None,
    ) -> List[IntegrationResult]:
        """Execute all integrations for an organization."""
        results = []
        for lifecycle in self._lifecycles.values():
            if lifecycle.config.org_id == org_id:
                result = await lifecycle.execute_full_cycle(correlation_id)
                results.append(result)
        return results

    async def execute_all(self, correlation_id: Optional[str] = None) -> List[IntegrationResult]:
        """Execute all enabled integrations."""
        results = []
        for lifecycle in self._lifecycles.values():
            if lifecycle.config.enabled:
                result = await lifecycle.execute_full_cycle(correlation_id)
                results.append(result)
        return results

    def get_integration_status(self, integration_id: str) -> Optional[IntegrationStatus]:
        """Get status of an integration."""
        lifecycle = self._lifecycles.get(integration_id)
        if lifecycle:
            return lifecycle.get_status()
        return None

    def get_all_statuses(self) -> Dict[str, IntegrationStatus]:
        """Get status of all integrations."""
        return {
            integration_id: lifecycle.get_status()
            for integration_id, lifecycle in self._lifecycles.items()
        }

    def get_integration_config(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get configuration of an integration."""
        return self._configs.get(integration_id)

    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all integrations with basic info."""
        return [
            {
                "integration_id": config.integration_id,
                "name": config.name,
                "provider_id": config.provider_id,
                "org_id": config.org_id,
                "enabled": config.enabled,
                "schedule": config.schedule,
                "tags": config.tags,
            }
            for config in self._configs.values()
        ]

    # ── Scheduled Execution ────────────────────────────────────────────────

    async def start_scheduled(self, integration_id: str) -> bool:
        """Start scheduled execution for an integration."""
        lifecycle = self._lifecycles.get(integration_id)
        if not lifecycle or not lifecycle.config.schedule:
            return False

        if integration_id in self._scheduled_tasks:
            return True  # Already running

        task = asyncio.create_task(lifecycle.start_scheduled())
        self._scheduled_tasks[integration_id] = task
        return True

    async def stop_scheduled(self, integration_id: str) -> bool:
        """Stop scheduled execution for an integration."""
        if integration_id in self._scheduled_tasks:
            task = self._scheduled_tasks.pop(integration_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        lifecycle = self._lifecycles.get(integration_id)
        if lifecycle:
            await lifecycle.stop_scheduled()

        return True

    async def start_all_scheduled(self) -> int:
        """Start scheduled execution for all integrations with schedules."""
        count = 0
        for integration_id, lifecycle in self._lifecycles.items():
            if lifecycle.config.schedule and lifecycle.config.enabled:
                if await self.start_scheduled(integration_id):
                    count += 1
        return count

    async def stop_all_scheduled(self) -> int:
        """Stop all scheduled executions."""
        count = 0
        for integration_id in list(self._scheduled_tasks.keys()):
            if await self.stop_scheduled(integration_id):
                count += 1
        return count

    # ── Cache & Monitor Access ────────────────────────────────────────────

    @property
    def cache(self) -> IntegrationCache:
        """Get global cache."""
        return self._global_cache

    @property
    def monitor(self) -> IntegrationMonitor:
        """Get global monitor."""
        return self._global_monitor

    @property
    def event_publisher(self) -> IntegrationEventPublisher:
        """Get event publisher."""
        return self._event_publisher

    # ── Health & Summary ──────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Get integration layer summary."""
        statuses = self.get_all_statuses()

        total = len(statuses)
        enabled = sum(1 for s in statuses.values() if s.state != IntegrationState.DISABLED)
        healthy = sum(1 for s in statuses.values() if s.health_score > 0.8)
        degraded = sum(1 for s in statuses.values() if 0.5 < s.health_score <= 0.8)
        unhealthy = sum(1 for s in statuses.values() if s.health_score <= 0.5)
        error = sum(1 for s in statuses.values() if s.state == IntegrationState.ERROR)

        return {
            "total_integrations": total,
            "enabled": enabled,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "error": error,
            "scheduled_running": len(self._scheduled_tasks),
            "cache_stats": self._global_cache.get_stats(),
            "monitor_summary": self._global_monitor.get_health_summary(),
        }